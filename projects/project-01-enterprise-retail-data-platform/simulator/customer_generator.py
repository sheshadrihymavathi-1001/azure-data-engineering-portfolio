"""Customer volume generator for Project 01."""

# TODO: add the validated local implementation.
from datetime import datetime, timedelta
import random
import time

from config.database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_ROW_COUNT = 10_000
DEFAULT_BATCH_SIZE = 1_000
RANDOM_SEED = 42


# ============================================================
# REFERENCE DATA
# ============================================================

FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Ananya", "Rahul",
    "Priya", "Karthik", "Neha", "Vikram", "Sneha",
    "Rohan", "Pooja", "Amit", "Divya", "Sanjay",
    "Kavya", "Nikhil", "Meera", "Raj", "Isha",
]

LAST_NAMES = [
    "Sharma", "Patel", "Reddy", "Rao", "Kumar",
    "Singh", "Verma", "Gupta", "Mehta", "Nair",
    "Iyer", "Joshi", "Das", "Kapoor", "Malhotra",
]

LOCATIONS = [
    ("Hyderabad", "Telangana"),
    ("Bengaluru", "Karnataka"),
    ("Chennai", "Tamil Nadu"),
    ("Mumbai", "Maharashtra"),
    ("Pune", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Kolkata", "West Bengal"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
    ("Kochi", "Kerala"),
]

COUNTRY = "India"


# ============================================================
# DATA GENERATION
# ============================================================

def generate_customer_batch(
    start_number,
    batch_size,
    rng
):
    """
    Generate one batch of customer records.

    The generated data is deterministic when the same
    random seed is supplied.
    """

    rows = []

    base_time = datetime(2026, 1, 1, 0, 0, 0)

    for i in range(batch_size):

        logical_number = start_number + i

        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)

        city, state = rng.choice(LOCATIONS)

        email = (
            f"customer{logical_number:07d}"
            "@contosoretail.example"
        )

        phone = f"9{logical_number:09d}"

        random_seconds = rng.randint(
            0,
            365 * 24 * 60 * 60
        )

        created_at = (
            base_time +
            timedelta(seconds=random_seconds)
        )

        update_seconds = rng.randint(
            0,
            30 * 24 * 60 * 60
        )

        updated_at = (
            created_at +
            timedelta(seconds=update_seconds)
        )

        customer_status = (
            "ACTIVE"
            if rng.random() < 0.95
            else "INACTIVE"
        )

        rows.append(
            (
                first_name,
                last_name,
                email,
                phone,
                city,
                state,
                COUNTRY,
                customer_status,
                created_at,
                updated_at
            )
        )

    return rows


# ============================================================
# DATABASE LOAD
# ============================================================

def insert_customer_batch(cursor, rows):
    """
    Insert one batch using an existing SQL connection.

    The cursor belongs to the connection created by the
    calling function.
    """

    if not rows:
        return 0

    cursor.fast_executemany = True

    cursor.executemany(
        """
        INSERT INTO dbo.customers
        (
            first_name,
            last_name,
            email,
            phone,
            city,
            state,
            country,
            customer_status,
            created_at,
            updated_at
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        rows
    )

    return len(rows)


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_customers(
    total_rows=DEFAULT_ROW_COUNT,
    batch_size=DEFAULT_BATCH_SIZE,
    seed=RANDOM_SEED,
    start_number=1
):
    """
    Generate and bulk-load customers into SQL Server.

    One database connection is reused for the entire run.
    """

    if total_rows <= 0:
        raise ValueError(
            "total_rows must be greater than zero"
        )

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be greater than zero"
        )

    if start_number <= 0:
        raise ValueError(
        "start_number must be greater than zero"
    )

    print("====================================")
    print("CONTOSO CUSTOMER DATA GENERATOR")
    print("====================================")

    print("Total rows :", total_rows)
    print("Batch size :", batch_size)
    print("Random seed:", seed)

    rng = random.Random(seed)

    start_time = time.perf_counter()

    rows_generated = 0
    rows_inserted = 0
    batch_number = 0

    conn = get_connection()

    try:

        cursor = conn.cursor()

        while rows_generated < total_rows:

            remaining_rows = (
                total_rows - rows_generated
            )

            current_batch_size = min(
                batch_size,
                remaining_rows
            )

            batch_number += 1

            batch = generate_customer_batch(
                start_number=start_number + rows_generated,
                batch_size=current_batch_size,
                rng=rng
            )

            inserted = insert_customer_batch(
                cursor,
                batch
            )

            conn.commit()

            rows_generated += current_batch_size
            rows_inserted += inserted

            elapsed = (
                time.perf_counter()
                - start_time
            )

            rows_per_second = (
                rows_inserted / elapsed
                if elapsed > 0
                else 0
            )

            print(
                f"Batch {batch_number:04d} | "
                f"Rows: "
                f"{rows_inserted:,}/{total_rows:,} | "
                f"Rate: "
                f"{rows_per_second:,.0f} rows/sec"
            )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        rows_per_second = (
            rows_inserted / elapsed
            if elapsed > 0
            else 0
        )

        print("\n====================================")
        print("GENERATION COMPLETE")
        print("====================================")

        print(
            "Rows generated :",
            rows_generated
        )

        print(
            "Rows inserted  :",
            rows_inserted
        )

        print(
            "Elapsed seconds:",
            f"{elapsed:.2f}"
        )

        print(
            "Rows/sec       :",
            f"{rows_per_second:,.0f}"
        )

        return {
            "rows_generated": rows_generated,
            "rows_inserted": rows_inserted,
            "elapsed_seconds": elapsed,
            "rows_per_second": rows_per_second
        }

    except Exception:
        conn.rollback()

        print(
            "\nGeneration failed. "
            "Current batch transaction rolled back."
        )

        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    generate_customers(
        total_rows=900_000,
        batch_size=1_000,
        start_number=100_001
    )
