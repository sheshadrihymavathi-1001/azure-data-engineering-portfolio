# Incremental Loading

## Customer Incremental Pattern

The customer pipeline uses a composite watermark:

```sql
WHERE updated_at > ?
   OR (updated_at = ? AND customer_id > ?)
ORDER BY updated_at, customer_id
```

The timestamp provides the primary ordering and the business key breaks ties.

## Checkpoint Rule

The checkpoint is advanced only after successful target processing. This prevents a failed target write from permanently advancing the source position.

## Replay Window

Target commit and checkpoint update are separate transactions. Therefore a target commit can succeed while checkpoint persistence fails. The next run must safely replay the source rows.

## Idempotency

The target operation must distinguish between:

- new records
- updates
- already-applied records
- no-op deletes

The objective is safe retry without duplicate target records.

## Delete Limitation

A timestamp watermark cannot discover a source DELETE because the deleted row no longer exists to satisfy the `updated_at` predicate. This is one reason CDC is demonstrated separately.
