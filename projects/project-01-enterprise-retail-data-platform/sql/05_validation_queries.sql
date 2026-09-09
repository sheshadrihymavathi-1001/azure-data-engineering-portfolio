/*
Project 01 - Data Quality and Reconciliation Validation

Purpose:
    Validate source-system integrity and business reconciliation.

Validation categories:

    1. Row counts
    2. Referential integrity
    3. Duplicate detection
    4. Invalid values
    5. Order-item reconciliation
    6. Payment reconciliation
    7. Inventory integrity
    8. Status-history reconciliation
    9. Control-plane state
*/

USE ContosoRetailDB;
GO


/* ============================================================
   1. ROW COUNTS
   ============================================================ */

SELECT
    'customers' AS table_name,
    COUNT_BIG(*) AS row_count
FROM dbo.customers

UNION ALL

SELECT
    'products',
    COUNT_BIG(*)
FROM dbo.products

UNION ALL

SELECT
    'stores',
    COUNT_BIG(*)
FROM dbo.stores

UNION ALL

SELECT
    'orders',
    COUNT_BIG(*)
FROM dbo.orders

UNION ALL

SELECT
    'order_items',
    COUNT_BIG(*)
FROM dbo.order_items

UNION ALL

SELECT
    'payments',
    COUNT_BIG(*)
FROM dbo.payments

UNION ALL

SELECT
    'inventory',
    COUNT_BIG(*)
FROM dbo.inventory

UNION ALL

SELECT
    'order_status_history',
    COUNT_BIG(*)
FROM dbo.order_status_history;
GO


/* ============================================================
   2. ORPHAN ORDERS
   ============================================================ */

SELECT COUNT_BIG(*) AS orphan_orders
FROM dbo.orders o
LEFT JOIN dbo.customers c
    ON o.customer_id = c.customer_id
LEFT JOIN dbo.stores s
    ON o.store_id = s.store_id
WHERE c.customer_id IS NULL
   OR s.store_id IS NULL;
GO


/* ============================================================
   3. ORPHAN ORDER ITEMS
   ============================================================ */

SELECT COUNT_BIG(*) AS orphan_order_items
FROM dbo.order_items oi
LEFT JOIN dbo.orders o
    ON oi.order_id = o.order_id
LEFT JOIN dbo.products p
    ON oi.product_id = p.product_id
WHERE o.order_id IS NULL
   OR p.product_id IS NULL;
GO


/* ============================================================
   4. ORPHAN PAYMENTS
   ============================================================ */

SELECT COUNT_BIG(*) AS orphan_payments
FROM dbo.payments p
LEFT JOIN dbo.orders o
    ON p.order_id = o.order_id
WHERE o.order_id IS NULL;
GO


/* ============================================================
   5. DUPLICATE CUSTOMER EMAILS
   ============================================================ */

SELECT
    email,
    COUNT(*) AS duplicate_count
FROM dbo.customers
GROUP BY email
HAVING COUNT(*) > 1;
GO


/* ============================================================
   6. DUPLICATE INVENTORY COMBINATIONS
   ============================================================ */

SELECT
    store_id,
    product_id,
    COUNT(*) AS duplicate_count
FROM dbo.inventory
GROUP BY
    store_id,
    product_id
HAVING COUNT(*) > 1;
GO


/* ============================================================
   7. INVALID ORDER VALUES
   ============================================================ */

SELECT COUNT_BIG(*) AS invalid_orders
FROM dbo.orders
WHERE total_amount < 0
   OR created_at > updated_at;
GO


/* ============================================================
   8. INVALID ORDER ITEM VALUES
   ============================================================ */

SELECT COUNT_BIG(*) AS invalid_order_items
FROM dbo.order_items
WHERE quantity <= 0
   OR discount < 0
   OR line_amount < 0;
GO


/* ============================================================
   9. ORDER TOTAL VS ORDER ITEMS
   ============================================================ */

SELECT
    o.order_id,
    o.total_amount,
    SUM(oi.line_amount) AS calculated_total
FROM dbo.orders o
INNER JOIN dbo.order_items oi
    ON o.order_id = oi.order_id
GROUP BY
    o.order_id,
    o.total_amount
HAVING
    ABS(o.total_amount - SUM(oi.line_amount)) > 0.01;
GO


/* ============================================================
   10. ORDERS WITHOUT ORDER ITEMS
   ============================================================ */

SELECT COUNT_BIG(*) AS orders_without_items
FROM dbo.orders o
LEFT JOIN dbo.order_items oi
    ON o.order_id = oi.order_id
WHERE oi.order_id IS NULL;
GO


/* ============================================================
   11. PAYMENT VS ORDER AMOUNT
   ============================================================ */

SELECT
    o.order_id,
    o.total_amount,
    p.amount AS payment_amount
FROM dbo.orders o
INNER JOIN dbo.payments p
    ON o.order_id = p.order_id
WHERE ABS(o.total_amount - p.amount) > 0.01;
GO


/* ============================================================
   12. MULTIPLE PAYMENTS PER ORDER
   ============================================================ */

SELECT
    order_id,
    COUNT(*) AS payment_count
FROM dbo.payments
GROUP BY order_id
HAVING COUNT(*) > 1;
GO


/* ============================================================
   13. DUPLICATE TRANSACTION REFERENCES
   ============================================================ */

SELECT
    transaction_reference,
    COUNT(*) AS duplicate_count
FROM dbo.payments
GROUP BY transaction_reference
HAVING COUNT(*) > 1;
GO


/* ============================================================
   14. INVALID PAYMENT AMOUNTS
   ============================================================ */

SELECT COUNT_BIG(*) AS invalid_payment_amounts
FROM dbo.payments
WHERE amount < 0;
GO


/* ============================================================
   15. INVENTORY VALIDATION
   ============================================================ */

SELECT
    store_id,
    COUNT(*) AS inventory_rows,
    COUNT(DISTINCT product_id) AS distinct_products
FROM dbo.inventory
WHERE store_id IN (1, 2, 3)
GROUP BY store_id
ORDER BY store_id;
GO


/* ============================================================
   16. INVENTORY INVALID VALUES
   ============================================================ */

SELECT COUNT_BIG(*) AS invalid_inventory_rows
FROM dbo.inventory
WHERE quantity_on_hand < 0
   OR reorder_level < 0;
GO


/* ============================================================
   17. STATUS HISTORY WITHOUT ORDERS
   ============================================================ */

SELECT COUNT_BIG(*) AS orphan_status_history
FROM dbo.order_status_history osh
LEFT JOIN dbo.orders o
    ON osh.order_id = o.order_id
WHERE o.order_id IS NULL;
GO


/* ============================================================
   18. STATUS HISTORY BEFORE ORDER CREATION
   ============================================================ */

SELECT COUNT_BIG(*) AS invalid_status_timestamps
FROM dbo.order_status_history osh
INNER JOIN dbo.orders o
    ON osh.order_id = o.order_id
WHERE osh.changed_at < o.created_at;
GO


/* ============================================================
   19. LATEST STATUS VS CURRENT ORDER STATUS
   ============================================================ */

WITH LatestStatus AS
(
    SELECT
        order_id,
        new_status,
        changed_at,
        status_history_id,
        ROW_NUMBER() OVER
        (
            PARTITION BY order_id
            ORDER BY
                changed_at DESC,
                status_history_id DESC
        ) AS rn
    FROM dbo.order_status_history
)
SELECT
    o.order_id,
    o.order_status,
    ls.new_status AS latest_history_status
FROM dbo.orders o
INNER JOIN LatestStatus ls
    ON o.order_id = ls.order_id
   AND ls.rn = 1
WHERE o.order_status <> ls.new_status;
GO


/* ============================================================
   20. CONTROL PLANE - WATERMARK STATE
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


/* ============================================================
   21. CONTROL PLANE - PIPELINE RUNS
   ============================================================ */

SELECT TOP (50)
    run_id,
    pipeline_name,
    run_start_time,
    run_end_time,
    status,
    rows_read,
    rows_inserted,
    rows_updated,
    rows_deleted,
    idempotent_replays,
    rows_noop,
    error_message
FROM dbo.etl_pipeline_run
ORDER BY run_id DESC;
GO


/* ============================================================
   22. CONTROL PLANE - ERRORS
   ============================================================ */

SELECT TOP (50)
    error_id,
    run_id,
    pipeline_name,
    source_table,
    error_time,
    error_type,
    error_message
FROM dbo.etl_error_log
ORDER BY error_id DESC;
GO


/* ============================================================
   23. CDC CHECKPOINT
   ============================================================ */

SELECT
    source_table,
    capture_instance,
    last_processed_lsn,
    updated_at
FROM dbo.etl_cdc_checkpoint;
GO
