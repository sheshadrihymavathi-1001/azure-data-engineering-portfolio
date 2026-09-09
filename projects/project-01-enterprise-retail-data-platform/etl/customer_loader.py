"""Customer incremental target loader."""

# TODO: add the validated local implementation.
from config.database import get_connection


def upsert_customers(rows):
    """
    Idempotently load customer records into customer_target.

    Returns:
        {
            "rows_read": int,
            "rows_inserted": int,
            "rows_updated": int
        }
    """

    if not rows:
        print("No records to load.")

        return {
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_updated": 0
        }

    conn = get_connection()

    rows_inserted = 0
    rows_updated = 0

    try:
        cursor = conn.cursor()

        for row in rows:

            # Check whether the customer already exists
            cursor.execute(
                """
                SELECT 1
                FROM dbo.customer_target
                WHERE customer_id = ?
                """,
                row.customer_id
            )

            exists = cursor.fetchone() is not None

            cursor.execute(
                """
                MERGE dbo.customer_target AS target
                USING
                (
                    SELECT
                        ? AS customer_id,
                        ? AS first_name,
                        ? AS last_name,
                        ? AS email,
                        ? AS phone,
                        ? AS city,
                        ? AS state,
                        ? AS country,
                        ? AS customer_status,
                        ? AS created_at,
                        ? AS updated_at
                ) AS source
                ON target.customer_id = source.customer_id

                WHEN MATCHED THEN
                    UPDATE SET
                        first_name = source.first_name,
                        last_name = source.last_name,
                        email = source.email,
                        phone = source.phone,
                        city = source.city,
                        state = source.state,
                        country = source.country,
                        customer_status = source.customer_status,
                        created_at = source.created_at,
                        updated_at = source.updated_at,
                        loaded_at = SYSDATETIME()

                WHEN NOT MATCHED THEN
                    INSERT
                    (
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
                        updated_at,
                        loaded_at
                    )
                    VALUES
                    (
                        source.customer_id,
                        source.first_name,
                        source.last_name,
                        source.email,
                        source.phone,
                        source.city,
                        source.state,
                        source.country,
                        source.customer_status,
                        source.created_at,
                        source.updated_at,
                        SYSDATETIME()
                    );
                """,
                (
                    row.customer_id,
                    row.first_name,
                    row.last_name,
                    row.email,
                    row.phone,
                    row.city,
                    row.state,
                    row.country,
                    row.customer_status,
                    row.created_at,
                    row.updated_at,
                )
            )

            if exists:
                rows_updated += 1
            else:
                rows_inserted += 1

        conn.commit()

        print("Target load successful.")
        print("Rows read:", len(rows))
        print("Rows inserted:", rows_inserted)
        print("Rows updated:", rows_updated)

        return {
            "rows_read": len(rows),
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated
        }

    except Exception:
        conn.rollback()

        print("Target load failed. Transaction rolled back.")

        raise

    finally:
        cursor.close()
        conn.close()
