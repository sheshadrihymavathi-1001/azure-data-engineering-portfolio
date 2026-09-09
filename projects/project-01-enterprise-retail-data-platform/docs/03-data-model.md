# Data Model

## Core Entities

```text
customers ─────┐
               ├── orders ─── order_items ─── products
stores ────────┘       │
                       ├── payments
                       └── order_status_history

stores ─── inventory ─── products
```

## Key Relationships

- orders.customer_id → customers.customer_id
- orders.store_id → stores.store_id
- order_items.order_id → orders.order_id
- order_items.product_id → products.product_id
- payments.order_id → orders.order_id
- inventory.store_id → stores.store_id
- inventory.product_id → products.product_id
- order_status_history.order_id → orders.order_id

## Design Principle

The operational schema intentionally resembles a normalized retail source system. Transformation into analytics-oriented structures is treated as a separate pipeline concern rather than mixing source simulation with target modeling.
