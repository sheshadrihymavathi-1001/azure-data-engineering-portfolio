/*
Project 01 - ETL Control Tables

Purpose:
    Create operational control tables used for:

    - Pipeline auditing
    - Incremental loading
    - Error tracking
    - Idempotent replay tracking
    - CDC checkpoint management
*/

USE ContosoRetailDB;
GO


/* ============================================================
   1. ETL WATERMARK
   ============================================================ */

IF OBJECT_ID('dbo.etl_watermark', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.etl_watermark
    (
        watermark_id INT IDENTITY(1,1)
            CONSTRAINT PK_etl_watermark PRIMARY KEY,

        source_table VARCHAR(100) NOT NULL,

        watermark_column VARCHAR(100) NOT NULL,

        last_watermark_value DATETIME2(3) NULL,

        last_primary_key_value BIGINT NULL,

        updated_at DATETIME2(3) NOT NULL
            CONSTRAINT DF_etl_watermark_updated_at
            DEFAULT SYSDATETIME(),

        CONSTRAINT UQ_etl_watermark_source
            UNIQUE (source_table)
    );

    PRINT 'Created dbo.etl_watermark';
END
GO


/* ============================================================
   Initialize incremental-load watermark configuration
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_watermark
    WHERE source_table = 'customers'
)
BEGIN
    INSERT INTO dbo.etl_watermark
    (
        source_table,
        watermark_column
    )
    VALUES
    (
        'customers',
        'updated_at'
    );
END
GO


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_watermark
    WHERE source_table = 'orders'
)
BEGIN
    INSERT INTO dbo.etl_watermark
    (
        source_table,
        watermark_column
    )
    VALUES
    (
        'orders',
        'updated_at'
    );
END
GO


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_watermark
    WHERE source_table = 'order_items'
)
BEGIN
    INSERT INTO dbo.etl_watermark
    (
        source_table,
        watermark_column
    )
    VALUES
    (
        'order_items',
        'updated_at'
    );
END
GO


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_watermark
    WHERE source_table = 'payments'
)
BEGIN
    INSERT INTO dbo.etl_watermark
    (
        source_table,
        watermark_column
    )
    VALUES
    (
        'payments',
        'updated_at'
    );
END
GO


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_watermark
    WHERE source_table = 'inventory'
)
BEGIN
    INSERT INTO dbo.etl_watermark
    (
        source_table,
        watermark_column
    )
    VALUES
    (
        'inventory',
        'updated_at'
    );
END
GO


IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_watermark
    WHERE source_table = 'order_status_history'
)
BEGIN
    INSERT INTO dbo.etl_watermark
    (
        source_table,
        watermark_column
    )
    VALUES
    (
        'order_status_history',
        'changed_at'
    );
END
GO


/* ============================================================
   2. PIPELINE RUN AUDIT
   ============================================================ */

IF OBJECT_ID('dbo.etl_pipeline_run', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.etl_pipeline_run
    (
        run_id BIGINT IDENTITY(1,1)
            CONSTRAINT PK_etl_pipeline_run PRIMARY KEY,

        pipeline_name VARCHAR(200) NOT NULL,

        run_start_time DATETIME2(3) NOT NULL
            CONSTRAINT DF_etl_pipeline_run_start
            DEFAULT SYSDATETIME(),

        run_end_time DATETIME2(3) NULL,

        status VARCHAR(30) NOT NULL,

        rows_read BIGINT NOT NULL
            CONSTRAINT DF_etl_pipeline_run_rows_read
            DEFAULT 0,

        rows_inserted BIGINT NOT NULL
            CONSTRAINT DF_etl_pipeline_run_rows_inserted
            DEFAULT 0,

        rows_updated BIGINT NOT NULL
            CONSTRAINT DF_etl_pipeline_run_rows_updated
            DEFAULT 0,

        rows_deleted BIGINT NOT NULL
            CONSTRAINT DF_etl_pipeline_run_rows_deleted
            DEFAULT 0,

        idempotent_replays BIGINT NOT NULL
            CONSTRAINT DF_etl_pipeline_run_replays
            DEFAULT 0,

        rows_noop BIGINT NOT NULL
            CONSTRAINT DF_etl_pipeline_run_noop
            DEFAULT 0,

        error_message NVARCHAR(4000) NULL
    );

    PRINT 'Created dbo.etl_pipeline_run';
END
GO


/* ============================================================
   3. ETL ERROR LOG
   ============================================================ */

IF OBJECT_ID('dbo.etl_error_log', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.etl_error_log
    (
        error_id BIGINT IDENTITY(1,1)
            CONSTRAINT PK_etl_error_log PRIMARY KEY,

        run_id BIGINT NULL,

        pipeline_name VARCHAR(200) NOT NULL,

        source_table VARCHAR(100) NULL,

        error_time DATETIME2(3) NOT NULL
            CONSTRAINT DF_etl_error_log_error_time
            DEFAULT SYSDATETIME(),

        error_type VARCHAR(100) NULL,

        error_message NVARCHAR(4000) NOT NULL,

        error_details NVARCHAR(MAX) NULL
    );

    PRINT 'Created dbo.etl_error_log';
END
GO


/* ============================================================
   4. CDC CHECKPOINT
   ============================================================ */

IF OBJECT_ID('dbo.etl_cdc_checkpoint', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.etl_cdc_checkpoint
    (
        checkpoint_id INT IDENTITY(1,1)
            CONSTRAINT PK_etl_cdc_checkpoint PRIMARY KEY,

        source_table VARCHAR(100) NOT NULL,

        capture_instance VARCHAR(100) NOT NULL,

        last_processed_lsn BINARY(10) NULL,

        updated_at DATETIME2(3) NOT NULL
            CONSTRAINT DF_etl_cdc_checkpoint_updated_at
            DEFAULT SYSDATETIME(),

        CONSTRAINT UQ_etl_cdc_checkpoint_source
            UNIQUE (source_table)
    );

    PRINT 'Created dbo.etl_cdc_checkpoint';
END
GO


/* ============================================================
   5. INITIAL CDC CHECKPOINT
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1
    FROM dbo.etl_cdc_checkpoint
    WHERE source_table = 'customers'
)
BEGIN
    INSERT INTO dbo.etl_cdc_checkpoint
    (
        source_table,
        capture_instance,
        last_processed_lsn
    )
    VALUES
    (
        'customers',
        'dbo_customers',
        NULL
    );
END
GO


/* ============================================================
   6. DISPLAY CONTROL TABLE CONFIGURATION
   ============================================================ */

SELECT
    source_table,
    watermark_column,
    last_watermark_value,
    last_primary_key_value,
    updated_at
FROM dbo.etl_watermark
ORDER BY source_table;
GO


SELECT
    source_table,
    capture_instance,
    last_processed_lsn,
    updated_at
FROM dbo.etl_cdc_checkpoint;
GO
