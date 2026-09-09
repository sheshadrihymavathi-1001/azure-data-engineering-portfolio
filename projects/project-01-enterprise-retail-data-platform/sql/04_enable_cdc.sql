/*
Project 01 - Change Data Capture Setup

Purpose:
    Enable SQL Server CDC for the customers table.

The project uses CDC to demonstrate:

    INSERT
    UPDATE
    DELETE

and LSN-based checkpoint recovery.

Prerequisite:
    SQL Server Agent must be running.
*/

USE ContosoRetailDB;
GO


/* ============================================================
   1. ENABLE CDC AT DATABASE LEVEL
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.databases
    WHERE name = DB_NAME()
      AND is_cdc_enabled = 1
)
BEGIN
    EXEC sys.sp_cdc_enable_db;

    PRINT 'CDC enabled for database.';
END
ELSE
BEGIN
    PRINT 'CDC already enabled for database.';
END
GO


/* ============================================================
   2. ENABLE CDC FOR CUSTOMERS
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1
    FROM cdc.change_tables
    WHERE capture_instance = 'dbo_customers'
)
BEGIN
    EXEC sys.sp_cdc_enable_table
        @source_schema = 'dbo',
        @source_name = 'customers',
        @role_name = NULL,
        @capture_instance = 'dbo_customers',
        @supports_net_changes = 1;

    PRINT 'CDC enabled for dbo.customers.';
END
ELSE
BEGIN
    PRINT 'CDC already enabled for dbo.customers.';
END
GO


/* ============================================================
   3. VERIFY CDC CONFIGURATION
   ============================================================ */

SELECT
    capture_instance,
    source_schema,
    source_name,
    start_lsn,
    supports_net_changes
FROM cdc.change_tables
WHERE source_schema = 'dbo'
  AND source_name = 'customers';
GO


/* ============================================================
   4. VERIFY CDC CHANGE TABLE
   ============================================================ */

SELECT
    name
FROM sys.tables
WHERE schema_id = SCHEMA_ID('cdc')
  AND name LIKE 'dbo_customers_CT';
GO


/* ============================================================
   5. VERIFY CDC DATABASE STATUS
   ============================================================ */

SELECT
    name AS database_name,
    is_cdc_enabled
FROM sys.databases
WHERE name = DB_NAME();
GO
