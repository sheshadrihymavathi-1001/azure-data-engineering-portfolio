# Project Overview

## Objective

Build and validate a production-style retail data platform that demonstrates incremental ingestion, CDC, idempotency, checkpointing, failure recovery, data quality, reconciliation, and scale.

## Source Domain

- Customers
- Products
- Stores
- Orders
- Order items
- Payments
- Inventory
- Order status history

## Engineering Approach

The source system is simulated in SQL Server so controlled INSERT, UPDATE, DELETE, late-change, duplicate, and failure scenarios can be reproduced deterministically.

## Target Architecture

```text
SQL Server → ADF → ADLS Gen2 Bronze → Databricks/PySpark → Delta Silver → Gold → Power BI
```

## Key Interview Themes

- Why timestamp-only incremental loading can miss records
- Why composite watermarks improve ordering
- Why deletes require CDC or another delete-detection strategy
- Why target commit and checkpoint commit create a replay window
- How idempotency makes replay safe
- How scale changes storage and Spark design decisions
