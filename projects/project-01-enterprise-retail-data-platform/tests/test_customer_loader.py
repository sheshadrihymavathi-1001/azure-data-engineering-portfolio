"""Incremental customer loader scenarios.

TODO: add the validated local test implementation used during Project 01.
"""
from config.database import get_connection
from etl.customer_loader import upsert_customers


def get_customer_19():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                customer_id,
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
            FROM dbo.customers
            WHERE customer_id = 19
            """
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        conn.close()


def get_target_count():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM dbo.customer_target
            WHERE customer_id = 19
            """
        )

        return cursor.fetchone()[0]

    finally:
        cursor.close()
        conn.close()


def main():

    row = get_customer_19()

    if row is None:
        raise RuntimeError("Customer 19 not found in source.")

    print("Before load:")
    print("Target count:", get_target_count())

    # First load
    print("\n--- First load ---")
    upsert_customers([row])

    print("Target count:", get_target_count())

    # Replay the exact same record
    print("\n--- Second load: replay same record ---")
    upsert_customers([row])

    print("Target count:", get_target_count())


if __name__ == "__main__":
    main()
