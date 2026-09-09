"""Payment generator with restart checkpoint support for Project 01."""

# TODO: add the validated local implementation.
import sys
import os
import uuid
import random
import time
from decimal import Decimal

# Allow execution directly from simulator folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

GENERATOR_NAME = "payment_generator"

# Number of orders fetched/processed in one logical transaction
ORDER_BATCH_SIZE = 1_000

# Number of payment rows sent to SQL Server per executemany call
INSERT_BATCH_SIZE = 1_000

# Fixed random seed for reproducible distribution
SEED = 500

# ------------------------------------------------------------
# TEST CONTROL
# ------------------------------------------------------------
# 10      -> process only 10 orders in this execution
# 50_000  -> process 50K orders in this execution
# None    -> continue until all generated orders are processed
#
# IMPORTANT:
# This does NOT mean batch size.
# ORDER_BATCH_SIZE remains 5,000.
# MAX_ORDERS controls how many orders this RUN processes.
# ------------------------------------------------------------

MAX_ORDERS = None

# Set True only when deliberately testing checkpoint failure.
#
# Behavior:
#   1. Payment batch is committed.
#   2. Checkpoint is NOT updated.
#   3. Generator raises an error.
#
# On the next run, the same batch will be detected as REPLAY.
SIMULATE_CHECKPOINT_FAILURE = False


# ============================================================
# DISTRIBUTIONS
# ============================================================

PAYMENT_STATUS = [
    "SUCCESS",
    "PENDING",
    "FAILED",
    "REFUNDED",
]

PAYMENT_STATUS_WEIGHTS = [
    0.85,
    0.05,
    0.07,
    0.03,
]


PAYMENT_METHOD = [
    "CARD",
    "UPI",
    "NET_BANKING",
    "WALLET",
    "CASH",
]

PAYMENT_METHOD_WEIGHTS = [
    0.40,
    0.30,
    0.15,
    0.10,
    0.05,
]


# ============================================================
# CHECKPOINT FUNCTIONS
# ============================================================

def get_checkpoint(cursor):
    """
    Read the last successfully checkpointed order_id.
    """

    cursor.execute(
        """
        SELECT last_order_id
        FROM dbo.payment_generation_checkpoint
        WHERE generator_name = ?
        """,
        GENERATOR_NAME,
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            f"No checkpoint found for generator: {GENERATOR_NAME}"
        )

    return int(row[0])


def update_checkpoint(cursor, last_order_id):
    """
    Update checkpoint.

    This function does NOT commit.
    The caller controls the transaction boundary.
    """

    cursor.execute(
        """
        UPDATE dbo.payment_generation_checkpoint
        SET
            last_order_id = ?,
            updated_at = SYSDATETIME()
        WHERE generator_name = ?
        """,
        last_order_id,
        GENERATOR_NAME,
    )

    if cursor.rowcount != 1:
        raise RuntimeError(
            f"Checkpoint update failed for {GENERATOR_NAME}"
        )


# ============================================================
# ORDER EXTRACTION
# ============================================================

def fetch_order_batch(cursor, last_order_id, batch_size):
    """
    Fetch generated orders after the checkpoint.

    Seed orders are excluded using the generated customer email
    pattern.
    """

    cursor.execute(
        """
        SELECT TOP (?)
            o.order_id,
            o.total_amount,
            o.order_date,
            o.created_at
        FROM dbo.orders o
        INNER JOIN dbo.customers c
            ON o.customer_id = c.customer_id
        WHERE o.order_id > ?
          AND c.email LIKE 'customer%@contosoretail.example'
        ORDER BY o.order_id
        """,
        batch_size,
        last_order_id,
    )

    return cursor.fetchall()


# ============================================================
# BATCH STATE
# ============================================================

def check_batch_state(
    cursor,
    first_order_id,
    last_order_id,
    expected_orders,
):
    """
    Determine whether the payment batch is:

        NEW
        REPLAY
        PARTIAL

    NEW:
        No payments exist for these orders.

    REPLAY:
        Every order already has a payment.

    PARTIAL:
        Some orders have payments and some do not.

    PARTIAL is treated as an unsafe state and the generator
    stops rather than creating inconsistent data.
    """

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM dbo.payments p
        INNER JOIN dbo.orders o
            ON p.order_id = o.order_id
        INNER JOIN dbo.customers c
            ON o.customer_id = c.customer_id
        WHERE p.order_id BETWEEN ? AND ?
          AND c.email LIKE 'customer%@contosoretail.example'
        """,
        first_order_id,
        last_order_id,
    )

    payment_count = int(cursor.fetchone()[0])

    if payment_count == 0:
        return "NEW"

    if payment_count == expected_orders:
        return "REPLAY"

    return "PARTIAL"


# ============================================================
# PAYMENT GENERATION
# ============================================================

def generate_payment(order_id, total_amount, order_date, created_at, rng):
    """
    Generate exactly one payment for one generated order.
    """

    payment_status = rng.choices(
        PAYMENT_STATUS,
        weights=PAYMENT_STATUS_WEIGHTS,
        k=1,
    )[0]

    payment_method = rng.choices(
        PAYMENT_METHOD,
        weights=PAYMENT_METHOD_WEIGHTS,
        k=1,
    )[0]

    transaction_reference = (
        f"PAY-{order_id}-{SEED}-{uuid.uuid4().hex[:12].upper()}"
    )

    return (
        order_id,
        payment_method,
        payment_status,
        Decimal(str(total_amount)),
        transaction_reference,
        created_at,
        created_at,
    )


# ============================================================
# PAYMENT INSERT
# ============================================================

def insert_payments(cursor, payment_rows):
    """
    Insert payments using executemany.

    No commit happens here.
    """

    cursor.fast_executemany = True

    cursor.executemany(
        """
        INSERT INTO dbo.payments
        (
            order_id,
            payment_method,
            payment_status,
            amount,
            transaction_reference,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        payment_rows,
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_payments():
    rng = random.Random(SEED)

    conn = get_connection()
    cursor = conn.cursor()

    total_orders_processed = 0
    total_rows_generated = 0
    total_rows_inserted = 0
    total_rows_replayed = 0

    execution_start = time.time()

    try:

        # ----------------------------------------------------
        # READ CHECKPOINT
        # ----------------------------------------------------

        checkpoint = get_checkpoint(cursor)

        print("=" * 70)
        print("PAYMENT GENERATOR")
        print("=" * 70)

        print(f"Generator              : {GENERATOR_NAME}")
        print(f"Current checkpoint     : {checkpoint:,}")
        print(f"Order batch size       : {ORDER_BATCH_SIZE:,}")
        print(f"Insert batch size      : {INSERT_BATCH_SIZE:,}")
        print(f"Maximum orders / run  : {MAX_ORDERS}")
        print(f"Seed                   : {SEED}")
        print(
            f"Checkpoint failure    : "
            f"{SIMULATE_CHECKPOINT_FAILURE}"
        )

        print("=" * 70)

        # ----------------------------------------------------
        # EXECUTION LIMIT
        # ----------------------------------------------------

        remaining_for_execution = MAX_ORDERS

        while True:

            # Stop when MAX_ORDERS has been reached
            if (
                remaining_for_execution is not None
                and remaining_for_execution <= 0
            ):
                print()
                print(
                    f"MAX_ORDERS reached: "
                    f"{MAX_ORDERS:,}"
                )
                break

            # ------------------------------------------------
            # DETERMINE FETCH SIZE
            # ------------------------------------------------

            fetch_size = ORDER_BATCH_SIZE

            if remaining_for_execution is not None:
                fetch_size = min(
                    ORDER_BATCH_SIZE,
                    remaining_for_execution,
                )

            # ------------------------------------------------
            # FETCH ORDERS
            # ------------------------------------------------

            orders = fetch_order_batch(
                cursor,
                checkpoint,
                fetch_size,
            )

            if not orders:
                print()
                print("No more generated orders found.")
                break

            first_order_id = int(orders[0][0])
            last_order_id = int(orders[-1][0])

            expected_orders = len(orders)

            print()
            print(
                f"Processing orders "
                f"{first_order_id:,} → {last_order_id:,} "
                f"({expected_orders:,} orders)"
            )

            # ------------------------------------------------
            # CHECK EXISTING TARGET STATE
            # ------------------------------------------------

            batch_state = check_batch_state(
                cursor,
                first_order_id,
                last_order_id,
                expected_orders,
            )

            print(f"Batch state: {batch_state}")

            # =================================================
            # REPLAY
            # =================================================

            if batch_state == "REPLAY":

                print(
                    "REPLAY DETECTED: "
                    "payments already committed."
                )

                print(
                    "Skipping payment insertion."
                )

                # ------------------------------------------------
                # Checkpoint transaction
                # ------------------------------------------------

                update_checkpoint(
                    cursor,
                    last_order_id,
                )

                conn.commit()

                print(
                    f"Checkpoint updated to: "
                    f"{last_order_id:,}"
                )

                total_orders_processed += expected_orders
                total_rows_replayed += expected_orders

                if remaining_for_execution is not None:
                    remaining_for_execution -= expected_orders

                checkpoint = last_order_id

                print(
                    f"Replay rows: "
                    f"{expected_orders:,}"
                )

                continue

            # =================================================
            # PARTIAL
            # =================================================

            if batch_state == "PARTIAL":

                raise RuntimeError(
                    "\n"
                    "PARTIAL BATCH DETECTED.\n"
                    f"Order range: "
                    f"{first_order_id:,} → "
                    f"{last_order_id:,}\n"
                    "Some payments exist but others do not.\n"
                    "Generator stopped to prevent inconsistent "
                    "payment generation."
                )

            # =================================================
            # NEW BATCH
            # =================================================

            payment_buffer = []

            for order in orders:

                order_id = int(order[0])
                total_amount = order[1]
                order_date = order[2]
                created_at = order[3]

                payment = generate_payment(
                    order_id,
                    total_amount,
                    order_date,
                    created_at,
                    rng,
                )

                payment_buffer.append(payment)

            total_rows_generated += len(payment_buffer)

            # ------------------------------------------------
            # INSERT IN SMALL DATABASE BATCHES
            # ------------------------------------------------

            rows_inserted_this_batch = 0

            for i in range(
                0,
                len(payment_buffer),
                INSERT_BATCH_SIZE,
            ):

                insert_batch = payment_buffer[
                    i:i + INSERT_BATCH_SIZE
                ]

                insert_payments(
                    cursor,
                    insert_batch,
                )

                rows_inserted_this_batch += len(
                    insert_batch
                )

                print(
                    f"Inserted payment batch: "
                    f"{len(insert_batch):,}"
                )

            # ------------------------------------------------
            # TARGET COMMIT
            # ------------------------------------------------

            conn.commit()

            total_rows_inserted += (
                rows_inserted_this_batch
            )

            total_orders_processed += expected_orders

            print(
                f"Payment rows committed: "
                f"{rows_inserted_this_batch:,}"
            )

            # =================================================
            # DELIBERATE CHECKPOINT FAILURE TEST
            # =================================================

            if SIMULATE_CHECKPOINT_FAILURE:

                print()
                print(
                    "SIMULATED FAILURE:"
                )

                print(
                    "Payments have been committed, "
                    "but checkpoint will NOT be updated."
                )

                raise RuntimeError(
                    "SIMULATED FAILURE: "
                    "payment batch committed but "
                    "checkpoint not updated."
                )

            # =================================================
            # CHECKPOINT COMMIT
            # =================================================

            update_checkpoint(
                cursor,
                last_order_id,
            )

            conn.commit()

            checkpoint = last_order_id

            print(
                f"Checkpoint updated to: "
                f"{checkpoint:,}"
            )

            # ------------------------------------------------
            # UPDATE EXECUTION LIMIT
            # ------------------------------------------------

            if remaining_for_execution is not None:
                remaining_for_execution -= expected_orders

                print(
                    f"Execution progress: "
                    f"{total_orders_processed:,}"
                    f"/{MAX_ORDERS:,} orders"
                )

            # ------------------------------------------------
            # PERFORMANCE
            # ------------------------------------------------

            elapsed = time.time() - execution_start

            if elapsed > 0:

                orders_per_sec = (
                    total_orders_processed / elapsed
                )

                rows_per_sec = (
                    total_rows_inserted / elapsed
                )

                print(
                    f"Execution rate: "
                    f"{orders_per_sec:,.0f} orders/sec | "
                    f"{rows_per_sec:,.0f} payments/sec"
                )

        # =====================================================
        # FINAL SUMMARY
        # =====================================================

        elapsed = time.time() - execution_start

        print()
        print("=" * 70)
        print("PAYMENT GENERATOR SUMMARY")
        print("=" * 70)

        print(
            f"Orders processed this run : "
            f"{total_orders_processed:,}"
        )

        print(
            f"Rows generated this run   : "
            f"{total_rows_generated:,}"
        )

        print(
            f"Rows inserted this run    : "
            f"{total_rows_inserted:,}"
        )

        print(
            f"Rows replayed this run    : "
            f"{total_rows_replayed:,}"
        )

        print(
            f"Final checkpoint          : "
            f"{checkpoint:,}"
        )

        print(
            f"Elapsed                   : "
            f"{elapsed:,.2f} sec"
        )

        if elapsed > 0:

            print(
                f"Orders/sec                : "
                f"{total_orders_processed / elapsed:,.0f}"
            )

            print(
                f"Payments/sec              : "
                f"{total_rows_inserted / elapsed:,.0f}"
            )

        print("=" * 70)

    except Exception as exc:

        # ----------------------------------------------------
        # Roll back any uncommitted work
        # ----------------------------------------------------

        conn.rollback()

        print()
        print("=" * 70)
        print("PAYMENT GENERATOR FAILED")
        print("=" * 70)

        print(f"Error: {exc}")

        print(
            "Any uncommitted transaction has been rolled back."
        )

        print(
            f"Checkpoint remains at: {get_checkpoint(cursor):,}"
        )

        print("=" * 70)

        raise

    finally:

        cursor.close()
        conn.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    generate_payments()
