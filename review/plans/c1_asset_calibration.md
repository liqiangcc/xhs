# C1 Existing Asset Calibration

Completed: 2026-07-10. Scope: the 34 CanonicalQuestion assets that existed at the C0 baseline.

## Outcome

| Metric | C0 baseline | C1 result |
|---|---:|---:|
| Canonical records | 34 | 34 |
| Assigned question rows | 134 | 150 |
| Distinct assigned question IDs | 37 | 45 |
| Ready answers | 34 | 34 |
| P0 / P1 | 12 / 22 | 18 / 16 |
| Known duplicate Canonical records | 0 | 0 |

The priority change is an expected result of attaching additional companies and occurrences. C1's manual answer audit remains the original 12 P0 records from the frozen baseline; newly promoted P0 records enter the complete P0/P1 upgrade in C3.

## Synonym Attachments

Eight unassigned exact or obvious synonym groups were attached to existing assets. Each group contributed one distinct `question_id` and two source rows.

| Canonical | Attached wording | Added rows |
|---|---|---:|
| `cq_topic_f575096b` | 线程和进程的区别 | 2 |
| `cq_tcp_e9932fa7` | TCP 与 UDP 的区别 | 2 |
| `cq_topic_3f61dd36` | 反转链表 II（LeetCode 92） | 2 |
| `cq_rocketmq_b7347b07` | 提升 RocketMQ 顺序消费性能 | 2 |
| `cq_topic_20fba961` | 超卖的多层防御方案 | 2 |
| `cq_topic_99ffa229` | 索引失效场景 | 2 |
| `cq_topic_89b69343` | 通过架构设计缓解流量压力 | 2 |
| `cq_topic_fe047aa4` | 双十一预约抢购系统 | 2 |

No group was force-merged across a distinct semantic boundary.

## Title And Domain Calibration

Eleven titles were rewritten as single, directly answerable interview questions: ArrayList/LinkedList, Redis performance, TCP/UDP, merge intervals, search efficiency, oversell, reverse linked list II, dynamic-query bottlenecks, MySQL index invalidation, string addition, and microservice decomposition.

Five Canonical domains received an explicit editorial override: merge intervals, search efficiency, reverse linked list II, distributed scheduling, and string addition. The source Question domain remains rebuildable from `note_tagged`; `primary_domain_override` preserves the reviewed Canonical classification during later accept/merge refreshes.

## Answer Type Map

This type determines the content checklist used by C3 and later full-answer work.

| Type | Canonical assets |
|---|---|
| Concept | `cq_arraylist_9d3444a1`, `cq_stringbuffer_8b8caf0d`, `cq_tcp_e9932fa7`, `cq_http_c439559c`, `cq_topic_c569b06e`, `cq_topic_f575096b` |
| Mechanism | `cq_bean_319a398d`, `cq_redis_ff848e90`, `cq_hashmap_4d9f15d2`, `cq_hashmap_d74d2fd7`, `cq_force_index_5e733952`, `cq_topic_2494ec69`, `cq_topic_36aeccc5`, `cq_topic_99ffa229` |
| Scenario | `cq_easyexcel_0f713ce7`, `cq_rocketmq_b7347b07`, `cq_topic_0c5b15b3`, `cq_topic_20fba961`, `cq_topic_71d1f3c1`, `cq_topic_89b69343`, `cq_topic_956bc5ce`, `cq_topic_9e860ba7`, `cq_topic_e60c993a`, `cq_topic_f003d8b7`, `cq_topic_fcc849e5`, `cq_topic_fe047aa4` |
| Coding | `cq_merge_intervals_866286e5`, `cq_topic_3f61dd36`, `cq_topic_722fbd80`, `cq_topic_745b29f7`, `cq_topic_77ee33f1`, `cq_topic_ac84034f`, `cq_topic_cc39dcdb` |
| Project | `cq_ai_055f19f9` |
| Behavior | None in the C0 baseline; this remains an explicit coverage gap for C6/C7. |

## Original P0 Answer Audit

The 12 baseline P0 answers were upgraded to answer version 2 and reviewed against the social-hire content standard.

| Canonical | Type | C1 evidence |
|---|---|---|
| `cq_arraylist_9d3444a1` | Concept | comparison dimensions, selection boundary, four answered follow-ups |
| `cq_bean_319a398d` | Mechanism | lifecycle flow, extension points, version boundary, four answered follow-ups |
| `cq_redis_ff848e90` | Mechanism | data path, event loop boundary, persistence/slow-command caveats |
| `cq_rocketmq_b7347b07` | Scenario | order scope, bottleneck split, failure handling and observability |
| `cq_topic_0c5b15b3` | Scenario | index/write/query flow, capacity and consistency trade-offs |
| `cq_topic_71d1f3c1` | Scenario | scheduling semantics, idempotency, failover and monitoring |
| `cq_topic_722fbd80` | Coding | invariant, Java implementation, complexity, edge cases and variant |
| `cq_topic_77ee33f1` | Coding | pointer invariant, Java implementation, complexity and recursive variant |
| `cq_topic_9e860ba7` | Scenario | diagnosis flow, query/index alternatives, rollout and rollback |
| `cq_topic_ac84034f` | Coding | tails invariant, Java implementation, complexity and envelope variant |
| `cq_topic_f575096b` | Concept | comparison dimensions, scheduling/resource boundary and selection context |
| `cq_topic_fcc849e5` | Scenario | service boundaries, data ownership, consistency and migration strategy |

Every audited answer has four question-and-short-answer follow-ups. Project sections are phrased as project mapping or algorithm training prompts and do not claim unverified personal experience. All three baseline coding answers contain Java implementations.

## Verification

- `migrate build-questions --check --noWrite`: source-derived question data is reproducible.
- `index check --noWrite`: indexes match current data.
- `canonical check --noWrite`: 34 records, 150 assigned rows, no duplicate, missing, mismatch, orphan or unlisted binding.
- `answer validate --strict --noWrite`: all 34 answers pass, including the 12 audited P0 answers.
- `validate all --noWrite`: schema and hash checks pass; taxonomy has no unknown values. Legacy aliases remain migration debt outside C1.
- The Canonical domain-override preservation behavior has a regression test.

## Remaining Work

- C2 expands the high-frequency core to at least 60 Canonical records and 200 assigned rows.
- C3 upgrades every C2 P0/P1 answer using the type map above.
- C7 still performs the row-by-row validity audit; this C1 attachment pass is intentionally limited to obvious synonyms.
