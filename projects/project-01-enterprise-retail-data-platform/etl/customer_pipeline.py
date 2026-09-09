"""Customer incremental pipeline orchestration."""

# TODO: add the validated local implementation.
from config.database import get_connection

from etl.customer_extractor import (
    extract_customers,
    update_customer_watermark
)

from etl.customer_loader import (
    upsert_customers
)


PIPELINE_NAME = "customer_incremental_pipeline"


def start_pipeline_run():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO dbo.etl_pipeline_run
            (
                pipeline_name,
                run_start_time,
                status,
                rows_read,
                rows_inserted,
                rows_updated,
                rows_deleted
            )
            OUTPUT INSERTED.run_id
            VALUES
            (
                ?,
                SYSDATETIME(),
                'RUNNING',
                0,
                0,
                0,
                0
            )
            """,
            PIPELINE_NAME
        )

        run_id = cursor.fetchone()[0]

        conn.commit()

        return run_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def complete_pipeline_run(
    run_id,
    status,
    rows_read=0,
    rows_inserted=0,
    rows_updated=0,
    rows_deleted=0,
    error_message=None
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE dbo.etl_pipeline_run
            SET
                run_end_time = SYSDATETIME(),
                status = ?,
                rows_read = ?,
                rows_inserted = ?,
                rows_updated = ?,
                rows_deleted = ?,
                error_message = ?
            WHERE run_id = ?
            """,
            status,
            rows_read,
            rows_inserted,
            rows_updated,
            rows_deleted,
            error_message,
            run_id
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def log_pipeline_error(
    run_id,
    source_table,
    error_type,
    error_message
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO dbo.etl_error_log
            (
                run_id,
                source_table,
                error_type,
                error_message,
                error_time
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                SYSDATETIME()
            )
            """,
            run_id,
            source_table,
            error_type,
            error_message
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def main():

    run_id = start_pipeline_run()

    print("====================================")
    print("Customer Pipeline Started")
    print("Run ID:", run_id)
    print("====================================")

    rows = []

    try:

        # -----------------------------------------
        # 1. Extract
        # -----------------------------------------

        print("\nSTEP 1: Extraction")

        rows = extract_customers()

        rows_read = len(rows)

        if not rows:

            print("No new records.")

            complete_pipeline_run(
                run_id=run_id,
                status="SUCCESS",
                rows_read=0
            )

            print("\nPipeline completed successfully.")
            return

        # -----------------------------------------
        # 2. Load target
        # -----------------------------------------

        print("\nSTEP 2: Target Load")

        load_result = upsert_customers(rows)

        rows_inserted = load_result["rows_inserted"]
        rows_updated = load_result["rows_updated"]

        # -----------------------------------------
        # 3. Update watermark
        # -----------------------------------------

        print("\nSTEP 3: Watermark Update")

        last_row = rows[-1]

        update_customer_watermark(
            last_row.updated_at,
            last_row.customer_id
        )

        # -----------------------------------------
        # 4. Mark pipeline SUCCESS
        # -----------------------------------------

        print("\nSTEP 4: Pipeline Success")

        complete_pipeline_run(
            run_id=run_id,
            status="SUCCESS",
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
            rows_deleted=0
        )

        print("\n====================================")
        print("Pipeline completed successfully.")
        print("Run ID:", run_id)
        print("Rows read:", rows_read)
        print("Rows inserted:", rows_inserted)
        print("Rows updated:", rows_updated)
        print("====================================")

    except Exception as exc:

        error_message = str(exc)

        print("\n====================================")
        print("Pipeline FAILED")
        print("Error:", error_message)
        print("====================================")

        log_pipeline_error(
            run_id=run_id,
            source_table="customers",
            error_type=type(exc).__name__,
            error_message=error_message
        )

        complete_pipeline_run(
            run_id=run_id,
            status="FAILED",
            rows_read=len(rows),
            error_message=error_message
        )

        raise


if __name__ == "__main__":
    main()
