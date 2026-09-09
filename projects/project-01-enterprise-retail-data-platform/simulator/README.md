# Source Simulator

The simulator creates a controlled SQL Server operational source for Project 01.

## Components

- `customer_events.py` — controlled customer INSERT/UPDATE/DELETE events
- `customer_generator.py` — customer volume generation
- `product_generator.py` — product volume and popularity tiers
- `store_generator.py` — store generation
- `order_generator.py` — order generation
- `order_item_generator.py` — order-item generation and restart checkpoints
- `payment_generator.py` — payment generation and restart checkpoints
- `inventory_generator.py` — store/product inventory matrix and replay handling
- `order_status_history_generator.py` — realistic order lifecycle history

Generated data is not committed to GitHub.
