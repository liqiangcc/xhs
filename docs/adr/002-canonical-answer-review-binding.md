# ADR-002: Bind Answers And Review To Canonical Questions

## Decision

Answers and review progress bind to `canonical_id`, not raw `question_id`.

## Rationale

Raw questions preserve original interview wording. Canonical questions represent reusable knowledge assets across repeated or equivalent prompts. Answers and spaced review should follow the reusable knowledge asset.

## Consequences

- `review/answers/{canonical_id}.md` is the answer unit.
- `review/progress.json` stores progress by `canonical_id`.
- Canonical merge and split commands must update question bindings and indexes.
