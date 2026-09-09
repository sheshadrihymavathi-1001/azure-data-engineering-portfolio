"""Customer CDC pipeline orchestration and checkpoint handling."""

# TODO: add the validated local implementation.
from config.database import get_connection

from etl.customer_cdc_extractor import (
    extract_customer_changes,
    update_cdc_checkpoint
)

from etl.customer_cdc_loader import (
    apply_customer_cdc_changes
)


SIMULATE_CHECKPOINT_FAILURE = False

PIPELINE_NAME = "customer_cdc_pipeline"
SOURCE_TABLE = "customers"


# ======================================================
# START PIPELINE RUN
# ======================================================

def start_pipeline_run():
    """
    Create a new pipeline execution record.

    Returns:
        run_id: ID of the newly created pipeline run.
    """

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


# ======================================================
# COMPLETE PIPELINE RUN
# ======================================================

def complete_pipeline_run(
    run_id,
    status,
    rows_read=0,
    rows_inserted=0,
    rows_updated=0,
    rows_deleted=0,
    idempotent_replays=0,
    rows_noop=0,
    error_message=None
):
    """
    Update the pipeline audit record after execution.
    """

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
                idempotent_replays = ?,
                rows_noop = ?,
                error_message = ?
            WHERE run_id = ?
            """,
            status,
            rows_read,
            rows_inserted,
            rows_updated,
            rows_deleted,
            idempotent_replays,
            rows_noop,
            error_message,
            run_id
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Pipeline run {run_id} was not found"
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ======================================================
# ERROR LOGGING
# ======================================================

def log_pipeline_error(
    run_id,
    source_table,
    error_type,
    error_message
):
    """
    Write detailed error information
    to the ETL error log.
    """

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


# ======================================================
# MAIN PIPELINE
# ======================================================

def main():

    run_id = None

    rows_read = 0
    rows_inserted = 0
    rows_updated = 0
    rows_deleted = 0
    idempotent_replays = 0
    rows_noop = 0

    try:

        # ==================================================
        # STEP 1: START PIPELINE RUN
        # ==================================================

        run_id = start_pipeline_run()

        print("====================================")
        print("CUSTOMER CDC PIPELINE")
        print("====================================")

        print("Pipeline run ID:", run_id)


        # ==================================================
        # STEP 2: CDC EXTRACTION
        # ==================================================

        print("\nSTEP 1: CDC EXTRACTION")

        extraction_result = extract_customer_changes()

        from_lsn = extraction_result["from_lsn"]
        to_lsn = extraction_result["to_lsn"]
        rows = extraction_result["rows"]

        rows_read = len(rows)

        print("\nExtraction completed.")
        print("From LSN:", from_lsn)
        print("To LSN:", to_lsn)
        print("Rows read:", rows_read)


        # ==================================================
        # STEP 3: TARGET LOAD
        # ==================================================

        print("\nSTEP 2: TARGET LOAD")

        load_result = apply_customer_cdc_changes(rows)

        rows_inserted = load_result["rows_inserted"]
        rows_updated = load_result["rows_updated"]
        rows_deleted = load_result["rows_deleted"]
        idempotent_replays = load_result["idempotent_replays"]
        rows_noop = load_result["rows_noop"]

        print("\nTarget load completed.")

        print("Rows inserted:", rows_inserted)
        print("Rows updated:", rows_updated)
        print("Rows deleted:", rows_deleted)
        print("Idempotent replays:", idempotent_replays)
        print("Rows no-op:", rows_noop)


        # ==================================================
        # STEP 4: CHECKPOINT UPDATE
        # ==================================================

        print("\nSTEP 3: CHECKPOINT UPDATE")

        if SIMULATE_CHECKPOINT_FAILURE:

            print(
                "SIMULATED FAILURE: "
                "Checkpoint update intentionally skipped."
            )

            raise RuntimeError(
                "Simulated failure after successful target commit "
                "and before checkpoint update."
            )

        update_cdc_checkpoint(to_lsn)

        print(
            "Checkpoint successfully advanced to:",
            to_lsn
        )


        # ==================================================
        # STEP 5: MARK PIPELINE SUCCESS
        # ==================================================

        complete_pipeline_run(
            run_id=run_id,
            status="SUCCESS",
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
            rows_deleted=rows_deleted,
            idempotent_replays=idempotent_replays,
            rows_noop=rows_noop
        )


        # ==================================================
        # FINAL SUMMARY
        # ==================================================

        print("\n====================================")
        print("PIPELINE SUCCESS")
        print("====================================")

        print("Run ID:", run_id)
        print("Rows read:", rows_read)
        print("Rows inserted:", rows_inserted)
        print("Rows updated:", rows_updated)
        print("Rows deleted:", rows_deleted)
        print("Idempotent replays:", idempotent_replays)
        print("Rows no-op:", rows_noop)
        print("Checkpoint:", to_lsn)


    except Exception as exc:

        print("\n====================================")
        print("PIPELINE FAILED")
        print("====================================")

        print("Run ID:", run_id)
        print("Error:", exc)


        if run_id is not None:

            # ----------------------------------------------
            # Log detailed error
            # ----------------------------------------------

            try:

                log_pipeline_error(
                    run_id=run_id,
                    source_table=SOURCE_TABLE,
                    error_type=type(exc).__name__,
                    error_message=str(exc)
                )

            except Exception as log_exc:

                print(
                    "ERROR: Failed to write error log:",
                    log_exc
                )


            # ----------------------------------------------
            # Mark pipeline as FAILED
            # ----------------------------------------------

            try:

                complete_pipeline_run(
                    run_id=run_id,
                    status="FAILED",
                    rows_read=rows_read,
                    rows_inserted=rows_inserted,
                    rows_updated=rows_updated,
                    rows_deleted=rows_deleted,
                    idempotent_replays=idempotent_replays,
                    rows_noop=rows_noop,
                    error_message=str(exc)
                )

            except Exception as audit_exc:

                print(
                    "ERROR: Failed to update pipeline audit:",
                    audit_exc
                )

        raise


# ======================================================
# SCRIPT ENTRY POINT
# ======================================================

if __name__ == "__main__":
    main()
