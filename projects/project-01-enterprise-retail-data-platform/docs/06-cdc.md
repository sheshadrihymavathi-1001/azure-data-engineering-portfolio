# Change Data Capture

SQL Server CDC is used to demonstrate a change-log based ingestion pattern for customers.

## Change Types

- INSERT
- UPDATE after-image
- DELETE

For normal synchronization, the pipeline consumes the effective row image needed by the target rather than treating the update-before image as a separate business state.

## CDC Checkpoint

A source-table-specific checkpoint stores the last processed LSN. The pipeline reads a fixed CDC range, applies the changes to the target, and advances the checkpoint only after target processing succeeds.

## Failure Scenario

The project intentionally simulates a successful target commit followed by checkpoint failure. A retry therefore sees the same CDC changes again. The target must handle the replay idempotently.

## Delete Replay

A DELETE replay is expected to become a safe no-op when the target row has already been removed.
