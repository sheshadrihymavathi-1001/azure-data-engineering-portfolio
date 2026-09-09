"""CDC INSERT/UPDATE/DELETE and replay scenarios.

TODO: add the validated local test implementation used during Project 01.
"""
from etl.customer_cdc_extractor import extract_customer_changes
from etl.customer_cdc_loader import apply_customer_cdc_changes


def main():

    print("====================================")
    print("CDC LOAD TEST")
    print("====================================")


    # ==================================================
    # STEP 1: EXTRACT CDC CHANGES
    # ==================================================

    print("\nSTEP 1: Extract CDC changes")

    extraction_result = extract_customer_changes()

    from_lsn = extraction_result["from_lsn"]
    to_lsn = extraction_result["to_lsn"]
    rows = extraction_result["rows"]

    print("\nExtraction result:")
    print("From LSN:", from_lsn)
    print("To LSN:", to_lsn)
    print("Rows extracted:", len(rows))


    if not rows:

        print("\nNo CDC changes found.")

        return


    # ==================================================
    # STEP 2: APPLY CDC CHANGES
    # ==================================================

    print("\nSTEP 2: Apply CDC changes")

    result = apply_customer_cdc_changes(rows)


    # ==================================================
    # FINAL RESULT
    # ==================================================

    print("\n====================================")
    print("CDC LOAD RESULT")
    print("====================================")

    print("Rows read:", result["rows_read"])
    print("Rows inserted:", result["rows_inserted"])
    print("Rows updated:", result["rows_updated"])
    print("Rows deleted:", result["rows_deleted"])
    print("Idempotent replays:", result["idempotent_replays"])
    print("Rows no-op:", result["rows_noop"])


if __name__ == "__main__":
    main()
