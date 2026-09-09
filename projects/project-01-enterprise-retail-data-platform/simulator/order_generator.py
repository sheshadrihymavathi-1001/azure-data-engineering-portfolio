"""Order volume generator for Project 01."""

# TODO: add the validated local implementation.
import random
import time
from datetime import datetime, timedelta

from config.database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

STORE_DISTRIBUTION = {
    1: 0.50,
    2: 0.30,
    3: 0.20
}

ORDER_STATUS_DISTRIBUTION = {
    "DELIVERED": 0.70,
    "SHIPPED": 0.10,
    "CONFIRMED": 0.08,
    "PLACED": 0.07,
    "CANCELLED": 0.05
}

ORDER_AMOUNT_DISTRIBUTION = {
    "100_2000": 0.70,
    "2000_10000": 0.25,
    "10000_50000": 0.045,
    "50000_100000": 0.005
}

# Percentage of orders allocated to each customer activity tier.
ORDER_TIER_DISTRIBUTION = {
    "HIGH": 0.50,
    "MEDIUM": 0.35,
    "LOW": 0.15
}

START_ORDER_DATE = datetime(2025, 9, 1)
END_ORDER_DATE = datetime(2026, 8, 31, 23, 59, 59)

CUSTOMER_ID_BATCH_SIZE = 50_000


# ============================================================
# CUSTOMER PROFILE LOADING
# ============================================================

def load_customer_ids_by_tier():
    """
    Load customer IDs from the explicit activity profile table.

    Returns:
        {
            "HIGH": [...],
            "MEDIUM": [...],
            "LOW": [...]
        }

    Customer IDs are fetched in batches to avoid transferring
    the entire dataset through one large ODBC operation.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        customers_by_tier = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }

        last_customer_id = 0

        while True:

            cursor.execute(
                """
                SELECT TOP (?)
                    p.customer_id,
                    p.activity_tier
                FROM dbo.customer_activity_profile p
                JOIN dbo.customers c
                    ON p.customer_id = c.customer_id
                WHERE p.customer_id > ?
                  AND c.email LIKE 'customer%@contosoretail.example'
                ORDER BY p.customer_id
                """,
                CUSTOMER_ID_BATCH_SIZE,
                last_customer_id
            )

            rows = cursor.fetchall()

            if not rows:
                break

            for row in rows:
                customer_id = row[0]
                activity_tier = row[1]

                customers_by_tier[activity_tier].append(
                    customer_id
                )

            last_customer_id = rows[-1][0]

            total_loaded = sum(
                len(ids)
                for ids in customers_by_tier.values()
            )

            print(
                "Loaded customer profiles:",
                f"{total_loaded:,}"
            )

        for tier in customers_by_tier:
            print(
                f"{tier} customers:",
                f"{len(customers_by_tier[tier]):,}"
            )

        total_customers = sum(
            len(ids)
            for ids in customers_by_tier.values()
        )

        if total_customers == 0:
            raise ValueError(
                "No customer activity profiles found."
            )

        print(
            "Total customer profiles loaded:",
            f"{total_customers:,}"
        )

        return customers_by_tier

    finally:
        cursor.close()
        conn.close()


# ============================================================
# RANDOM SELECTION
# ============================================================

def select_customer(
    customers_by_tier,
    rng
):
    """
    Select a customer according to the intended
    order allocation distribution.
    """

    value = rng.random()

    if value < ORDER_TIER_DISTRIBUTION["HIGH"]:
        tier = "HIGH"

    elif value < (
        ORDER_TIER_DISTRIBUTION["HIGH"]
        + ORDER_TIER_DISTRIBUTION["MEDIUM"]
    ):
        tier = "MEDIUM"

    else:
        tier = "LOW"

    customer_id = rng.choice(
        customers_by_tier[tier]
    )

    return customer_id, tier


# ============================================================
# ORDER ATTRIBUTES
# ============================================================

def generate_store_id(rng):
    value = rng.random()

    if value < STORE_DISTRIBUTION[1]:
        return 1

    elif value < (
        STORE_DISTRIBUTION[1]
        + STORE_DISTRIBUTION[2]
    ):
        return 2

    return 3


def generate_order_status(rng):
    value = rng.random()

    cumulative = 0.0

    for status, probability in ORDER_STATUS_DISTRIBUTION.items():

        cumulative += probability

        if value < cumulative:
            return status

    return "DELIVERED"


def generate_order_amount(rng):
    value = rng.random()

    if value < ORDER_AMOUNT_DISTRIBUTION["100_2000"]:
        return round(
            rng.uniform(100, 2000),
            2
        )

    value -= ORDER_AMOUNT_DISTRIBUTION["100_2000"]

    if value < ORDER_AMOUNT_DISTRIBUTION["2000_10000"]:
        return round(
            rng.uniform(2000, 10000),
            2
        )

    value -= ORDER_AMOUNT_DISTRIBUTION["2000_10000"]

    if value < ORDER_AMOUNT_DISTRIBUTION["10000_50000"]:
        return round(
            rng.uniform(10000, 50000),
            2
        )

    return round(
        rng.uniform(50000, 100000),
        2
    )


def generate_order_date(rng):
    total_seconds = int(
        (
            END_ORDER_DATE - START_ORDER_DATE
        ).total_seconds()
    )

    random_seconds = rng.randint(
        0,
        total_seconds
    )

    return (
        START_ORDER_DATE
        + timedelta(seconds=random_seconds)
    )


# ============================================================
# ORDER BATCH GENERATION
# ============================================================

def generate_order_batch(
    batch_size,
    customers_by_tier,
    rng
):
    """
    Generate one batch of orders.

    Returns:
        rows
        tier_counts
    """

    rows = []

    tier_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    for _ in range(batch_size):

        customer_id, tier = select_customer(
            customers_by_tier,
            rng
        )

        store_id = generate_store_id(rng)
        order_date = generate_order_date(rng)
        order_status = generate_order_status(rng)
        total_amount = generate_order_amount(rng)

        created_at = order_date

        updated_at = created_at + timedelta(
            seconds=rng.randint(0, 7 * 24 * 60 * 60)
        )

        rows.append(
            (
                customer_id,
                store_id,
                order_date,
                order_status,
                total_amount,
                created_at,
                updated_at
            )
        )

        tier_counts[tier] += 1

    return rows, tier_counts


# ============================================================
# BATCH INSERT
# ============================================================

def insert_order_batch(
    cursor,
    rows
):
    cursor.fast_executemany = True

    cursor.executemany(
        """
        INSERT INTO dbo.orders
        (
            customer_id,
            store_id,
            order_date,
            order_status,
            total_amount,
            created_at,
            updated_at
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?)
        """,
        rows
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_orders(
    total_rows=100_000,
    batch_size=1_000,
    seed=42
):
    print("====================================")
    print("CONTOSO ORDER DATA GENERATOR")
    print("====================================")
    print("Total rows :", f"{total_rows:,}")
    print("Batch size :", f"{batch_size:,}")
    print("Random seed:", seed)
    print()

    print("Loading customer activity profiles...")

    customers_by_tier = load_customer_ids_by_tier()

    print()

    rng = random.Random(seed)

    total_generated = 0

    total_tier_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    start_time = time.perf_counter()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        batch_number = 0

        while total_generated < total_rows:

            remaining = total_rows - total_generated

            current_batch_size = min(
                batch_size,
                remaining
            )

            batch_number += 1

            rows, tier_counts = generate_order_batch(
                current_batch_size,
                customers_by_tier,
                rng
            )

            insert_order_batch(
                cursor,
                rows
            )

            conn.commit()

            total_generated += current_batch_size

            for tier in total_tier_counts:
                total_tier_counts[tier] += tier_counts[tier]

            elapsed = (
                time.perf_counter()
                - start_time
            )

            rows_per_second = (
                total_generated / elapsed
                if elapsed > 0
                else 0
            )

            print(
                f"Batch {batch_number:04d} | "
                f"Rows: {total_generated:,}/{total_rows:,} | "
                f"Rate: {rows_per_second:,.0f} rows/sec"
            )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        rows_per_second = (
            total_generated / elapsed
            if elapsed > 0
            else 0
        )

        print()
        print("====================================")
        print("GENERATION COMPLETE")
        print("====================================")
        print(
            "Rows generated :",
            f"{total_generated:,}"
        )
        print(
            "Rows inserted  :",
            f"{total_generated:,}"
        )
        print(
            "Elapsed seconds:",
            f"{elapsed:.2f}"
        )
        print(
            "Rows/sec       :",
            f"{rows_per_second:,.0f}"
        )

        print()
        print("ORDER ALLOCATION BY CUSTOMER TIER")
        print("------------------------------------")

        for tier in [
            "HIGH",
            "MEDIUM",
            "LOW"
        ]:

            count = total_tier_counts[tier]

            percentage = (
                count * 100.0 / total_generated
                if total_generated > 0
                else 0
            )

            print(
                f"{tier:<8}: "
                f"{count:>8,} "
                f"({percentage:>5.2f}%)"
            )

    except Exception:
        conn.rollback()

        print()
        print("====================================")
        print("GENERATION FAILED")
        print("====================================")

        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    generate_orders(
        total_rows=4_000_000,
        batch_size=5_000,
        seed=44
    )
