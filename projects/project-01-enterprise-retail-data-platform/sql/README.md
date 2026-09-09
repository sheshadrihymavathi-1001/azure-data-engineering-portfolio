# SQL Scripts

This directory contains the SQL Server database setup, source schema,
ETL control tables, CDC configuration, and validation queries used by
Project 01 — Enterprise Retail Data Platform.

## Script Execution Order

Run the scripts in the following order:

1. `01_create_database.sql`
2. `02_create_source_tables.sql`
3. `03_create_control_tables.sql`
4. `04_enable_cdc.sql`
5. `05_validation_queries.sql`

## Purpose

The SQL layer represents the operational source system and the
control plane required for production-style data ingestion.

The project uses SQL Server as the simulated enterprise OLTP source.

The source system contains:

- Customers
- Products
- Stores
- Orders
- Order Items
- Payments
- Inventory
- Order Status History

The control plane contains:

- Pipeline run audit
- Incremental-load watermarks
- Error logging
- CDC checkpoints

## Design Principles

- Composite watermark for deterministic incremental extraction
- Checkpoint advancement only after successful target processing
- Idempotent replay handling
- CDC-based INSERT / UPDATE / DELETE processing
- Pipeline auditability
- Data-quality and reconciliation validation
- Restartable processing
- Referential-integrity validation

## Scale

The local source environment was designed to exercise large-scale
data-engineering scenarios:

| Entity | Approximate Volume |
|---|---:|
| Customers | 1M+ |
| Products | 100K+ |
| Stores | 1K |
| Orders | 5M+ |
| Order Items | 16M+ |
| Payments | 5M+ |
| Inventory | 300K+ |
| Order Status History | 17M+ |

The large dataset is generated locally and is not committed to GitHub.
Only schema, generation logic, validation logic and engineering evidence
are stored in the repository.
