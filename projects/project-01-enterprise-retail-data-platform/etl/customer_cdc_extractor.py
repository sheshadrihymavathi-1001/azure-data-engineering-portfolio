"""SQL Server CDC extractor using an LSN checkpoint."""

# TODO: add the validated local implementation.
from config.database import get_connection


SOURCE_TABLE = "customers"
CAPTURE_INSTANCE = "dbo_customers"


def get_cdc_checkpoint():
    """
    Get the last successfully processed CDC LSN.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT last_processed_lsn
            FROM dbo.etl_cdc_checkpoint
            WHERE source_table = ?
        """, SOURCE_TABLE)

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"No CDC checkpoint configuration found "
                f"for {SOURCE_TABLE}"
            )

        return row[0]

    finally:
        cursor.close()
        conn.close()


def get_cdc_min_lsn():
    """
    Get the minimum valid LSN currently available
    for this CDC capture instance.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sys.fn_cdc_get_min_lsn(?)
        """, CAPTURE_INSTANCE)

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                "Unable to retrieve CDC minimum LSN"
            )

        return row[0]

    finally:
        cursor.close()
        conn.close()


def get_cdc_max_lsn():
    """
    Get the current maximum CDC LSN available
    in the database.

    This is captured once at the beginning of the
    extraction and becomes the upper boundary for
    this pipeline run.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sys.fn_cdc_get_max_lsn()
        """)

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                "Unable to retrieve CDC maximum LSN"
            )

        return row[0]

    finally:
        cursor.close()
        conn.close()


def get_next_from_lsn(last_processed_lsn):
    """
    Convert the previously processed LSN into the
    next starting boundary.

    CDC extraction ranges are inclusive, so we advance
    the previous checkpoint before using it as FROM LSN.
    """

    if last_processed_lsn is None:
        return get_cdc_min_lsn()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sys.fn_cdc_increment_lsn(?)
        """, last_processed_lsn)

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                "Unable to calculate next CDC starting LSN"
            )

        return row[0]

    finally:
        cursor.close()
        conn.close()


def extract_customer_changes():
    """
    Extract customer CDC changes within a fixed LSN boundary.

    Returns:

        {
            "from_lsn": ...,
            "to_lsn": ...,
            "rows": [...]
        }

    The TO LSN is captured once at the beginning of
    this extraction. Changes arriving after that boundary
    belong to the next pipeline run.
    """

    last_processed_lsn = get_cdc_checkpoint()

    from_lsn = get_next_from_lsn(
        last_processed_lsn
    )

    to_lsn = get_cdc_max_lsn()

    print(
        "Last processed LSN:",
        last_processed_lsn
    )

    print(
        "From LSN:",
        from_lsn
    )

    print(
        "To LSN:",
        to_lsn
    )

    # Nothing to process
    if from_lsn > to_lsn:

        print("No new CDC changes.")

        return {
            "from_lsn": from_lsn,
            "to_lsn": to_lsn,
            "rows": []
        }

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                __$start_lsn,
                __$seqval,
                __$operation,
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

            FROM cdc.fn_cdc_get_all_changes_dbo_customers
            (
                ?,
                ?,
                'all'
            )

            ORDER BY
                __$start_lsn,
                __$seqval
        """,
            from_lsn,
            to_lsn
        )

        rows = cursor.fetchall()

        print(
            "CDC records extracted:",
            len(rows)
        )

        for row in rows:

            print(
                "LSN:", row[0],
                "| Operation:", row[2],
                "| Customer:", row[3]
            )

        return {
            "from_lsn": from_lsn,
            "to_lsn": to_lsn,
            "rows": rows
        }

    finally:
        cursor.close()
        conn.close()


def update_cdc_checkpoint(last_processed_lsn):
    """
    Advance the CDC checkpoint only after the target
    transaction has completed successfully.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE dbo.etl_cdc_checkpoint
            SET
                last_processed_lsn = ?,
                updated_at = SYSDATETIME()
            WHERE source_table = ?
        """,
            last_processed_lsn,
            SOURCE_TABLE
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"CDC checkpoint configuration not found "
                f"for {SOURCE_TABLE}"
            )

        conn.commit()

        print(
            "CDC checkpoint updated to:",
            last_processed_lsn
        )

    except Exception:

        conn.rollback()

        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":

    result = extract_customer_changes()

    print("\n====================================")
    print("CDC EXTRACTION RESULT")
    print("====================================")

    print(
        "From LSN:",
        result["from_lsn"]
    )

    print(
        "To LSN:",
        result["to_lsn"]
    )

    print(
        "Rows extracted:",
        len(result["rows"])
    )
