# Repository map

## Inputs

- Questions: `data/questions/questions.jsonl`
- Canonicals: `data/questions/canonical_questions.jsonl`
- Formal answers: `review/answers/{canonical_id}.md`
- Existing quality baseline: `data/manifests/quality/answer_semantic_baseline.json`
- Quality contract: `config/answer_quality.json`
- Content standard: `docs/refactor/09_answer_content_standard.md`
- Root execution task: `tasks/TASK-20260711-0313-long-tail-answer-quality.md`

## Generated working artifacts

- Candidate: `review/candidates/answers/{canonical_id}.md`
- Evidence: `review/evidence/{canonical_id}.json`
- Independent review: `review/evidence/{canonical_id}.review.json`
- Rewrite queue: `data/manifests/quality/answer_rewrite_queue.jsonl`
- Batch tasks: `tasks/answer-batches/*.md`

## Command sequence

```text
answer context        read-only context and nearby Canonical candidates
answer candidate      render a spec into the candidate directory
answer audit          deterministic and semantic gate report
answer promote        atomic formal-answer replacement after approval
answer sync           synchronize Canonical answer status
```

Until a command is implemented, do not imitate its state-changing behavior manually. Record the missing command in the active task and implement/test it first.

## Non-negotiable boundaries

- Batch size is at most 10.
- Old long-tail prose is not evidence.
- Search snippets and unsourced community prose are discovery-only.
- Candidate failures never modify formal answers.
- `ready/curated` means the complete score, evidence, review, and type-specific gates passed.
