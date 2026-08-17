---
name: xhs-answer-curator
description: Research, rewrite, independently review, validate, and promote XHS interview answers from needs_update/long_tail_baseline to curated-ready. Use in this repository when a user asks to regenerate, improve, audit, batch-upgrade, or promote files under review/answers, or to execute the long-tail answer quality task. Do not use for question extraction, OCR, taxonomy-only changes, or generic interview coaching that does not update the answer library.
---

# XHS Answer Curator

Upgrade answer assets through a fail-closed evidence and review workflow. Treat existing long-tail text as an artifact to replace, never as a factual source.

## Load authoritative rules

Before changing an answer, read:

1. `AGENTS.md` for repository execution rules.
2. `config/answer_quality.json` for scores, hard failures, evidence policy, and type requirements.
3. `docs/refactor/09_answer_content_standard.md` for answer structure and oral quality.
4. `references/repo-map.md` for commands, inputs, and outputs.
5. `docs/refactor/10_current_dedup_canonical_operations.md` when Canonical boundaries need review or mutation.

If these sources conflict, use the stricter quality requirement and record the conflict in task notes. For Canonical/Dedup command semantics, `10_current_dedup_canonical_operations.md` is authoritative over historical plans and ADRs.

## Select bounded work

- Accept one explicit `canonical_id` or one generated batch task containing at most 10 IDs.
- Require the current answer to be `needs_update`, unless the user explicitly requests a curated-answer audit.
- Never overwrite all long-tail files in one run.
- Update the active task/batch status before editing, and commit each completed batch separately.

## Prepare context and verify the Canonical

Run `node scripts/xhs.js answer context --canonical-id <id> --noWrite`.

For each ID:

1. Read the Canonical, every assigned source wording, domain, entities, companies, and nearby Canonicals.
2. Decide whether all source variants have one answer boundary.
3. Stop answer writing and route to Canonical relation/boundary review when the boundary is duplicated, mixed, or too broad.
4. Confirm the answer type from the response expected by the interviewer; do not trust the historical source label alone.

### Canonical boundary handoff

Answer curation must not bypass the Canonical/Dedup workflow.

When step 3 finds a boundary problem:

- use `canonical suggest -> dedup decide -> dedup apply` for newly detected same/alias relationships;
- use `canonical merge` / `canonical split` only to maintain already-existing Canonical records;
- never create a new `canonical_candidates.v1` manifest;
- never use `canonical accept` as the default path for newly detected relationships;
- never edit Question `canonical_id` manually to make answer validation pass;
- never let similarity evidence silently become a relation decision.

`canonical accept` is legacy compatibility for historical/manual manifests only. If the needed operation cannot be expressed through the current Application flow, stop answer writing, record the blocker, and route the repository change separately instead of inventing state transitions inside the answer task.

## Research before writing

- Do not use the old `long_tail_baseline` body as evidence or copy its prose.
- Use official specifications, official documentation, upstream source/release notes, primary papers, or reproducible tests for material claims.
- Require first-hand evidence for version behavior, defaults, thresholds, protocols, API contracts, and removals.
- Record claim-to-source mappings and `checked_at` in `review/evidence/{canonical_id}.json`.
- If a material claim cannot be verified, leave the answer `needs_update`.
- For Project/Behavior answers, use only user-provided facts. Without them, provide a fillable framework and never invent a completed story.

## Write a candidate, not the formal answer

Write a candidate spec and render it only under `review/candidates/answers/`.

The candidate must:

- directly answer the Canonical in the core conclusion;
- preserve all eight required sections;
- cover every source wording assigned to the Canonical;
- meet the selected type requirements;
- include at least three topic-specific answered follow-ups, including one boundary or failure question;
- contain no category-level filler, cross-topic facts, generic follow-ups, or fabricated experience;
- include runnable Java/SQL plus boundary tests for Coding answers.

Do not edit `review/answers/{canonical_id}.md` during candidate creation.

## Require isolated review

Use a fresh reviewer context or reviewer subagent when available. Give the reviewer only:

- Canonical record and source variants;
- candidate answer;
- evidence sidecar;
- `config/answer_quality.json` and the content standard.

Do not give the reviewer the writer's rationale, self-score, or expected decision. Require a structured score, hard-failure list, uncovered variants, unsupported claims, and a promote/revise/reject decision.

If no isolated reviewer is available, stop with `needs_update`; self-review alone cannot promote an answer.

## Revise at most twice

- Apply reviewer findings to the candidate and evidence, then rerun review.
- Allow at most two revision rounds per candidate.
- After two failed rounds, keep `needs_update`, record the blocker, and move no formal files.
- Never lower thresholds to complete a batch.

## Validate and promote atomically

Run:

```bash
node scripts/xhs.js answer audit --candidate <path> --require-evidence --noWrite
node scripts/xhs.js answer promote --canonical-id <id> --candidate <path> --evidence <path>
node scripts/xhs.js answer validate --strict --noWrite
node scripts/xhs.js canonical check --noWrite
```

For Coding/SQL also run the generated compilation/fixture tests. Promotion requires total score at least 90, every dimension minimum, zero hard failures, valid evidence, and an independent approve decision.

After promotion, verify metadata is `status=ready`, `quality_tier=curated`, version increased, and Canonical status synchronized. A failed promotion must leave the formal answer byte-for-byte unchanged.

## Close the batch

- Update the queue row, evidence, active task notes, validation result, changed files, and commit hash.
- Run all batch validations before committing.
- Randomly route at least 20% of steady-state candidates to human review; route 100% of the first 60 pilot answers.
- If any human audit finds a hard failure, downgrade the affected answer, return the whole batch to review, and audit all answers in that batch.
