"""SQL Server connectivity smoke test for Project 01."""

# TODO: add the validated local connectivity test implementation.
from config.database import get_connection


try:
    conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            DB_NAME() AS database_name,
            @@VERSION AS sql_version
    """)

    row = cursor.fetchone()

    print("Connection successful")
    print("Database:", row.database_name)
    print("SQL Server:", row.sql_version.splitlines()[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("Connection failed")
    print("Error:", e)
