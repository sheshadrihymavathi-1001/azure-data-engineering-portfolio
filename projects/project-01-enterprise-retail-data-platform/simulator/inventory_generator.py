"""Inventory matrix generator with checkpoint/replay behavior for Project 01."""

# TODO: add the validated local implementation.
import random
import time
from datetime import datetime, timedelta

from config.database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

GENERATOR_NAME = "inventory_generator"

STORE_IDS = [1, 2, 3]

# First test:
# 3,000 products × 3 stores = 9,000 logical combinations
MAX_PRODUCTS = None

INSERT_BATCH_SIZE = 1_000

SIMULATE_CHECKPOINT_FAILURE = False

SEED = 1200

START_DATE = datetime(2026, 8, 1, 0, 0, 0)
END_DATE = datetime(2026, 8, 31, 23, 59, 59)


# ============================================================
# CHECKPOINT
# ============================================================

def get_checkpoint(cursor):
    cursor.execute(
        """
        SELECT last_product_id
        FROM dbo.inventory_generation_checkpoint
        WHERE generator_name = ?
        """,
        GENERATOR_NAME
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            f"Checkpoint not found for {GENERATOR_NAME}"
        )

    return row[0]


def update_checkpoint(cursor, last_product_id):
    cursor.execute(
        """
        UPDATE dbo.inventory_generation_checkpoint
        SET
            last_product_id = ?,
            updated_at = SYSDATETIME()
        WHERE generator_name = ?
        """,
        last_product_id,
        GENERATOR_NAME
    )


# ============================================================
# PRODUCT FETCH
# ============================================================

def fetch_product_batch(cursor, last_product_id, max_products):
    sql = """
        SELECT TOP (?)
            product_id
        FROM dbo.products
        WHERE product_id > ?
        ORDER BY product_id
    """

    cursor.execute(
        sql,
        max_products,
        last_product_id
    )

    return cursor.fetchall()


# ============================================================
# EXISTING COMBINATIONS
# ============================================================

def get_existing_combinations(
    cursor,
    product_ids
):
    """
    Return existing (store_id, product_id) combinations.

    This protects the generator from the 15 seed rows and
    also makes replay idempotent.
    """

    if not product_ids:
        return set()

    placeholders = ",".join(
        "?" for _ in product_ids
    )

    sql = f"""
        SELECT
            store_id,
            product_id
        FROM dbo.inventory
        WHERE store_id IN (1, 2, 3)
          AND product_id IN ({placeholders})
    """

    cursor.execute(sql, *product_ids)

    return {
        (row[0], row[1])
        for row in cursor.fetchall()
    }


# ============================================================
# INVENTORY VALUE GENERATION
# ============================================================

def generate_inventory_values(
    store_id,
    product_id,
    rng
):
    """
    Generate realistic inventory values.

    Quantity and reorder level are deterministic enough
    for reproducible testing while still looking realistic.
    """

    if store_id == 1:
        base_min = 10
        base_max = 120

    elif store_id == 2:
        base_min = 8
        base_max = 100

    else:
        base_min = 5
        base_max = 80

    quantity = rng.randint(
        base_min,
        base_max
    )

    # Reorder level should be lower than normal stock.
    reorder_level = max(
        3,
        int(quantity * rng.uniform(0.20, 0.40))
    )

    return quantity, reorder_level


# ============================================================
# UPDATED_AT GENERATION
# ============================================================

def generate_updated_at(
    product_id,
    store_id
):
    """
    Spread inventory timestamps across August 2026.

    The calculation is deterministic so that rerunning
    the generator does not produce random timestamps for
    already-existing rows.
    """

    total_seconds = int(
        (END_DATE - START_DATE).total_seconds()
    )

    offset = (
        product_id * 17
        + store_id * 997
    ) % total_seconds

    return START_DATE + timedelta(
        seconds=offset
    )


# ============================================================
# INSERT
# ============================================================

def insert_inventory_rows(
    cursor,
    rows
):
    if not rows:
        return

    cursor.executemany(
        """
        INSERT INTO dbo.inventory
        (
            store_id,
            product_id,
            quantity_on_hand,
            reorder_level,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        rows
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_inventory():
    start_time = time.time()

    rng = random.Random(SEED)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        last_product_id = get_checkpoint(cursor)

        print("=" * 70)
        print("INVENTORY GENERATOR")
        print("=" * 70)
        print(f"Starting checkpoint : {last_product_id:,}")
        print(f"Stores              : {STORE_IDS}")
        print(f"Max products        : {MAX_PRODUCTS}")
        print(f"Insert batch size   : {INSERT_BATCH_SIZE:,}")
        print()

        total_inserted = 0
        total_replayed = 0
        products_processed = 0

        while True:

            remaining = (
                MAX_PRODUCTS - products_processed
                if MAX_PRODUCTS is not None
                else 3_000
            )

            if remaining <= 0:
                break

            products = fetch_product_batch(
                cursor,
                last_product_id,
                min(remaining, 1_000)
            )

            if not products:
                break

            product_ids = [
                row[0]
                for row in products
            ]

            first_product_id = product_ids[0]
            last_product_id_batch = product_ids[-1]

            existing = get_existing_combinations(
                cursor,
                product_ids
            )

            batch_buffer = []

            expected_combinations = (
                len(product_ids) * len(STORE_IDS)
            )

            replayed = 0

            for product_id in product_ids:

                for store_id in STORE_IDS:

                    key = (
                        store_id,
                        product_id
                    )

                    if key in existing:
                        replayed += 1
                        continue

                    quantity, reorder_level = (
                        generate_inventory_values(
                            store_id,
                            product_id,
                            rng
                        )
                    )

                    updated_at = generate_updated_at(
                        product_id,
                        store_id
                    )

                    batch_buffer.append(
                        (
                            store_id,
                            product_id,
                            quantity,
                            reorder_level,
                            updated_at
                        )
                    )

            print(
                f"Products {first_product_id:,}"
                f" → {last_product_id_batch:,} | "
                f"Expected={expected_combinations:,} | "
                f"Insert={len(batch_buffer):,} | "
                f"Replay={replayed:,}"
            )

            # ------------------------------------------------
            # INSERT
            # ------------------------------------------------

            rows_inserted_this_batch = 0

            for i in range(
                0,
                len(batch_buffer),
                INSERT_BATCH_SIZE
            ):

                insert_batch = batch_buffer[
                    i:i + INSERT_BATCH_SIZE
                ]

                insert_inventory_rows(
                    cursor,
                    insert_batch
                )

                rows_inserted_this_batch += len(
                    insert_batch
                )

            # ------------------------------------------------
            # TARGET COMMIT
            # ------------------------------------------------

            conn.commit()

            total_inserted += (
                rows_inserted_this_batch
            )

            total_replayed += replayed

            products_processed += len(
                product_ids
            )

            # ------------------------------------------------
            # SIMULATED FAILURE
            # ------------------------------------------------

            if SIMULATE_CHECKPOINT_FAILURE:

                print(
                    "SIMULATED FAILURE:"
                    " inventory committed but checkpoint"
                    " not updated."
                )

                raise RuntimeError(
                    "SIMULATED CHECKPOINT FAILURE"
                )

            # ------------------------------------------------
            # CHECKPOINT
            # ------------------------------------------------

            update_checkpoint(
                cursor,
                last_product_id_batch
            )

            conn.commit()

            last_product_id = (
                last_product_id_batch
            )

            print(
                f"Checkpoint advanced → "
                f"{last_product_id:,}"
            )

            print()

        elapsed = time.time() - start_time

        print("=" * 70)
        print("GENERATION COMPLETE")
        print("=" * 70)

        print(
            f"Products processed : "
            f"{products_processed:,}"
        )

        print(
            f"Rows inserted      : "
            f"{total_inserted:,}"
        )

        print(
            f"Rows replayed      : "
            f"{total_replayed:,}"
        )

        print(
            f"Final checkpoint   : "
            f"{last_product_id:,}"
        )

        print(
            f"Elapsed            : "
            f"{elapsed:.2f} seconds"
        )

        if elapsed > 0:
            print(
                f"Rows/sec           : "
                f"{total_inserted / elapsed:,.0f}"
            )

    except Exception:

        conn.rollback()

        print()
        print(
            "GENERATOR FAILED."
        )

        raise

    finally:
        conn.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    generate_inventory()
