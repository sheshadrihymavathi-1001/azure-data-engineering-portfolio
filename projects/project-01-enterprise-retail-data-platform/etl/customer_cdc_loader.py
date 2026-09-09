"""Customer CDC target loader with replay-safe operations."""

# TODO: add the validated local implementation.
from config.database import get_connection


def apply_customer_cdc_changes(rows):
    """
    Apply CDC changes to customer_cdc_target.

    CDC operations:
        1 = DELETE
        2 = INSERT
        4 = UPDATE after-image

    Returns:
        rows_read
        rows_inserted
        rows_updated
        rows_deleted
        idempotent_replays
        rows_noop
    """

    if not rows:

        print("No CDC changes to apply.")

        return {
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_updated": 0,
            "rows_deleted": 0,
            "idempotent_replays": 0,
            "rows_noop": 0
        }

    conn = get_connection()

    rows_inserted = 0
    rows_updated = 0
    rows_deleted = 0
    idempotent_replays = 0
    rows_noop = 0

    try:

        cursor = conn.cursor()

        for row in rows:

            operation = row[2]
            customer_id = row[3]

            # ==================================================
            # INSERT
            # ==================================================

            if operation == 2:

                cursor.execute(
                    """
                    SELECT 1
                    FROM dbo.customer_cdc_target
                    WHERE customer_id = ?
                    """,
                    customer_id
                )

                exists = cursor.fetchone() is not None

                if exists:

                    # --------------------------------------------------
                    # Idempotent replay
                    #
                    # The same INSERT event was already successfully
                    # applied during an earlier pipeline attempt.
                    #
                    # Do not count this as a business UPDATE.
                    # --------------------------------------------------

                    idempotent_replays += 1

                    print(
                        "IDEMPOTENT REPLAY | Customer:",
                        customer_id
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO dbo.customer_cdc_target
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
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME()
                        )
                        """,
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        row[9],
                        row[10],
                        row[11],
                        row[12],
                        row[13]
                    )

                    rows_inserted += 1

                    print(
                        "INSERT | Customer:",
                        customer_id
                    )

            # ==================================================
            # UPDATE
            # ==================================================

            elif operation == 4:

                cursor.execute(
                    """
                    UPDATE dbo.customer_cdc_target
                    SET
                        first_name = ?,
                        last_name = ?,
                        email = ?,
                        phone = ?,
                        city = ?,
                        state = ?,
                        country = ?,
                        customer_status = ?,
                        created_at = ?,
                        updated_at = ?,
                        loaded_at = SYSDATETIME()
                    WHERE customer_id = ?
                    """,
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12],
                    row[13],
                    customer_id
                )

                if cursor.rowcount == 0:

                    raise ValueError(
                        f"Customer {customer_id} does not exist "
                        "in CDC target for UPDATE"
                    )

                rows_updated += 1

                print(
                    "UPDATE | Customer:",
                    customer_id
                )

            # ==================================================
            # DELETE
            # ==================================================

            elif operation == 1:

                cursor.execute(
                    """
                    DELETE FROM dbo.customer_cdc_target
                    WHERE customer_id = ?
                    """,
                    customer_id
                )

                if cursor.rowcount > 0:

                    rows_deleted += 1

                    print(
                        "DELETE | Customer:",
                        customer_id
                    )

                else:

                    # --------------------------------------------------
                    # Delete replay
                    #
                    # The record is already absent from the target.
                    # Nothing needs to be done.
                    # --------------------------------------------------

                    rows_noop += 1

                    print(
                        "DELETE REPLAY → NO-OP | Customer:",
                        customer_id
                    )

            else:

                raise ValueError(
                    f"Unsupported CDC operation: {operation}"
                )

        conn.commit()

        print("\nCDC target load successful.")
        print("Rows read:", len(rows))
        print("Rows inserted:", rows_inserted)
        print("Rows updated:", rows_updated)
        print("Rows deleted:", rows_deleted)
        print("Idempotent replays:", idempotent_replays)
        print("Rows no-op:", rows_noop)

        return {
            "rows_read": len(rows),
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
            "rows_deleted": rows_deleted,
            "idempotent_replays": idempotent_replays,
            "rows_noop": rows_noop
        }

    except Exception:

        conn.rollback()

        print(
            "CDC target load failed. "
            "Transaction rolled back."
        )

        raise

    finally:

        cursor.close()
        conn.close()
