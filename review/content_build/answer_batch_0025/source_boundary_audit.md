# Answer Batch 0025 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0025_SOURCE_PACKET.{json,md}` and repository-local caption/image transcripts before candidate authoring. It fails closed when the source cannot uniquely define an executable contract and removes unsupported detail from generated Canonical wording.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 6
- Recoverable wording normalization: 1
- Answer-type metadata correction: 1
- Source-unrecoverable / excluded: 2
- Active after boundary remediation: 8

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_497537f6fc79fb11fe854f142aa59d1e` | normalize, then candidate-qualified | Caption preserves only “算法题：图的拓扑排序”. The current dependency-management application clause is generated detail not present in source, so the Question is narrowed to the stable topological-sort problem identity. |
| `cq_q_4ba0bfbd9b87d9415d9724ee0db55ff6` | reclassify Concept, then candidate-qualified | Caption fully preserves the 1..N coin/divisibility flipping rule and explicitly says “说思路”; this is a parity/divisor reasoning problem, not a handwriting-code request. |
| `cq_q_4b3ef4f6983ba06fff2fe65aeb96f0a7` | candidate-qualified | Caption explicitly asks to implement a stack with one queue and requires only one sub-operation to be O(n). |
| `cq_q_4d49a2c53d787ce1d520075e3493152e` | candidate-qualified | Image transcript explicitly records the binary-tree longest-distance/diameter coding problem. |
| `cq_q_4d502e2e2c294d9f9dd468cff39c0162` | candidate-qualified | Caption explicitly asks for the median of two unsorted arrays that may contain duplicates. |
| `cq_q_4e2e32002bd212ba6a2a232d0761421e` | candidate-qualified | Image transcript preserves int[] a, k <= a.length, and the requirement to return the k smallest values. |
| `cq_q_4ef5329ef53731815f32df4a2942c8d2` | candidate-qualified | Caption explicitly asks to rebuild a tree from inorder/postorder traversals and print preorder non-recursively. |
| `cq_q_4f3244bca47814cd02291ecda86cad4c` | candidate-qualified | Caption explicitly asks to implement a stack using two queues. |
| `cq_q_4b55831a928b320f47710e2de666045e` | exclude / `incomplete_or_unreadable` | 仓库最强来源只保留“手撕：一道简单题”，没有题目、输入、输出、约束、样例或稳定的问题标识；source packet 还显示原 tagged Question 已明确 is_valid_for_library=false。无法从“简单题”唯一恢复任何可执行合同，因此按 incomplete_or_unreadable fail closed。 |
| `cq_q_4f04a54536a8856b265b4cfb49f1325a` | exclude / `incomplete_or_unreadable` | 来源只重复题名“找出字符串中出现次数最多的字母，并对前面的数字求和”，没有保留字符串语法。无法判断数字是单个数字还是多位整数、数字与字母如何配对、连续数字/无数字如何处理、并列最高频字母如何选择；这些差异会改变解析与输出，当前材料不足以得到唯一可验证实现，因此按 incomplete_or_unreadable fail closed。 |

## Normalization

`cq_q_497537f6fc79fb11fe854f142aa59d1e` keeps its Canonical identity but its source Question is narrowed to `算法题：图的拓扑排序`; normalized Question id: `f458a6a9baa833f5bcd4c2465098be0d`. The final answer may explain dependency-management as an example only if clearly labeled as an application, not as part of the recovered interview contract.

## Type correction

`cq_q_4ba0bfbd9b87d9415d9724ee0db55ff6` keeps its Question identity and is reclassified from `算法手撕_Coding` to `八股文_Concept`. Its source asks for the reasoning and final set of face-up coins, not runnable code.

## Fail-closed exclusions

The two excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with a specific `incomplete_or_unreadable` explanation.

## Candidate constraints

- The one-queue stack source does not say which operation must be O(n); a candidate may choose push-heavy or pop-heavy and must state that choice.
- The unsorted-two-array median source allows duplicates and explicitly rejected relying only on the sorted-array LeetCode 4 contract; a candidate must solve the unsorted input stated by source.
- The top-k-smallest source gives `k <= a.length`; empty-array behavior is outside source and should be stated as an API assumption if covered.

## Next gate

Only after Question/index/type projections are rebuilt and all coverage, canonical, review-integrity, strict answer, unit, semantic/evidence/code/coverage gates pass may batch 0025 candidate work begin.
