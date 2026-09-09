"""Order-item generator with checkpoint/replay behavior for Project 01."""

# TODO: add the validated local implementation.
import random
import time
from decimal import Decimal, ROUND_HALF_UP

from config.database import get_connection


TOTAL_ORDERS = 5_000_000
ORDER_BATCH_SIZE = 50_000
INSERT_BATCH_SIZE = 5_000
SEED = 200

GENERATOR_NAME = "order_item_generator"

# Set to True later when we deliberately test
# failure between item commit and checkpoint update.
SIMULATE_CHECKPOINT_FAILURE = False


ITEM_COUNT_DISTRIBUTION = [
    (1, 0.10),
    (2, 0.20),
    (3, 0.25),
    (4, 0.25),
    (5, 0.12),
    (6, 0.05),
    (7, 0.02),
    (8, 0.01),
]


PRODUCT_TIER_DISTRIBUTION = [
    ("VERY_HIGH", 0.50),
    ("HIGH", 0.30),
    ("MEDIUM", 0.15),
    ("LOW", 0.05),
]


def load_products():
    """
    Load product_id and unit_price grouped by popularity tier.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                p.product_id,
                p.unit_price,
                pp.popularity_tier
            FROM dbo.products p
            INNER JOIN dbo.product_popularity_profile pp
                ON p.product_id = pp.product_id
            WHERE p.product_name LIKE 'Brand_% Product_%'
            """
        )

        products_by_tier = {
            "VERY_HIGH": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }

        for row in cursor.fetchall():
            product_id = row[0]
            unit_price = Decimal(str(row[1]))
            tier = row[2]

            products_by_tier[tier].append(
                (product_id, unit_price)
            )

        total_products = sum(
            len(products)
            for products in products_by_tier.values()
        )

        print("Products loaded:", f"{total_products:,}")

        for tier, products in products_by_tier.items():
            print(
                f"{tier}: {len(products):,}"
            )

        if total_products != 100_000:
            raise ValueError(
                f"Expected 100,000 products, "
                f"found {total_products:,}"
            )

        return products_by_tier

    finally:
        cursor.close()
        conn.close()


def choose_item_count(rng):
    value = rng.random()
    cumulative = 0.0

    for item_count, probability in ITEM_COUNT_DISTRIBUTION:
        cumulative += probability

        if value <= cumulative:
            return item_count

    return ITEM_COUNT_DISTRIBUTION[-1][0]


def choose_product(rng, products_by_tier):
    value = rng.random()
    cumulative = 0.0

    selected_tier = None

    for tier, probability in PRODUCT_TIER_DISTRIBUTION:
        cumulative += probability

        if value <= cumulative:
            selected_tier = tier
            break

    products = products_by_tier[selected_tier]

    return rng.choice(products)


def choose_quantity(rng):
    value = rng.random()

    if value < 0.70:
        return rng.randint(1, 2)

    if value < 0.95:
        return rng.randint(3, 5)

    return rng.randint(6, 10)


def allocate_order_amount(
    target_amount,
    selected_products,
    rng
):
    """
    Generate quantities and discounts while ensuring
    line amounts reconcile exactly to orders.total_amount.
    """

    target_amount = Decimal(
        str(target_amount)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    item_count = len(selected_products)

    quantities = [
        choose_quantity(rng)
        for _ in range(item_count)
    ]

    gross_amounts = []

    for (_, unit_price), quantity in zip(
        selected_products,
        quantities
    ):
        gross = (
            unit_price *
            Decimal(quantity)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        gross_amounts.append(gross)

    total_gross = sum(
        gross_amounts,
        Decimal("0.00")
    )

    if total_gross < target_amount:

        product_id, unit_price = selected_products[-1]

        while total_gross < target_amount:

            quantities[-1] += 1

            gross_amounts[-1] = (
                unit_price *
                Decimal(quantities[-1])
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            total_gross = sum(
                gross_amounts,
                Decimal("0.00")
            )

    if total_gross < target_amount:
        raise ValueError(
            "Unable to allocate order total."
        )

    line_amounts = []

    remaining_amount = target_amount

    for index, gross in enumerate(gross_amounts):

        remaining_gross = sum(
            gross_amounts[index + 1:],
            Decimal("0.00")
        )

        minimum_allocation = max(
            Decimal("0.00"),
            remaining_amount - remaining_gross
        )

        maximum_allocation = min(
            gross,
            remaining_amount
        )

        if minimum_allocation > maximum_allocation:
            raise ValueError(
                "Unable to allocate order total "
                "within item gross capacities."
            )

        if index == item_count - 1:

            line_amount = remaining_amount

        else:

            line_amount = (
                minimum_allocation
                +
                (
                    maximum_allocation
                    - minimum_allocation
                )
                * Decimal(str(rng.random()))
            )

            line_amount = line_amount.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            line_amount = min(
                line_amount,
                maximum_allocation
            )

        line_amounts.append(line_amount)

        remaining_amount -= line_amount

    allocated_total = sum(
        line_amounts,
        Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if allocated_total != target_amount:
        raise ValueError(
            f"Order total allocation mismatch. "
            f"Target={target_amount}, "
            f"Allocated={allocated_total}"
        )

    results = []

    for index, (
        product_id,
        unit_price
    ) in enumerate(selected_products):

        gross = gross_amounts[index]
        line_amount = line_amounts[index]

        discount_amount = (
            gross - line_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        if discount_amount < Decimal("0.00"):
            raise ValueError(
                "Negative discount generated."
            )

        results.append(
            (
                product_id,
                quantities[index],
                unit_price,
                discount_amount,
                line_amount
            )
        )

    return results


def get_checkpoint(cursor):
    cursor.execute(
        """
        SELECT last_order_id
        FROM dbo.order_item_generation_checkpoint
        WHERE generator_name = ?
        """,
        GENERATOR_NAME
    )

    row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"No checkpoint found for "
            f"{GENERATOR_NAME}"
        )

    return row[0]


def update_checkpoint(cursor, last_order_id):
    cursor.execute(
        """
        UPDATE dbo.order_item_generation_checkpoint
        SET
            last_order_id = ?,
            updated_at = SYSDATETIME()
        WHERE generator_name = ?
        """,
        last_order_id,
        GENERATOR_NAME
    )

    if cursor.rowcount != 1:
        raise ValueError(
            "Checkpoint update failed."
        )


def fetch_order_batch(
    cursor,
    last_order_id,
    batch_size
):
    cursor.execute(
        """
        SELECT TOP (?)
            o.order_id,
            o.total_amount
        FROM dbo.orders o
        INNER JOIN dbo.customers c
            ON o.customer_id = c.customer_id
        WHERE o.order_id > ?
          AND c.email LIKE 'customer%@contosoretail.example'
        ORDER BY o.order_id
        """,
        batch_size,
        last_order_id
    )

    return cursor.fetchall()


def insert_order_items(
    cursor,
    rows
):
    if not rows:
        return

    cursor.executemany(
        """
        INSERT INTO dbo.order_items
        (
            order_id,
            product_id,
            quantity,
            unit_price,
            discount_amount,
            line_amount,
            created_at,
            updated_at
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            SYSDATETIME(),
            SYSDATETIME()
        )
        """,
        rows
    )

def check_batch_state(cursor, first_order_id, last_order_id, expected_orders):
    """
    Determine whether the current order batch is:
      1. Not processed yet
      2. Already committed (replay)
      3. Partially processed / inconsistent
    """

    cursor.execute(
        """
        SELECT COUNT(DISTINCT oi.order_id)
        FROM dbo.order_items oi
        INNER JOIN dbo.orders o
            ON oi.order_id = o.order_id
        INNER JOIN dbo.customers c
            ON o.customer_id = c.customer_id
        WHERE oi.order_id BETWEEN ? AND ?
          AND c.email LIKE 'customer%@contosoretail.example'
        """,
        first_order_id,
        last_order_id
    )

    existing_orders = cursor.fetchone()[0]

    if existing_orders == 0:
        return "NEW"

    if existing_orders == expected_orders:
        return "REPLAY"

    return "PARTIAL"

def generate_order_items(
    total_orders=TOTAL_ORDERS,
    order_batch_size=ORDER_BATCH_SIZE,
    insert_batch_size=INSERT_BATCH_SIZE,
    seed=SEED,
    start_order_id=None
):

    rng = random.Random(seed)

    print("====================================")
    print("ORDER ITEM GENERATOR")
    print("====================================")

    print(
        "Target orders:",
        f"{total_orders:,}"
    )

    print(
        "Order batch size:",
        f"{order_batch_size:,}"
    )

    print(
        "Insert batch size:",
        f"{insert_batch_size:,}"
    )

    print("Seed:", seed)

    products_by_tier = load_products()

    conn = get_connection()
    cursor = conn.cursor()

    start_time = time.perf_counter()

    try:

        checkpoint_order_id = get_checkpoint(cursor)

        if start_order_id is not None:
            last_order_id = start_order_id
        else:
            last_order_id = checkpoint_order_id

        print(
            "Checkpoint order ID:",
            last_order_id
        )

        orders_processed = 0
        rows_generated = 0
        rows_inserted = 0

        while orders_processed < total_orders:

            remaining_orders = (
                total_orders -
                orders_processed
            )

            current_batch_size = min(
                order_batch_size,
                remaining_orders
            )

            orders = fetch_order_batch(
                cursor,
                last_order_id,
                current_batch_size
            )

            if not orders:
                print(
                    "No more eligible orders."
                )
                break

            print(
                "\nProcessing order range:",
                f"{orders[0][0]:,}",
                "→",
                f"{orders[-1][0]:,}"
            )

            batch_buffer = []

            for order in orders:

                order_id = order[0]

                order_total = Decimal(
                    str(order[1])
                )

                item_count = choose_item_count(
                    rng
                )

                selected_products = []
                selected_product_ids = set()

                while len(selected_products) < item_count:

                    product = choose_product(
                        rng,
                        products_by_tier
                    )

                    product_id = product[0]

                    if product_id in selected_product_ids:
                        continue

                    selected_product_ids.add(
                        product_id
                    )

                    selected_products.append(
                        product
                    )

                items = allocate_order_amount(
                    order_total,
                    selected_products,
                    rng
                )

                for (
                    product_id,
                    quantity,
                    unit_price,
                    discount_amount,
                    line_amount
                ) in items:

                    batch_buffer.append(
                        (
                            order_id,
                            product_id,
                            quantity,
                            unit_price,
                            discount_amount,
                            line_amount
                        )
                    )

                    rows_generated += 1

            first_order_id = orders[0][0]
            last_order_id = orders[-1][0]
            expected_orders = len(orders)

            # Check whether this batch is new, already committed, or partial.
            batch_state = check_batch_state(
                cursor,
                first_order_id,
                last_order_id,
                expected_orders
            )

            print("Batch state:", batch_state)

            if batch_state == "NEW":

                # Insert the complete order batch in smaller database batches.
                # All inserts remain part of the same transaction.
                for i in range(0, len(batch_buffer), insert_batch_size):

                    insert_batch = batch_buffer[
                        i:i + insert_batch_size
                    ]

                    insert_order_items(
                        cursor,
                        insert_batch
                    )

                    rows_inserted += len(insert_batch)

                    print(
                        f"Inserted batch: "
                        f"{len(insert_batch):,} items"
                    )

                # Commit the COMPLETE order batch only after
                # every insert batch succeeds.
                conn.commit()

                print(
                    f"Inserted {len(batch_buffer):,} order items."
                )

            elif batch_state == "REPLAY":

                print(
                    "REPLAY DETECTED: "
                    "order items already committed. "
                    "Skipping insertion."
                )

            else:

                raise RuntimeError(
                    f"PARTIAL BATCH DETECTED: "
                    f"{first_order_id} → {last_order_id}. "
                    f"Refusing to continue."
                )

            # Simulate failure only after target processing
            # and before checkpoint advancement.
            if SIMULATE_CHECKPOINT_FAILURE:
                raise RuntimeError(
                    "SIMULATED FAILURE: "
                    "item batch committed but checkpoint not updated."
                )

            # Advance checkpoint only after successful target processing.
            update_checkpoint(
                cursor,
                last_order_id
            )

            conn.commit()

            print(
                f"Checkpoint updated to: {last_order_id}"
            )

            # Failure simulation is deliberately placed
            # AFTER the item commit but BEFORE checkpoint update.
            if SIMULATE_CHECKPOINT_FAILURE:
                raise RuntimeError(
                    "SIMULATED FAILURE: "
                    "item batch committed but "
                    "checkpoint not updated."
                )

            # Update checkpoint only after successful
            # item commit.
            update_checkpoint(
                cursor,
                last_order_id
            )

            conn.commit()

            orders_processed += len(orders)

            print(
                f"Orders processed: "
                f"{orders_processed:,}/"
                f"{total_orders:,} | "
                f"Items inserted: "
                f"{rows_inserted:,} | "
                f"Checkpoint: "
                f"{last_order_id:,}"
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
        print("ORDER ITEM GENERATION COMPLETE")
        print("====================================")

        print(
            "Orders processed:",
            f"{orders_processed:,}"
        )

        print(
            "Rows generated:",
            f"{rows_generated:,}"
        )

        print(
            "Rows inserted:",
            f"{rows_inserted:,}"
        )

        print(
            "Elapsed seconds:",
            f"{elapsed:.2f}"
        )

        print(
            "Rows/sec:",
            f"{rows_per_second:,.0f}"
        )

        print(
            "Final checkpoint:",
            f"{last_order_id:,}"
        )

    except Exception:

        conn.rollback()

        print(
            "\nOrder item generation failed."
        )

        print(
            "Database transaction rolled back "
            "where applicable."
        )

        raise

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":

    generate_order_items(
        total_orders=4_890_000,
        order_batch_size=5_000,
        insert_batch_size=5_000,
        seed=400,
        start_order_id=None
    )
