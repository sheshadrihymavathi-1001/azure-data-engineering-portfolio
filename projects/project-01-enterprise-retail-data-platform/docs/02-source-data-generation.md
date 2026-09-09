# Source Data Generation

## Purpose

The synthetic source system is a controlled enterprise test environment. It is designed to exercise pipeline behavior at meaningful scale rather than to serve as a dataset for distribution.

## Current Scale

| Entity | Approximate rows |
|---|---:|
| Customers | 1,000,019 |
| Products | 100,005 |
| Stores | 1,000 |
| Orders | 5,000,010 |
| Order items | 16,848,926 |
| Payments | 5,000,010 |
| Inventory | 300,015 |
| Order status history | 17,402,225 |

## Generation Principles

- Python generators write directly to SQL Server using batched inserts.
- Generators use checkpoints where restartability matters.
- Generated data follows business-oriented distributions rather than uniform random values.
- Referential relationships are preserved.
- Validation queries reconcile generated entities after each major generation phase.

## Customer Activity

Customers are distributed into HIGH, MEDIUM, and LOW activity tiers. These tiers are used to create non-uniform order demand and a more realistic workload.

## Product Popularity

Products are distributed across VERY_HIGH, HIGH, MEDIUM, and LOW popularity tiers. The order-item generator uses these tiers to create concentrated product demand and a useful basis for later Spark-skew experiments.

## Orders

Approximately five million generated orders span the configured historical period. Order volume is intentionally concentrated by customer activity tier and store distribution.

## Order Items

The generated order-item count uses a weighted 1–8 item distribution. Each order's item values are reconciled against the order total.

## Payments

Each generated order receives one baseline payment record. Payment methods and statuses use controlled distributions.

## Inventory

Inventory is generated for the original three stores across all 100,005 products, producing 300,015 valid store/product combinations.

## Order Status History

Status history follows valid order lifecycles such as PLACED → CONFIRMED → SHIPPED → DELIVERED, with cancellation paths where appropriate. The latest status history is reconciled with the current order status.

## Why Synthetic Data?

A static sample database cannot reliably reproduce controlled edge cases such as identical timestamps, replay after checkpoint failure, source deletes, CDC sequences, or deterministic scale. The simulator makes these scenarios reproducible.

## GitHub Policy

The generated millions of rows are intentionally not committed to GitHub. The repository stores generator logic, SQL definitions, tests, validation queries, and engineering evidence instead.
