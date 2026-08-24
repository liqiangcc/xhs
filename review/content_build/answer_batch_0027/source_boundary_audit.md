# Answer Batch 0027 — Source-First Boundary Audit

- Evidence boundary: frozen `review/reports/ANSWER_BATCH_0027_SOURCE_PACKET.{json,md}` at extraction commit `52847dba3f30d7fb92d281e873859c51630ed2d6` only; raw caption/image text is authoritative over derived tagged wording, entities, validity flags, or existing Canonical expansion.
- Audit rule: preserve every real recoverable interview Question; narrow unsupported derived wording; fail closed when a unique executable problem contract cannot be recovered. Historical answers/remediation records were not used to form these dispositions.
- Result: original 10 Canonicals → 9 source-recoverable active targets, 1 source-unrecoverable singleton to exclude as `incomplete_or_unreadable`; among the 9 active targets, 3 require source-backed wording/type normalization before candidate authoring.

| Canonical | Disposition | Source-first basis |
| --- | --- | --- |
| `cq_q_555486cb901cc4cd56776f7eeaa0d5b5` | candidate-qualified | Raw caption explicitly says `rand7实现rand10`; the problem identity is recoverable without relying on the derived `LeetCode 470` context. |
| `cq_q_5598debbce04bff1fcb9dbd8f09e9d68` | exclude — incomplete_or_unreadable | Strongest raw source only says `写一个类似数组合并的题目`. It does not preserve whether inputs are sorted, in-place vs returned output, array capacities, duplicate behavior, or any unique problem identity. The current `Merge Array`/`merge sort` expansion is derived and cannot define a verifiable Coding contract. |
| `cq_q_55c3a35aaf4f76ce9aab78ea39d9fddc` | candidate-qualified | Raw caption explicitly lists `链表翻转`; the standard linked-list reversal task is uniquely recoverable at the operation level. Candidate must state its node model and return contract rather than inventing hidden constraints. |
| `cq_q_55dffdc4ce650cf4146064792fc919ca` | candidate-qualified | Raw caption explicitly lists `手撕：…堆排序…`; heap sort is a concrete implementation task. |
| `cq_q_567ffeb91924fcb3677322177357773b` | candidate-qualified | Raw caption explicitly asks `亿级数据找最大的100个`. The task is recoverable as Top-100 over a very large numeric stream/dataset. Derived entities such as `大顶堆`/`快速选择` are suggestions, not source requirements; a bounded-memory streaming solution should normally maintain a size-100 min-heap, while alternatives must state their assumptions. |
| `cq_q_57aa151b635ea5536749fec03c6db22d` | candidate-qualified | Raw caption explicitly asks `使用AB线程以及AB两个锁，手写死锁例子，如何避免死锁`; both the demonstration and avoidance discussion are source-backed. |
| `cq_q_580b69f633d51b4f6c6262690a0fdf9c` | normalize type/validity + candidate-qualified | Raw caption explicitly asks the classic 12-ball balance puzzle and states that the odd ball may be lighter or heavier. It is a real recoverable interview Question, so the derived `is_valid_for_library=false` must not discard it. The expected response is a reasoning/proof construction rather than runnable code; before authoring, normalize it away from the current Coding contract to an explanatory type compatible with the repository quality DoD. |
| `cq_q_58149c934c9b77f14e10c21cebff411c` | normalize wording + candidate-qualified | Raw caption asks to `手写一下用数组实现的循环队列` with enqueue/dequeue, then improve the version that wastes one array slot. This supports array circular-queue implementation and full-slot utilization, but not the current extra `高性能` claim. Narrow the formal wording to the source-backed contract before candidate authoring. |
| `cq_q_5873d2a550ca02cc41b2862b6aefaa77` | normalize wording + candidate-qualified | Image transcript only asks `两个线程交替打印abababab`. The current formal wording invents `100 次` and mandates `wait/notify` or `LockSupport`; those mechanisms may be solution options but are not source requirements. Narrow to alternating A/B output before authoring. |
| `cq_q_59c84ea33afa81784f39f85a824a2d94` | normalize wording + candidate-qualified | Raw caption identifies `LeetCode 16.26 计算器` and specifically records failure to make multiplication/division take precedence. It does not ask for parentheses. Remove the unsupported `括号处理` requirement; retain calculator parsing with multiplication/division precedence as the source-backed task. |

## Required remediation before candidate authoring

- Retire `cq_q_5598...` fail-closed and record its Question in `config/question_validity_audit.json` with an explicit `incomplete_or_unreadable` reason; archive/remove active Answer and ReviewProgress through the repository’s existing bounded remediation mechanisms.
- Preserve `cq_q_580b...` as a real Question despite the derived false validity flag, and normalize its answer/question type so the quality gate does not demand an artificial runnable implementation for a balance-scale reasoning puzzle.
- Narrow the source wording for `cq_q_58149...`, `cq_q_5873...`, and `cq_q_59c84...` without changing the recoverable semantic identity. Rebuild Question projections/indexes and migrate bindings/ReviewProgress as required by the canonical mutation rules.
- Do not promote any answer as part of this boundary step. After remediation, run the full repository integrity and answer-quality gate set before research/candidate work begins.

## Guardrails for the next stage

- `cq_q_5554...`: use rejection sampling/uniformity reasoning; do not assume the derived LeetCode label is itself evidence.
- `cq_q_55c3...`: state the linked-list node/return contract explicitly.
- `cq_q_567f...`: do not present a max-heap as the bounded streaming Top-100 structure; distinguish streaming min-heap, quickselect/in-memory, and distributed/external-memory assumptions.
- `cq_q_57aa...`: the answer needs a reproducible deadlock example plus prevention/avoidance strategies; do not imply `tryLock` is the only valid prevention technique.
- `cq_q_580b...`: prove the minimum and give a complete three-weighing decision strategy; do not turn it into unrelated code merely to satisfy an old type label.
- `cq_q_58149...`: distinguish the sentinel-slot design from a full-capacity design using size/count or equivalent state.
- `cq_q_5873...`: mechanisms such as `wait/notify`, `Condition`, semaphores, or `LockSupport` are implementation choices unless a later primary source adds a constraint.
- `cq_q_59c84...`: no parentheses unless a primary source explicitly adds them; multiplication/division precedence is source-backed.
