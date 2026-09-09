# Data Quality and Validation

Validation is treated as an engineering control, not an afterthought.

## Referential Integrity

Validate that every child foreign key points to an existing parent.

Examples:

- orders → customers
- orders → stores
- order_items → orders
- order_items → products
- payments → orders
- inventory → stores/products
- order_status_history → orders

Expected result: zero orphan records.

## Reconciliation

Use multiple checks rather than relying only on row counts:

- source/target row counts
- missing business keys
- duplicate business keys
- aggregate amount checks
- order total versus order-item total
- payment amount versus order amount
- latest status history versus current order status

## Temporal Validation

Status-history events must occur at or after the order creation timestamp and remain monotonic within an order.

## Inventory Validation

The final inventory matrix must contain one row per store/product combination for the intended stores, with no duplicate combinations.
