# Repository map

## Inputs

- Questions: `data/questions/questions.jsonl`
- Canonicals: `data/questions/canonical_questions.jsonl`
- Formal answers: `review/answers/{canonical_id}.md`
- Existing quality baseline: `data/manifests/quality/answer_semantic_baseline.json`
- Quality contract: `config/answer_quality.json`
- Content standard: `docs/refactor/09_answer_content_standard.md`
- Current Canonical/Dedup operations: `docs/refactor/10_current_dedup_canonical_operations.md`
- Root execution task: `tasks/TASK-20260711-0313-long-tail-answer-quality.md`

## Generated working artifacts

- Candidate: `review/candidates/answers/{canonical_id}.md`
- Evidence: `review/evidence/{canonical_id}.json`
- Independent review: `review/evidence/{canonical_id}.review.json`
- Rewrite queue: `data/manifests/quality/answer_rewrite_queue.jsonl`
- Batch tasks: `tasks/answer-batches/*.md`

## Answer command sequence

```text
answer context        read-only context and nearby Canonical candidates
answer candidate      render a spec into the candidate directory
answer audit          deterministic and semantic gate report
answer promote        atomic formal-answer replacement after approval
answer sync           synchronize Canonical answer status
```

Until a command is implemented, do not imitate its state-changing behavior manually. Record the missing command in the active task and implement/test it first.

## Canonical boundary routing

When answer context reveals duplicate/mixed Canonical boundaries, stop answer work and use the current repository workflow instead of manipulating bindings directly:

```text
newly detected relationship:
canonical suggest
  -> dedup decide
  -> dedup apply

existing Canonical maintenance:
canonical merge / canonical split
```

Current review state lives in:

```text
data/manifests/dedup/relation_candidate_queues.json
data/manifests/dedup/relation_decisions.jsonl
```

Do not create `canonical_candidates.v1` for new work. `canonical accept` is legacy compatibility for historical/manual manifests only.

## Non-negotiable boundaries

- Batch size is at most 10.
- Old long-tail prose is not evidence.
- Search snippets and unsourced community prose are discovery-only.
- Candidate failures never modify formal answers.
- `ready/curated` means the complete score, evidence, review, and type-specific gates passed.
- Answer work must not edit Question `canonical_id` manually or bypass explicit Dedup review/freshness checks.
