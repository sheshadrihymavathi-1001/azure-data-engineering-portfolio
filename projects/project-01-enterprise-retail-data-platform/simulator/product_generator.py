"""Product volume and popularity-tier generator for Project 01."""

# TODO: add the validated local implementation.
import random
import time
from datetime import datetime, timedelta

from config.database import get_connection


TOTAL_PRODUCTS = 100_000
BATCH_SIZE = 5_000
SEED = 100


CATEGORIES = {
    "Electronics": [
        "Laptops",
        "Mobiles",
        "Tablets",
        "Headphones",
        "Cameras",
    ],
    "Home": [
        "Furniture",
        "Kitchen",
        "Lighting",
        "Storage",
        "Decor",
    ],
    "Fashion": [
        "Men Clothing",
        "Women Clothing",
        "Footwear",
        "Accessories",
        "Bags",
    ],
    "Grocery": [
        "Beverages",
        "Snacks",
        "Packaged Food",
        "Dairy",
        "Household",
    ],
    "Beauty": [
        "Skincare",
        "Haircare",
        "Makeup",
        "Personal Care",
        "Fragrance",
    ],
    "Sports": [
        "Fitness",
        "Outdoor",
        "Running",
        "Cycling",
        "Sportswear",
    ],
    "Toys": [
        "Educational",
        "Games",
        "Action Figures",
        "Puzzles",
        "Kids Toys",
    ],
    "Books": [
        "Fiction",
        "Non Fiction",
        "Technology",
        "Business",
        "Education",
    ],
}


BRANDS = [
    f"Brand_{i:04d}"
    for i in range(1, 1001)
]


PRICE_RANGES = [
    (100, 500, 0.30),
    (500, 2_000, 0.30),
    (2_000, 10_000, 0.25),
    (10_000, 50_000, 0.12),
    (50_000, 200_000, 0.03),
]


def weighted_price(rng):
    """
    Generate a deliberately skewed product-price distribution.
    """

    ranges = [
        (low, high, weight)
        for low, high, weight in PRICE_RANGES
    ]

    random_value = rng.random()
    cumulative = 0.0

    for low, high, weight in ranges:
        cumulative += weight

        if random_value <= cumulative:
            return round(
                rng.uniform(low, high),
                2
            )

    return round(
        rng.uniform(
            PRICE_RANGES[-1][0],
            PRICE_RANGES[-1][1]
        ),
        2
    )


def generate_product(product_number, rng):
    category = rng.choice(
        list(CATEGORIES.keys())
    )

    subcategory = rng.choice(
        CATEGORIES[category]
    )

    brand = rng.choice(BRANDS)

    product_name = (
        f"{brand} "
        f"{subcategory} "
        f"Product_{product_number:06d}"
    )

    unit_price = weighted_price(rng)

    product_status = (
        "ACTIVE"
        if rng.random() < 0.95
        else "INACTIVE"
    )

    # Spread product creation over roughly two years.
    created_at = (
        datetime.now()
        - timedelta(
            days=rng.randint(0, 730),
            seconds=rng.randint(0, 86_399)
        )
    )

    # Updated timestamp is always >= created timestamp.
    updated_at = created_at + timedelta(
        days=rng.randint(0, 180),
        seconds=rng.randint(0, 86_399)
    )

    return (
        product_name,
        category,
        subcategory,
        brand,
        unit_price,
        product_status,
        created_at,
        updated_at
    )


def generate_products(
    total_rows=TOTAL_PRODUCTS,
    batch_size=BATCH_SIZE,
    seed=SEED
):
    rng = random.Random(seed)

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO dbo.products
        (
            product_name,
            category,
            subcategory,
            brand,
            unit_price,
            product_status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    start_time = time.perf_counter()

    rows_generated = 0
    rows_inserted = 0

    try:
        cursor.fast_executemany = True

        while rows_generated < total_rows:

            current_batch_size = min(
                batch_size,
                total_rows - rows_generated
            )

            batch = []

            for _ in range(current_batch_size):

                product_number = (
                    rows_generated + 1
                )

                batch.append(
                    generate_product(
                        product_number,
                        rng
                    )
                )

                rows_generated += 1

            cursor.executemany(sql, batch)
            conn.commit()

            rows_inserted += len(batch)

            print(
                f"Batch loaded: "
                f"{rows_inserted:,}/{total_rows:,}"
            )

        elapsed = time.perf_counter() - start_time

        rows_per_second = (
            rows_inserted / elapsed
            if elapsed > 0
            else 0
        )

        print("\n====================================")
        print("PRODUCT GENERATION COMPLETE")
        print("====================================")
        print("Rows generated:", f"{rows_generated:,}")
        print("Rows inserted:", f"{rows_inserted:,}")
        print("Elapsed seconds:", f"{elapsed:.2f}")
        print("Rows/sec:", f"{rows_per_second:,.0f}")

    except Exception:
        conn.rollback()
        print(
            "\nProduct generation failed. "
            "Current batch rolled back."
        )
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    generate_products(
        total_rows=100_000,
        batch_size=5_000,
        seed=100
    )
