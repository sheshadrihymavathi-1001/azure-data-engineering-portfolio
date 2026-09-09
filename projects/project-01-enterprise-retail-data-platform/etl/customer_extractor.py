"""Customer incremental extractor using a composite watermark."""

# TODO: add the validated local implementation.
from config.database import get_connection


def get_customer_watermark():
    """
    Read the last successfully processed watermark
    for the customers table.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                last_watermark_value,
                last_primary_key_value
            FROM dbo.etl_watermark
            WHERE source_table = ?
            """,
            "customers"
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                "No watermark configuration found for customers"
            )

        return row.last_watermark_value, row.last_primary_key_value

    finally:
        cursor.close()
        conn.close()


def extract_customers():
    """
    Extract customers after the stored composite watermark.
    """

    last_watermark, last_customer_id = get_customer_watermark()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        if last_watermark is None:

            print("Initial load detected.")
            print("Extracting all customers.")

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
                ORDER BY
                    updated_at,
                    customer_id
                """
            )

        else:

            print("Incremental load detected.")
            print("Last watermark:", last_watermark)
            print("Last customer ID:", last_customer_id)

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
                WHERE
                    updated_at > ?
                    OR (
                        updated_at = ?
                        AND customer_id > ?
                    )
                ORDER BY
                    updated_at,
                    customer_id
                """,
                last_watermark,
                last_watermark,
                last_customer_id
            )

        rows = cursor.fetchall()

        print("Records extracted:", len(rows))

        for row in rows:
            print(
                row.customer_id,
                row.first_name,
                row.last_name,
                row.updated_at
            )

        return rows

    finally:
        cursor.close()
        conn.close()


def update_customer_watermark(
    last_watermark,
    last_customer_id
):
    """
    Update the customers watermark after
    successful target processing.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE dbo.etl_watermark
            SET
                last_watermark_value = ?,
                last_primary_key_value = ?,
                updated_at = SYSDATETIME()
            WHERE source_table = ?
            """,
            last_watermark,
            last_customer_id,
            "customers"
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "No watermark row found for customers"
            )

        conn.commit()

        print("Watermark updated successfully")
        print("Last watermark:", last_watermark)
        print("Last customer ID:", last_customer_id)

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":

    rows = extract_customers()

    if rows:

        last_row = rows[-1]

        print("\nExtraction completed.")
        print("Last extracted customer:", last_row.customer_id)

    else:

        print("No new records. Watermark not changed.")
