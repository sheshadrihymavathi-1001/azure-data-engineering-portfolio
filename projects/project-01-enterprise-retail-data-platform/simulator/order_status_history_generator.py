"""Order-status lifecycle generator for Project 01."""

# TODO: add the validated local implementation.
import sys
import os
import random
import time
from datetime import datetime, timedelta

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

GENERATOR_NAME = "order_status_history_generator"

# Number of orders processed per logical transaction
ORDER_BATCH_SIZE = 1_000

# Number of history rows sent to SQL Server per executemany
INSERT_BATCH_SIZE = 1_000

# ------------------------------------------------------------
# TEST CONTROL
# ------------------------------------------------------------
# 10_000 -> controlled test
# 100_000 -> medium test
# None -> all remaining generated orders
# ------------------------------------------------------------

MAX_ORDERS = None

SEED = 900


# ============================================================
# VALID STATUS TRANSITIONS
# ============================================================

# The lifecycle is constructed from the final status.
#
# Every generated order starts at PLACED.
#
# Possible paths:
#
# PLACED
#
# PLACED -> CONFIRMED
#
# PLACED -> CONFIRMED -> SHIPPED
#
# PLACED -> CONFIRMED -> SHIPPED -> DELIVERED
#
# Cancellation:
#
# PLACED -> CANCELLED
#
# PLACED -> CONFIRMED -> CANCELLED
#
# PLACED -> CONFIRMED -> SHIPPED -> CANCELLED
#
# ============================================================


def build_lifecycle(final_status, rng):
    """
    Build a valid status lifecycle ending in final_status.
    """

    if final_status == "PLACED":

        return [
            "PLACED"
        ]

    if final_status == "CONFIRMED":

        return [
            "PLACED",
            "CONFIRMED"
        ]

    if final_status == "SHIPPED":

        return [
            "PLACED",
            "CONFIRMED",
            "SHIPPED"
        ]

    if final_status == "DELIVERED":

        return [
            "PLACED",
            "CONFIRMED",
            "SHIPPED",
            "DELIVERED"
        ]

    if final_status == "CANCELLED":

        cancellation_point = rng.choice(
            [
                "PLACED",
                "CONFIRMED",
                "SHIPPED",
            ]
        )

        if cancellation_point == "PLACED":

            return [
                "PLACED",
                "CANCELLED"
            ]

        if cancellation_point == "CONFIRMED":

            return [
                "PLACED",
                "CONFIRMED",
                "CANCELLED"
            ]

        return [
            "PLACED",
            "CONFIRMED",
            "SHIPPED",
            "CANCELLED"
        ]

    raise ValueError(
        f"Unsupported order status: {final_status}"
    )


# ============================================================
# FETCH ORDERS
# ============================================================

def fetch_order_batch(
    cursor,
    last_order_id,
    batch_size,
):
    """
    Fetch generated orders after checkpoint.

    Seed orders are excluded through the generated customer
    email pattern.
    """

    cursor.execute(
        """
        SELECT TOP (?)
            o.order_id,
            o.order_status,
            o.order_date,
            o.created_at,
            o.updated_at
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
# CHECKPOINT
# ============================================================

def get_checkpoint(cursor):

    cursor.execute(
        """
        SELECT last_order_id
        FROM dbo.order_status_history_generation_checkpoint
        WHERE generator_name = ?
        """,
        GENERATOR_NAME,
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            f"No checkpoint found for {GENERATOR_NAME}"
        )

    return int(row[0])


def update_checkpoint(
    cursor,
    last_order_id,
):

    cursor.execute(
        """
        UPDATE dbo.order_status_history_generation_checkpoint
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
            "Checkpoint update failed."
        )


# ============================================================
# EXISTING HISTORY CHECK
# ============================================================

def check_batch_state(
    cursor,
    first_order_id,
    last_order_id,
    expected_orders,
):
    """
    Detect:

    NEW
    REPLAY
    PARTIAL

    We check distinct orders with history.

    NEW:
        zero orders have history.

    REPLAY:
        every order has history.

    PARTIAL:
        some orders have history and others don't.
    """

    cursor.execute(
        """
        SELECT COUNT(DISTINCT h.order_id)
        FROM dbo.order_status_history h
        INNER JOIN dbo.orders o
            ON h.order_id = o.order_id
        INNER JOIN dbo.customers c
            ON o.customer_id = c.customer_id
        WHERE h.order_id BETWEEN ? AND ?
          AND c.email LIKE 'customer%@contosoretail.example'
        """,
        first_order_id,
        last_order_id,
    )

    orders_with_history = int(
        cursor.fetchone()[0]
    )

    if orders_with_history == 0:

        return "NEW"

    if orders_with_history == expected_orders:

        return "REPLAY"

    return "PARTIAL"


# ============================================================
# HISTORY GENERATION
# ============================================================

def generate_history_for_order(
    order_id,
    final_status,
    order_date,
    created_at,
    updated_at,
    rng,
):
    """
    Generate valid history rows for one order.

    The final row's new_status MUST equal orders.order_status.
    """

    lifecycle = build_lifecycle(
        final_status,
        rng,
    )

    rows = []

    # --------------------------------------------------------
    # Start timestamp
    # --------------------------------------------------------

    base_time = created_at

    # Ensure history does not occur before order creation.
    if base_time is None:

        base_time = order_date

    current_time = base_time

    # --------------------------------------------------------
    # Generate transitions
    # --------------------------------------------------------

    previous_status = None

    for index, new_status in enumerate(lifecycle):

        if index == 0:

            old_status = None

            # Initial PLACED event.
            #
            # Keep it at or after order creation.
            changed_at = current_time

        else:

            old_status = previous_status

            # Add a realistic time gap between transitions.
            #
            # 5 minutes → 48 hours.
            gap_minutes = rng.randint(
                5,
                48 * 60,
            )

            current_time = (
                current_time
                + timedelta(minutes=gap_minutes)
            )

            changed_at = current_time

        rows.append(
            (
                order_id,
                old_status,
                new_status,
                changed_at,
            )
        )

        previous_status = new_status

    # --------------------------------------------------------
    # Safety assertion
    # --------------------------------------------------------

    if rows[-1][2] != final_status:

        raise RuntimeError(
            f"Lifecycle error for order {order_id}: "
            f"final history status does not match "
            f"orders.order_status."
        )

    return rows


# ============================================================
# INSERT HISTORY
# ============================================================

def insert_history(
    cursor,
    history_rows,
):
    """
    Insert history rows.

    status_history_id is identity-generated by SQL Server.
    """

    cursor.fast_executemany = True

    cursor.executemany(
        """
        INSERT INTO dbo.order_status_history
        (
            order_id,
            old_status,
            new_status,
            changed_at
        )
        VALUES (?, ?, ?, ?)
        """,
        history_rows,
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_status_history():

    rng = random.Random(SEED)

    conn = get_connection()
    cursor = conn.cursor()

    execution_start = time.time()

    total_orders_processed = 0
    total_history_rows_generated = 0
    total_history_rows_inserted = 0
    total_orders_replayed = 0

    try:

        # ----------------------------------------------------
        # CHECKPOINT
        # ----------------------------------------------------

        checkpoint = get_checkpoint(cursor)

        print("=" * 70)
        print("ORDER STATUS HISTORY GENERATOR")
        print("=" * 70)

        print(
            f"Generator              : "
            f"{GENERATOR_NAME}"
        )

        print(
            f"Current checkpoint     : "
            f"{checkpoint:,}"
        )

        print(
            f"Order batch size       : "
            f"{ORDER_BATCH_SIZE:,}"
        )

        print(
            f"Insert batch size      : "
            f"{INSERT_BATCH_SIZE:,}"
        )

        print(
            f"Maximum orders / run  : "
            f"{MAX_ORDERS}"
        )

        print(
            f"Seed                   : "
            f"{SEED}"
        )

        print("=" * 70)

        remaining_for_execution = MAX_ORDERS

        # ====================================================
        # MAIN LOOP
        # ====================================================

        while True:

            # ------------------------------------------------
            # MAX_ORDERS LIMIT
            # ------------------------------------------------

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
            # FETCH SIZE
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
                print(
                    "No more generated orders found."
                )

                break

            first_order_id = int(
                orders[0][0]
            )

            last_order_id = int(
                orders[-1][0]
            )

            expected_orders = len(orders)

            print()
            print(
                f"Processing orders "
                f"{first_order_id:,} → "
                f"{last_order_id:,} "
                f"({expected_orders:,} orders)"
            )

            # ------------------------------------------------
            # CHECK REPLAY STATE
            # ------------------------------------------------

            batch_state = check_batch_state(
                cursor,
                first_order_id,
                last_order_id,
                expected_orders,
            )

            print(
                f"Batch state: {batch_state}"
            )

            # =================================================
            # REPLAY
            # =================================================

            if batch_state == "REPLAY":

                print(
                    "REPLAY DETECTED: "
                    "history already exists."
                )

                print(
                    "Skipping history insertion."
                )

                update_checkpoint(
                    cursor,
                    last_order_id,
                )

                conn.commit()

                checkpoint = last_order_id

                total_orders_processed += (
                    expected_orders
                )

                total_orders_replayed += (
                    expected_orders
                )

                if remaining_for_execution is not None:

                    remaining_for_execution -= (
                        expected_orders
                    )

                print(
                    f"Checkpoint updated to: "
                    f"{checkpoint:,}"
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
                    "Some orders already have history "
                    "while others do not.\n"
                    "Generator stopped to avoid "
                    "inconsistent data."
                )

            # =================================================
            # NEW
            # =================================================

            history_buffer = []

            for order in orders:

                order_id = int(order[0])
                final_status = order[1]
                order_date = order[2]
                created_at = order[3]
                updated_at = order[4]

                history_rows = (
                    generate_history_for_order(
                        order_id,
                        final_status,
                        order_date,
                        created_at,
                        updated_at,
                        rng,
                    )
                )

                history_buffer.extend(
                    history_rows
                )

            total_history_rows_generated += (
                len(history_buffer)
            )

            # ------------------------------------------------
            # INSERT IN CHUNKS
            # ------------------------------------------------

            rows_inserted_this_batch = 0

            for i in range(
                0,
                len(history_buffer),
                INSERT_BATCH_SIZE,
            ):

                insert_batch = history_buffer[
                    i:i + INSERT_BATCH_SIZE
                ]

                insert_history(
                    cursor,
                    insert_batch,
                )

                rows_inserted_this_batch += (
                    len(insert_batch)
                )

                print(
                    f"Inserted history batch: "
                    f"{len(insert_batch):,}"
                )

            # ------------------------------------------------
            # COMMIT DATA
            # ------------------------------------------------

            conn.commit()

            total_history_rows_inserted += (
                rows_inserted_this_batch
            )

            total_orders_processed += (
                expected_orders
            )

            # ------------------------------------------------
            # CHECKPOINT
            # ------------------------------------------------

            update_checkpoint(
                cursor,
                last_order_id,
            )

            conn.commit()

            checkpoint = last_order_id

            print(
                f"History rows committed: "
                f"{rows_inserted_this_batch:,}"
            )

            print(
                f"Checkpoint updated to: "
                f"{checkpoint:,}"
            )

            # ------------------------------------------------
            # EXECUTION LIMIT
            # ------------------------------------------------

            if remaining_for_execution is not None:

                remaining_for_execution -= (
                    expected_orders
                )

                print(
                    f"Execution progress: "
                    f"{total_orders_processed:,}/"
                    f"{MAX_ORDERS:,} orders"
                )

            # ------------------------------------------------
            # PERFORMANCE
            # ------------------------------------------------

            elapsed = (
                time.time()
                - execution_start
            )

            if elapsed > 0:

                print(
                    f"Execution rate: "
                    f"{total_orders_processed / elapsed:,.0f} "
                    f"orders/sec | "
                    f"{total_history_rows_inserted / elapsed:,.0f} "
                    f"history rows/sec"
                )

        # ====================================================
        # SUMMARY
        # ====================================================

        elapsed = (
            time.time()
            - execution_start
        )

        print()
        print("=" * 70)
        print("ORDER STATUS HISTORY GENERATOR SUMMARY")
        print("=" * 70)

        print(
            f"Orders processed this run : "
            f"{total_orders_processed:,}"
        )

        print(
            f"History rows generated    : "
            f"{total_history_rows_generated:,}"
        )

        print(
            f"History rows inserted     : "
            f"{total_history_rows_inserted:,}"
        )

        print(
            f"Orders replayed           : "
            f"{total_orders_replayed:,}"
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
                f"History rows/sec          : "
                f"{total_history_rows_inserted / elapsed:,.0f}"
            )

        print("=" * 70)

    except Exception as exc:

        conn.rollback()

        print()
        print("=" * 70)
        print("ORDER STATUS HISTORY GENERATOR FAILED")
        print("=" * 70)

        print(
            f"Error: {exc}"
        )

        print(
            "Any uncommitted transaction "
            "has been rolled back."
        )

        print(
            f"Checkpoint remains at: "
            f"{get_checkpoint(cursor):,}"
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
    generate_status_history()
