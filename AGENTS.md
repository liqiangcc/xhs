# XHS repository guidance

## Answer assets

- Use `$xhs-answer-curator` for any rewrite, improvement, audit, batch upgrade, or promotion under `review/answers/`.
- Treat `config/answer_quality.json` and `docs/refactor/09_answer_content_standard.md` as the quality contract.
- Do not use `long_tail_baseline` prose as a factual source and do not run the legacy generator to create `ready` answers.
- Work on one explicit Canonical or a batch of at most 10. Verify Canonical boundaries and answer type before writing.
- If Canonical boundaries need changing, follow `docs/refactor/10_current_dedup_canonical_operations.md`: new relationships use `canonical suggest -> dedup decide -> dedup apply`; existing Canonical maintenance uses merge/split. Do not create `canonical_candidates.v1`, use legacy `canonical accept` for new work, or edit Question `canonical_id` manually.
- Render new work into `review/candidates/answers/`; keep evidence and isolated review records under `review/evidence/`.
- Do not set `status=ready` or `quality_tier=curated` manually. Use the audited promotion command after score, evidence, independent review, and type-specific gates pass.
- A failed candidate must leave the formal answer unchanged and remain `needs_update`.

## Validation

For answer changes, run the candidate-specific audit plus:

```bash
node scripts/xhs.js answer validate --strict --noWrite
node scripts/xhs.js canonical check --noWrite
npm test
```

Run generated compilation/fixture tests for Coding and SQL answers. Structural validation is not evidence of semantic quality.

## Resumable tasks

- Keep the active Markdown task and batch task current before and after edits.
- Commit every completed subtask or answer batch separately; do not mix unrelated files.
- Never mark a quality stage complete from aggregate counts alone. Use the full evidence required by its completion audit.
