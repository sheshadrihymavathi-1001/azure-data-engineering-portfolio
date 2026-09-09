"""Database configuration placeholder for Project 01.

Do not commit passwords, access tokens, or production connection strings.
The validated local implementation can be added here with environment-based
configuration.
"""

# TODO: add the validated local database connection implementation.

import pyodbc

SERVER = "localhost,14330"
DATABASE = "ContosoRetailDB"
DRIVER = "ODBC Driver 18 for SQL Server"


def get_connection():
    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)
