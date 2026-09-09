"""Customer DELETE and replay/no-op scenarios.

TODO: add the validated local test implementation used during Project 01.
"""
from etl.customer_cdc_loader import apply_customer_cdc_changes

from config.database import get_connection


DELETE_LSN = bytes.fromhex(
    "00000039000001780007"
)


def get_delete_event():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
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
            WHERE __$operation = 1
              AND customer_id = 27
            """,
            DELETE_LSN,
            DELETE_LSN
        )

        rows = cursor.fetchall()

        return rows

    finally:
        cursor.close()
        conn.close()


def main():

    print("====================================")
    print("CDC DELETE TEST")
    print("====================================")

    print("\nSTEP 1: Get DELETE event")

    rows = get_delete_event()

    print("DELETE events found:", len(rows))

    for row in rows:
        print(
            "LSN:", row[0],
            "| Operation:", row[2],
            "| Customer:", row[3]
        )

    if not rows:
        print("No DELETE event found.")
        return

    print("\nSTEP 2: Apply DELETE")

    result = apply_customer_cdc_changes(rows)

    print("\n====================================")
    print("DELETE TEST RESULT")
    print("====================================")

    print("Rows read:", result["rows_read"])
    print("Rows inserted:", result["rows_inserted"])
    print("Rows updated:", result["rows_updated"])
    print("Rows deleted:", result["rows_deleted"])
    print("Idempotent replays:", result["idempotent_replays"])
    print("Rows no-op:", result["rows_noop"])


if __name__ == "__main__":
    main()
