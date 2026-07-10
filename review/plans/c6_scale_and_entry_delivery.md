# C6 Scale And Review Entry Delivery

Completed: 2026-07-10.

## Outcome

| Metric | C5 result | C6 result |
|---|---:|---:|
| Canonical records | 100 | 258 |
| Assigned question rows | 328 | 600 |
| Ready answers | 100 | 100 |
| P0/P1 missing answers | 0 | 0 |
| Review progress records | 100 | 258 |
| Mastered records | 0 | 1 |

All 158 C6 additions are P2 long-tail assets. C6 intentionally validates scale and discovery while deferring their complete answer build to C8; no P0/P1 answer debt was introduced.

## Stable Long-Tail Canonicalization

`scripts/content/canonicalize_unassigned.js` provides a deterministic path from unassigned Question groups to Canonical records:

- group exact source rows by stable `question_id`;
- attach only when a normalized title exactly matches an existing title/alias;
- otherwise create `cq_q_<question_id>` so low-frequency independent questions keep their own semantic boundary;
- derive normalized domain, entities, companies, frequency and priority;
- persist Question bindings, Canonical records and indexes together.

The C6 run selected 158 groups / 272 rows, taking coverage from 328 to exactly 600 assigned rows.

## Review Entries

Four reproducible plans were generated from the same Canonical/Answer/Progress data:

| Entry | File | Items |
|---|---|---:|
| JVM topic drill | `review/plans/c6_jvm_topic.md` | 15 |
| Meituan company simulation | `review/plans/c6_meituan_company.md` | 20 |
| P0 comprehensive review | `review/plans/c6_p0_comprehensive.md` | 20 |
| Weak-item recovery | `review/plans/c6_weak_recovery.md` | 4 |

`review prepare` now accepts `--status`, making weak/learning/mastered lists first-class saved plans rather than JSON-only output.

## Scheduler Recovery Path

The prior scheduler retained `mistake_count` forever, so a weak card could never become learning. C6 changed successful `good/easy` reviews to consume one historical mistake. A regression test fixes the expected path:

```text
weak(level=1, mistakes=1)
  --easy--> learning(level=3, mistakes=0)
  --easy--> mastered(level=5, mistakes=0)
```

The ArrayList card executed this transition in the repository. Its two C6 events are explicitly labeled as scheduler validation, not user mastery evidence.

## Verification

- `canonical check`: 258 records, 600 assigned rows, no binding integrity error.
- P0/P1 missing answers: zero.
- Topic/company/P0/weak plans all contain results.
- Review progress: 258 records.
- Full CI and rebuild/index verification are recorded in the stage commit.
