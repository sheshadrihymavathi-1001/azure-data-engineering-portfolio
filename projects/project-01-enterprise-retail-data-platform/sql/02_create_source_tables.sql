/*
Project 01 - Enterprise Retail Data Platform

Purpose:
    Create the simulated enterprise OLTP source schema.

Source entities:
    customers
    products
    stores
    orders
    order_items
    payments
    inventory
    order_status_history

Important:
    This DDL is based on the validated local SQL Server schema
    captured using sp_help on 2026-09-09.

    CDC configuration is intentionally kept in 04_enable_cdc.sql.
*/

USE ContosoRetailDB;
GO

/* ================================================================
   1. Customers
   ================================================================ */
IF OBJECT_ID('dbo.customers', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.customers
    (
        customer_id INT NOT NULL IDENTITY(1,1),
        first_name NVARCHAR(100) NOT NULL,
        last_name NVARCHAR(100) NOT NULL,
        email NVARCHAR(255) NOT NULL,
        phone VARCHAR(20) NULL,
        city NVARCHAR(100) NULL,
        state NVARCHAR(100) NULL,
        country NVARCHAR(100) NOT NULL,
        customer_status VARCHAR(20) NOT NULL,
        created_at DATETIME2(3) NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_customers
            PRIMARY KEY CLUSTERED (customer_id),

        CONSTRAINT UQ_customers_email
            UNIQUE NONCLUSTERED (email),

        CONSTRAINT CK_customers_status
            CHECK (customer_status IN ('ACTIVE', 'INACTIVE'))
    );
END;
GO

/* ================================================================
   2. Products
   ================================================================ */
IF OBJECT_ID('dbo.products', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.products
    (
        product_id INT NOT NULL IDENTITY(1,1),
        product_name NVARCHAR(200) NOT NULL,
        category NVARCHAR(100) NOT NULL,
        subcategory NVARCHAR(100) NULL,
        brand NVARCHAR(100) NULL,
        unit_price DECIMAL(12,2) NOT NULL,
        product_status VARCHAR(20) NOT NULL,
        created_at DATETIME2(3) NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_products
            PRIMARY KEY CLUSTERED (product_id),

        CONSTRAINT CK_products_price
            CHECK (unit_price >= 0),

        CONSTRAINT CK_products_status
            CHECK (product_status IN ('ACTIVE', 'INACTIVE'))
    );
END;
GO

/* ================================================================
   3. Stores
   ================================================================ */
IF OBJECT_ID('dbo.stores', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.stores
    (
        store_id INT NOT NULL IDENTITY(1,1),
        store_name NVARCHAR(200) NOT NULL,
        city NVARCHAR(100) NOT NULL,
        state NVARCHAR(100) NOT NULL,
        country NVARCHAR(100) NOT NULL,
        store_type VARCHAR(30) NOT NULL,
        created_at DATETIME2(3) NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_stores
            PRIMARY KEY CLUSTERED (store_id),

        CONSTRAINT CK_stores_type
            CHECK (store_type IN ('WAREHOUSE', 'OUTLET', 'RETAIL'))
    );
END;
GO

/* ================================================================
   4. Orders
   ================================================================ */
IF OBJECT_ID('dbo.orders', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.orders
    (
        order_id BIGINT NOT NULL IDENTITY(1,1),
        customer_id INT NOT NULL,
        store_id INT NOT NULL,
        order_date DATETIME2(3) NOT NULL,
        order_status VARCHAR(20) NOT NULL,
        total_amount DECIMAL(14,2) NOT NULL,
        created_at DATETIME2(3) NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_orders
            PRIMARY KEY CLUSTERED (order_id),

        CONSTRAINT CK_orders_amount
            CHECK (total_amount >= 0),

        CONSTRAINT CK_orders_status
            CHECK (order_status IN ('CANCELLED', 'DELIVERED', 'SHIPPED', 'CONFIRMED', 'PLACED')),

        CONSTRAINT FK_orders_customer
            FOREIGN KEY (customer_id)
            REFERENCES dbo.customers (customer_id),

        CONSTRAINT FK_orders_store
            FOREIGN KEY (store_id)
            REFERENCES dbo.stores (store_id)
    );

    CREATE NONCLUSTERED INDEX IX_orders_customer_id
        ON dbo.orders (customer_id);

    CREATE NONCLUSTERED INDEX IX_orders_store_id
        ON dbo.orders (store_id);

    CREATE NONCLUSTERED INDEX IX_orders_updated_at
        ON dbo.orders (updated_at);
END;
GO

/* ================================================================
   5. Order Items
   ================================================================ */
IF OBJECT_ID('dbo.order_items', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_items
    (
        order_item_id BIGINT NOT NULL IDENTITY(1,1),
        order_id BIGINT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(12,2) NOT NULL,
        discount_amount DECIMAL(12,2) NOT NULL,
        line_amount DECIMAL(14,2) NOT NULL,
        created_at DATETIME2(3) NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_order_items
            PRIMARY KEY CLUSTERED (order_item_id),

        CONSTRAINT CK_order_items_quantity
            CHECK (quantity > 0),

        CONSTRAINT CK_order_items_unit_price
            CHECK (unit_price >= 0),

        CONSTRAINT CK_order_items_discount
            CHECK (discount_amount >= 0),

        CONSTRAINT CK_order_items_line_amount
            CHECK (line_amount >= 0),

        CONSTRAINT FK_order_items_order
            FOREIGN KEY (order_id)
            REFERENCES dbo.orders (order_id),

        CONSTRAINT FK_order_items_product
            FOREIGN KEY (product_id)
            REFERENCES dbo.products (product_id)
    );

    CREATE NONCLUSTERED INDEX IX_order_items_order_id
        ON dbo.order_items (order_id);

    CREATE NONCLUSTERED INDEX IX_order_items_product_id
        ON dbo.order_items (product_id);

    CREATE NONCLUSTERED INDEX IX_order_items_updated_at
        ON dbo.order_items (updated_at);
END;
GO

/* ================================================================
   6. Payments
   ================================================================ */
IF OBJECT_ID('dbo.payments', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.payments
    (
        payment_id BIGINT NOT NULL IDENTITY(1,1),
        order_id BIGINT NOT NULL,
        payment_method VARCHAR(30) NOT NULL,
        payment_status VARCHAR(20) NOT NULL,
        amount DECIMAL(14,2) NOT NULL,
        transaction_reference VARCHAR(100) NOT NULL,
        created_at DATETIME2(3) NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_payments
            PRIMARY KEY CLUSTERED (payment_id),

        CONSTRAINT UQ_payments_transaction_reference
            UNIQUE NONCLUSTERED (transaction_reference),

        CONSTRAINT CK_payments_amount
            CHECK (amount >= 0),

        CONSTRAINT CK_payments_method
            CHECK (payment_method IN ('CASH', 'WALLET', 'NET_BANKING', 'UPI', 'CARD')),

        CONSTRAINT CK_payments_status
            CHECK (payment_status IN ('REFUNDED', 'FAILED', 'SUCCESS', 'PENDING')),

        CONSTRAINT FK_payments_order
            FOREIGN KEY (order_id)
            REFERENCES dbo.orders (order_id)
    );

    CREATE NONCLUSTERED INDEX IX_payments_order_id
        ON dbo.payments (order_id);

    CREATE NONCLUSTERED INDEX IX_payments_updated_at
        ON dbo.payments (updated_at);
END;
GO

/* ================================================================
   7. Inventory
   ================================================================ */
IF OBJECT_ID('dbo.inventory', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.inventory
    (
        inventory_id BIGINT NOT NULL IDENTITY(1,1),
        store_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity_on_hand INT NOT NULL,
        reorder_level INT NOT NULL,
        updated_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_inventory
            PRIMARY KEY CLUSTERED (inventory_id),

        CONSTRAINT UQ_inventory_store_product
            UNIQUE NONCLUSTERED (store_id, product_id),

        CONSTRAINT CK_inventory_quantity
            CHECK (quantity_on_hand >= 0),

        CONSTRAINT CK_inventory_reorder
            CHECK (reorder_level >= 0),

        CONSTRAINT FK_inventory_product
            FOREIGN KEY (product_id)
            REFERENCES dbo.products (product_id),

        CONSTRAINT FK_inventory_store
            FOREIGN KEY (store_id)
            REFERENCES dbo.stores (store_id)
    );

    CREATE NONCLUSTERED INDEX IX_inventory_updated_at
        ON dbo.inventory (updated_at);
END;
GO

/* ================================================================
   8. Order Status History
   ================================================================ */
IF OBJECT_ID('dbo.order_status_history', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_status_history
    (
        status_history_id BIGINT NOT NULL IDENTITY(1,1),
        order_id BIGINT NOT NULL,
        old_status VARCHAR(20) NULL,
        new_status VARCHAR(20) NOT NULL,
        changed_at DATETIME2(3) NOT NULL,

        CONSTRAINT PK_order_status_history
            PRIMARY KEY CLUSTERED (status_history_id),

        CONSTRAINT CK_order_status_history_new_status
            CHECK (new_status IN ('CANCELLED', 'DELIVERED', 'SHIPPED', 'CONFIRMED', 'PLACED')),

        CONSTRAINT FK_order_status_history_order
            FOREIGN KEY (order_id)
            REFERENCES dbo.orders (order_id)
    );

    CREATE NONCLUSTERED INDEX IX_order_status_history_changed_at
        ON dbo.order_status_history (changed_at);

    CREATE NONCLUSTERED INDEX IX_order_status_history_order_id
        ON dbo.order_status_history (order_id);
END;
GO

/* ================================================================
   Validation: confirm objects exist
   ================================================================ */
SELECT
    s.name AS schema_name,
    t.name AS table_name
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
WHERE s.name = 'dbo'
  AND t.name IN
  (
      'customers',
      'products',
      'stores',
      'orders',
      'order_items',
      'payments',
      'inventory',
      'order_status_history'
  )
ORDER BY t.name;
GO
