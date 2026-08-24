# Answer Batch 0021 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0021_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It deliberately separates source recoverability from answer correctness.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 8
- Recoverable normalization: 1
- Source-unrecoverable / excluded: 1
- Active after boundary remediation: 9

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_36adef6f4fb0a868fca32118d03969a5` | exclude / `incomplete_or_unreadable` | Strongest source only says “二叉树相关操作”; no concrete operation or executable contract survives. |
| `cq_q_37245bc43848028f006b2e4eaea7500c` | candidate-qualified | Source explicitly asks to implement a singly linked-list structure with CRUD. |
| `cq_q_37772fa23763570fb8d04764450230d3` | candidate-qualified | Source explicitly asks to use C to distinguish current system 32-bit vs 64-bit; answer must state the process-vs-OS observability limitation. |
| `cq_q_377898b5b67a6219eaa583c6d2e21081` | candidate-qualified | Source preserves the positive-integer transition rules and minimum-operation objective. |
| `cq_q_37b42623861093a397be5bff1ee3fad6` | candidate-qualified | Source explicitly says “LC 25. K 个一组翻转链表”, making the problem identity recoverable. |
| `cq_q_37c73385b683ba395f0d066744d02f37` | candidate-qualified | Source explicitly asks for multi-threaded array sorting; implementation must state thread-count/merge assumptions rather than invent them as source facts. |
| `cq_q_37ffe67ab69164654b0a19aa57b410df` | candidate-qualified | Source explicitly names topological sort; representation/API details must be stated as answer-side assumptions. |
| `cq_q_39a734b5a5602f2d965f9e2f35a50514` | candidate-qualified | Source explicitly asks for pairs summing to 10 in an increasing array. |
| `cq_q_3a1c2667429257c4fbe7e2d8d8012096` | normalize, then candidate-qualified | Source asks for the maximum outstanding-package time interval and time/space complexity, but does not prescribe Difference Array or Sweep Line. Prescribing those methods in the Question was unsupported enrichment. |
| `cq_q_3a314d375a1b0bdf127953e8614906e0` | candidate-qualified | Source question directly asks for the first common node of two intersecting singly linked lists. |

## Normalization

`cq_q_3a1c2667429257c4fbe7e2d8d8012096` remains the Canonical identity, while its source Question is normalized from the derived solution-prescribing wording to:

> 给定一天内1亿个包裹的存入和取出时间，如何找出未取出包裹数最多的时间段及持续时长？方案的时间和空间复杂度是多少？

The normalized Question id is `f2d52be391d5a320a5460d80e4256278`. `Difference Array` / `Sweep Line` may be evaluated as answer strategies, but they are not source facts and therefore are removed from Question/Canonical metadata.

## Fail-closed exclusion

`cq_q_36adef6f4fb0a868fca32118d03969a5` is archived rather than answered. The source phrase “二叉树相关操作” is a category fragment, not a recoverable coding contract. The exclusion is recorded in `config/question_validity_audit.json` with an explicit explanation so source rows remain auditable.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, and all answer CI gates pass may batch 0021 candidate work begin.
