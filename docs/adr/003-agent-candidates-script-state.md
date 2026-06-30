# ADR-003: Agents Generate Candidates, Scripts Own State

## Decision

AI or agent workflows may generate candidate titles, tags, clusters, and answer drafts. Repository scripts own validation, writes, indexes, and status transitions.

## Rationale

The project depends on stable, inspectable data. Keeping state changes inside deterministic scripts prevents silent drift in JSONL, indexes, answer status, and review progress.

## Consequences

- `canonical suggest` produces candidates; `canonical accept|merge|split` mutates state.
- `answer init|sync` owns answer file status.
- `review mark` owns review scheduling.
- Quality reports and run manifests document state changes.
