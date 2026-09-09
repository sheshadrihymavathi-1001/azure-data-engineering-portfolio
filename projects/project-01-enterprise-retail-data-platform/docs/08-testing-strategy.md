# Testing Strategy

## Test Layers

### Unit / Component Tests

Validate loaders and transformation behavior independently.

### Scenario Tests

Exercise realistic source changes:

- INSERT
- UPDATE
- DELETE
- identical timestamps
- replay
- missing target row
- checkpoint failure

### Reconciliation Tests

Validate counts, business keys, aggregates, duplicates, relationships, and temporal rules after generation or ingestion.

## Representative Scenarios

| Scenario | Expected behavior |
|---|---|
| Two customers share an `updated_at` value | Composite watermark loads both in key order |
| Target commit succeeds, checkpoint fails | Retry replays safely |
| Source customer is deleted | Timestamp-only incremental load does not discover it |
| CDC DELETE replay | Second DELETE becomes a no-op |
| Existing target row receives replayed INSERT | Duplicate is recognized rather than inserted again |
| Invalid lifecycle timestamp | Validation fails |

## Test Philosophy

The goal is to test failure semantics and correctness guarantees, not simply achieve code coverage.
