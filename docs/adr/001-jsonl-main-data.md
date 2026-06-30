# ADR-001: JSONL Main Data

## Decision

Use JSONL files as the first production data layer for questions, canonical questions, and review progress metadata.

## Rationale

The repo is still data-refactor heavy. JSONL keeps records reviewable in Git, supports deterministic rebuilds, and avoids introducing SQLite before the canonical and answer contracts are stable.

## Consequences

- Scripts must keep output sorting stable.
- Validation and index checks are required before committing generated data.
- SQLite remains a future optimization, not a current dependency.
