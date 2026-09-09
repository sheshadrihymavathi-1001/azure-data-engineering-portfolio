"""Store generator for Project 01."""

# TODO: add the validated local implementation.
import sys
import os
import random
import time
from datetime import datetime

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

GENERATOR_NAME = "store_generator"

# Logical transaction size
BATCH_SIZE = 100

# ------------------------------------------------------------
# TEST CONTROL
# ------------------------------------------------------------
# 10   -> generate 10 stores in this run
# 100  -> generate 100 stores
# None -> generate until target is reached
# ------------------------------------------------------------

MAX_STORES = None

TARGET_STORE_COUNT = 1_000

SEED = 700


# ============================================================
# STORE TYPE DISTRIBUTION
# ============================================================

STORE_TYPES = [
    "RETAIL",
    "OUTLET",
    "WAREHOUSE",
]

STORE_TYPE_WEIGHTS = [
    0.70,
    0.20,
    0.10,
]


# ============================================================
# LOCATION DATA
# ============================================================

LOCATIONS = [
    ("Mumbai", "Maharashtra", "India"),
    ("Pune", "Maharashtra", "India"),
    ("Nagpur", "Maharashtra", "India"),
    ("Bengaluru", "Karnataka", "India"),
    ("Mysuru", "Karnataka", "India"),
    ("Hyderabad", "Telangana", "India"),
    ("Warangal", "Telangana", "India"),
    ("Chennai", "Tamil Nadu", "India"),
    ("Coimbatore", "Tamil Nadu", "India"),
    ("Delhi", "Delhi", "India"),
    ("Noida", "Uttar Pradesh", "India"),
    ("Lucknow", "Uttar Pradesh", "India"),
    ("Ahmedabad", "Gujarat", "India"),
    ("Surat", "Gujarat", "India"),
    ("Jaipur", "Rajasthan", "India"),
    ("Kolkata", "West Bengal", "India"),
    ("Bhubaneswar", "Odisha", "India"),
    ("Kochi", "Kerala", "India"),
    ("Thiruvananthapuram", "Kerala", "India"),
    ("Visakhapatnam", "Andhra Pradesh", "India"),
]


# ============================================================
# CHECKPOINT
# ============================================================

def get_checkpoint(cursor):
    cursor.execute(
        """
        SELECT last_store_id
        FROM dbo.store_generation_checkpoint
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


def update_checkpoint(cursor, last_store_id):

    cursor.execute(
        """
        UPDATE dbo.store_generation_checkpoint
        SET
            last_store_id = ?,
            updated_at = SYSDATETIME()
        WHERE generator_name = ?
        """,
        last_store_id,
        GENERATOR_NAME,
    )

    if cursor.rowcount != 1:
        raise RuntimeError(
            "Checkpoint update failed."
        )


# ============================================================
# STORE COUNT
# ============================================================

def get_store_count(cursor):

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM dbo.stores
        """
    )

    return int(cursor.fetchone()[0])


# ============================================================
# GENERATE STORE
# ============================================================

def generate_store(store_number, rng):

    city, state, country = rng.choice(LOCATIONS)

    store_type = rng.choices(
        STORE_TYPES,
        weights=STORE_TYPE_WEIGHTS,
        k=1,
    )[0]

    store_name = (
        f"{city} {store_type.title()} Store "
        f"{store_number}"
    )

    now = datetime.now()

    return (
        store_name,
        city,
        state,
        country,
        store_type,
        now,
        now,
    )


# ============================================================
# INSERT STORES
# ============================================================

def insert_stores(cursor, rows):

    cursor.fast_executemany = True

    cursor.executemany(
        """
        INSERT INTO dbo.stores
        (
            store_name,
            city,
            state,
            country,
            store_type,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


# ============================================================
# MAIN
# ============================================================

def generate_stores():

    rng = random.Random(SEED)

    conn = get_connection()
    cursor = conn.cursor()

    execution_start = time.time()

    total_inserted = 0
    total_batches = 0

    try:

        # ----------------------------------------------------
        # READ CHECKPOINT
        # ----------------------------------------------------

        checkpoint = get_checkpoint(cursor)

        current_store_count = get_store_count(cursor)

        print("=" * 70)
        print("STORE GENERATOR")
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
            f"Current store count    : "
            f"{current_store_count:,}"
        )

        print(
            f"Target store count     : "
            f"{TARGET_STORE_COUNT:,}"
        )

        print(
            f"Batch size             : "
            f"{BATCH_SIZE:,}"
        )

        print(
            f"Maximum stores / run  : "
            f"{MAX_STORES}"
        )

        print(
            f"Seed                   : "
            f"{SEED}"
        )

        print("=" * 70)

        # ----------------------------------------------------
        # DETERMINE WORK
        # ----------------------------------------------------

        remaining_to_target = (
            TARGET_STORE_COUNT
            - current_store_count
        )

        if remaining_to_target <= 0:

            print()
            print(
                "Target store count already reached."
            )

            return

        if MAX_STORES is None:

            stores_for_execution = remaining_to_target

        else:

            stores_for_execution = min(
                MAX_STORES,
                remaining_to_target,
            )

        print(
            f"Stores to generate this run: "
            f"{stores_for_execution:,}"
        )

        generated_this_run = 0

        # ====================================================
        # GENERATION LOOP
        # ====================================================

        while generated_this_run < stores_for_execution:

            remaining_this_run = (
                stores_for_execution
                - generated_this_run
            )

            batch_size = min(
                BATCH_SIZE,
                remaining_this_run,
            )

            # ------------------------------------------------
            # Generate rows
            # ------------------------------------------------

            rows = []

            for i in range(batch_size):

                # This number is only used for the store name.
                # SQL Server generates the actual store_id.
                store_number = (
                    checkpoint
                    + generated_this_run
                    + i
                    + 1
                )

                rows.append(
                    generate_store(
                        store_number,
                        rng,
                    )
                )

            # ------------------------------------------------
            # INSERT
            # ------------------------------------------------

            insert_stores(
                cursor,
                rows,
            )

            # ------------------------------------------------
            # Get actual identity values BEFORE COMMIT
            # ------------------------------------------------
            #
            # Since this is a local single-generator process,
            # MAX(store_id) gives us the highest assigned ID.
            #
            # SQL Server remains the authority for store_id.
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT MAX(store_id)
                FROM dbo.stores
                """
            )

            actual_last_store_id = int(
                cursor.fetchone()[0]
            )

            # ------------------------------------------------
            # CHECKPOINT
            # ------------------------------------------------

            update_checkpoint(
                cursor,
                actual_last_store_id,
            )

            # ------------------------------------------------
            # COMMIT INSERT + CHECKPOINT TOGETHER
            # ------------------------------------------------

            conn.commit()

            checkpoint = actual_last_store_id

            generated_this_run += batch_size
            total_inserted += batch_size
            total_batches += 1

            print()
            print(
                f"Inserted stores        : "
                f"{batch_size:,}"
            )

            print(
                f"Checkpoint updated to  : "
                f"{checkpoint:,}"
            )

            print(
                f"Execution progress     : "
                f"{generated_this_run:,}/"
                f"{stores_for_execution:,}"
            )

        # ====================================================
        # SUMMARY
        # ====================================================

        elapsed = time.time() - execution_start

        print()
        print("=" * 70)
        print("STORE GENERATOR SUMMARY")
        print("=" * 70)

        print(
            f"Stores inserted this run : "
            f"{total_inserted:,}"
        )

        print(
            f"Batches processed        : "
            f"{total_batches:,}"
        )

        print(
            f"Final checkpoint         : "
            f"{checkpoint:,}"
        )

        print(
            f"Elapsed                  : "
            f"{elapsed:,.2f} sec"
        )

        if elapsed > 0:

            print(
                f"Stores/sec               : "
                f"{total_inserted / elapsed:,.0f}"
            )

        print("=" * 70)

    except Exception as exc:

        conn.rollback()

        print()
        print("=" * 70)
        print("STORE GENERATOR FAILED")
        print("=" * 70)

        print(f"Error: {exc}")

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
    generate_stores()
