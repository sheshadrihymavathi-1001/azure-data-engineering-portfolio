# Project 01 — Enterprise Retail Data Platform

A production-style retail data platform built to exercise the core engineering problems encountered in enterprise batch data pipelines.

## Business Scenario

A retail organization operates customers, products, stores, orders, order items, payments, inventory, and order-status history in SQL Server. The platform must move operational data into an analytics-ready architecture while handling scale, changes, deletes, duplicates, late-arriving records, failures, and replay.

## Current Scope

- Synthetic enterprise source system in SQL Server
- ~1M customers
- ~100K products
- ~1K stores
- ~5M generated orders
- ~16.8M order items
- ~5M payments
- ~300K inventory records across the original stores
- ~17.4M order-status history records
- Incremental loading using composite watermarks
- SQL Server CDC for customer changes
- Idempotent replay handling
- Checkpoint-based restartability
- Failure simulation and recovery tests
- Referential-integrity and reconciliation validation

## Target Architecture

```text
SQL Server Operational Source
          |
          | ADF / ingestion
          v
ADLS Gen2 Bronze
          |
          | Databricks / PySpark
          v
Delta Silver
          |
          v
Gold / Analytics
          |
          v
Power BI
```

Cloud deployment is intentionally separated from the local source-system and pipeline engineering work. The local environment is used to build and validate deterministic scenarios before cloud validation.

## Repository Areas

```text
project-01-enterprise-retail-data-platform/
├── README.md
├── docs/
├── config/
├── simulator/
├── etl/
├── tests/
├── sql/
├── evidence/
└── requirements.txt
```

## Engineering Focus

1. Incremental loading
2. Composite watermarking
3. CDC
4. Idempotency
5. Checkpointing
6. Failure recovery
7. Data quality
8. Reconciliation
9. Referential integrity
10. Scale and performance

## Interview Positioning

The purpose of the project is not merely to generate millions of rows. The generated source system is a controlled test environment for demonstrating how an enterprise data pipeline behaves under realistic data volume, change patterns, failures, and replay conditions.
