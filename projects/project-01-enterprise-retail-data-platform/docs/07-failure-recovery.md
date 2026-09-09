# Failure Recovery

Failure recovery is tested deliberately rather than assumed.

## Failure Classes

1. Failure before target commit
2. Target commit succeeds but checkpoint update fails
3. Replay after an unchanged checkpoint
4. Duplicate INSERT during replay
5. DELETE replay after the target row is already absent
6. Connection or SQL Server resource failure during large-scale generation

## Recovery Principle

```text
Read checkpoint
      ↓
Process source range
      ↓
Commit target
      ↓
Persist checkpoint
```

If checkpoint persistence fails after target commit, the source range is processed again. Idempotency converts the replay from a data-corruption risk into a recoverable condition.

## What Is Demonstrated

- Checkpoint remains unchanged after simulated checkpoint failure.
- Retry detects already-committed target state.
- Replayed INSERT/UPDATE operations do not create duplicate business keys.
- Replayed DELETE operations can become no-ops.

## Important Boundary

Target commit and checkpoint commit are separate transactions in the current local implementation. The project therefore demonstrates replay safety rather than claiming an atomic distributed transaction across source, target, and checkpoint.
