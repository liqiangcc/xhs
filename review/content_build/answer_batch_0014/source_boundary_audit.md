# Answer Batch 0014 — Source Boundary Audit

Date: 2026-08-21

This audit is intentionally source-first. It records what the repository source actually preserves before any answer is promoted. A coding candidate must not invent a missing problem contract merely to make a placeholder answer look complete.

## `cq_q_0d3977f38b683b8870680583294bec75`

- Source: `note_structured/68a7d1ed000000001b0214a7.json` and matching tagged record.
- Recovered wording: first and last position of an element in a sorted array; the wording names the standard *Find First and Last Position of Element in Sorted Array* problem.
- Boundary result: recoverable enough for a source-qualified candidate. Details that come from the named standard problem rather than the local note must stay explicitly attributed to that external problem statement.
- Current action: candidate + deterministic Java validation prepared; no formal promotion before independent review/evidence and pilot approval.

## `cq_q_0e62222057e8d368021aea7612198b22`

- Source: `note_structured/6694f7db000000000a0247b6.json` and `note_tagged/6694f7db000000000a0247b6.json`.
- Recovered wording: `算法：旋转字符串`.
- Boundary result: the local record is ambiguous because it has no parameters, examples, or return contract. The same title is commonly used for the two-string rotation predicate (for example LeetCode 796), but that correspondence is not proven by the local note.
- Current action: candidate prepared with the ambiguity as an explicit first-class boundary. The candidate answers the two-string predicate only as a named standard interpretation and separately states that a `k`-position left-rotation problem would be a different contract. Deterministic KMP-vs-enumeration validation passes; no formal promotion before independent review/evidence and pilot approval.

## `cq_q_0e8c139a0cb99666f643c27d40386cdc`

- Source: `note_structured/67e1143d000000001d0387d5.json` and `note_tagged/67e1143d000000001d0387d5.json`.
- Recovered wording: `算法：难度为 Easy/Medium 的题目。`
- Raw-source check: `note_desc/67e1143d000000001d0387d5.txt` contains only topic hashtags and therefore does not recover any hidden coding statement beneath the structured/tagged summary. No repository-local text inspected in this source chain supplies an input/output contract, operation, objective, example, or named problem.
- Boundary result: **not a recoverable coding question**. It describes only the difficulty/category of an unspecified algorithm question and preserves no problem statement, input/output, operation, objective, example, or named problem that could identify the missing contract.
- Quality finding: the tagged source currently marks this record `is_valid_for_library=true`, and a Canonical plus placeholder answer were created from it. That conflicts with the content SSOT rule that only real, recoverable questions remain valid.
- Required remediation: reclassify the Question SSOT record as invalid with `exclusion_reason=not_a_question`, clear/remove its Canonical assignment according to the canonical maintenance procedure, and remove/retire the orphan Canonical/Answer/ReviewProgress atomically. Do **not** write a fabricated coding answer for this item.

## `cq_q_0f228d6d7628cae5c8a2b224451eb8f2`

- Source: `note_structured/6744571d00000000060179e9.json`, `note_desc/6744571d00000000060179e9.txt`, and the embedded note text in `note_json/6744571d00000000060179e9.json`.
- Recovered wording: the raw note itself says only `算法：智能水龙头`; the structured layer expands the label to `算法：智能水龙头流量控制算法（逻辑设计/实现）` but does not add a recoverable contract.
- Raw-source check: the surrounding first-round note lists project discussion, a privacy-compliance scenario, then exactly `算法：智能水龙头`; it immediately proceeds to the second-round list. There are no omitted parameters, examples, constraints, or follow-up lines describing the algorithm.
- Boundary result: the topic is identifiable, but the actual algorithm contract is **not recoverable** from the stored source. There is no definition of sensors/inputs, actuator/output, flow objective, time model, safety constraints, target volume/rate, feedback behavior, or examples. Many mutually incompatible algorithms could fit this label.
- Required remediation: classify the underlying Question as `incomplete_or_unreadable`, record that the raw stored note contains only the label and cannot reconstruct the problem, and retire the resulting orphan Canonical/Answer/ReviewProgress through the supported atomic maintenance flow. Do **not** promote a candidate that invents control rules.

## `cq_q_0f9160e71713fc230d36b97489276d71`

- Source: `note_desc/684a8ada0000000012006277.txt`, `note_structured/684a8ada0000000012006277.json`, and `note_tagged/684a8ada0000000012006277.json`.
- Raw wording: `笔试题。三道sql题，5分钟内做完。最后一题没答出来。`
- Current tagged/canonical wording: `SQL笔试题：常见复杂查询与聚合函数应用`.
- Boundary result: **not a recoverable SQL problem**. The raw note confirms that three SQL questions existed but preserves none of their tables, columns, predicates, desired result, or even whether aggregation was involved. `常见复杂查询与聚合函数应用` is an inferred category, not recovered problem text.
- Required remediation: reclassify the Question as `incomplete_or_unreadable`, remove the unsupported Canonical/Answer/ReviewProgress atomically, and do not replace the missing SQL statements with a generic tutorial.

## `cq_q_10b16ccc8b909fb29e93c5d4a67ddf71`

- Source: `note_img_txt/694512cd000000001e004d1a.txt` plus matching structured/tagged records.
- Raw wording: `算法题：链表大数求和，尾节点是个位数，头节点是最大的数，输出两个链表之和的新链表`; the next numbered line asks for time and space complexity.
- Boundary result: **recoverable**. The source establishes the representation direction (most-significant digit at head, least-significant at tail), the two-list addition operation, creation of a result list, and complexity follow-up.
- Candidate constraint: the source does not state whether input nodes may be mutated, whether leading zeroes are legal, or how null/empty lists are treated. A candidate must state its chosen API assumptions rather than presenting them as quoted source facts. A stack-based `O(m+n)` implementation is source-compatible because carry propagation starts at the tails while the list links point from most-significant toward least-significant digits.
- Current action: eligible for a source-qualified candidate and deterministic tests; formal answer remains unchanged until independent review/evidence and pilot approval.

## `cq_q_10ca2be141844abf692f07c3c2ab8918`

- Source: embedded raw note text in `note_json/6818de380000000022024043.json` plus matching structured/tagged records. `note_img_txt/6818de380000000022024043.txt` explicitly says image text could not be recognized.
- Raw wording: `数组分组，图2的数组如何按性别分组？如何按年龄分组？怎么写更优雅（分组逻辑通过函数传入）`.
- Boundary result: **recoverable with a missing sample-data boundary**. The abstraction requirement is clear: group an array by a caller-supplied classifier so the same routine can group by sex or age. The actual `图2` sample array is not recoverable from the repository OCR artifact.
- Candidate constraint: implement the generic grouping abstraction and use clearly labelled illustrative data only if an example is needed. Do not claim any synthesized `Person[]` values came from figure 2. Tests should verify the grouping contract independently of the missing screenshot data.

## `cq_q_116c85df5f0d148fc71487b5e00d1c8f`

- Source: `note_desc/68aae954000000001d0117cc.txt` plus matching structured/tagged records.
- Raw wording: `算法题：代码实现一个生产者消费者模型`.
- Current tagged/canonical wording: `利用 wait/notify 或 BlockingQueue 手写一个经典的生产者-消费者模型，并解析其在多线程协作场景下的物理意义`.
- Boundary result: **the task is recoverable, but the stored Question/Canonical wording is source-widened**. The raw note asks only for a producer-consumer implementation. It does not mandate `wait/notify`, `BlockingQueue`, multiple implementations, or a separate “physical meaning” explanation.
- Required boundary correction: normalize the Question/Canonical wording back to the source-supported task before promotion. A candidate may compare `wait/notify` and `BlockingQueue` as optional implementation approaches, but must label that comparison as solution design rather than source requirement.

## `cq_q_11a63f77b2a2a6f2f46bdcdeaf0ec3eb`

- Source: `note_desc/685d25970000000017036aec.txt` plus matching structured/tagged records.
- Raw wording: `算法题是字符串的字符出现次数排列`.
- Boundary result: **recoverable only as an explicitly underspecified prompt**. The source preserves the input family (string), frequency counting, and an ordering operation, but does not say whether the output is characters, `(char,count)` pairs, or a reconstructed string; nor does it state ascending/descending order or tie-breaking.
- Required action: do not silently choose one online-problem contract. Either recover stronger source evidence or keep the candidate boundary explicit and branch on the missing output/order contract. If the strict Answer DoD requires one deterministic output contract, classify this item `incomplete_or_unreadable` rather than inventing one.

## `cq_q_12a229bba2127f25e5b1219c3d2be0a0`

- Source: `note_desc/66adb99a0000000009015abb.txt` plus matching structured/tagged records.
- Raw wording: third-round `mid-hard手撕（不是很常见）`; no problem statement follows.
- Boundary result: **not a recoverable coding question**. This is only a difficulty/frequency description of an unspecified hand-written algorithm problem.
- Required remediation: reclassify as `not_a_question` (or `incomplete_or_unreadable` if the repository chooses that reason consistently for lost algorithm statements) and atomically retire the orphan Canonical/Answer/ReviewProgress. Do not generate a generic medium-hard algorithm answer.

## Batch disposition

The source-first boundary pass now covers all 10 Canonicals in batch 0014:

- source-qualified candidate path: `cq_q_0d3977f38b683b8870680583294bec75`, `cq_q_0e62222057e8d368021aea7612198b22` (explicit ambiguity), `cq_q_10b16ccc8b909fb29e93c5d4a67ddf71`, `cq_q_10ca2be141844abf692f07c3c2ab8918` (missing sample data), `cq_q_116c85df5f0d148fc71487b5e00d1c8f` (after source-widening correction), and potentially `cq_q_11a63f77b2a2a6f2f46bdcdeaf0ec3eb` only if the missing output/order contract is treated explicitly;
- Question/Canonical remediation instead of answer generation: `cq_q_0e8c139a0cb99666f643c27d40386cdc`, `cq_q_0f228d6d7628cae5c8a2b224451eb8f2`, `cq_q_0f9160e71713fc230d36b97489276d71`, and `cq_q_12a229bba2127f25e5b1219c3d2be0a0`;
- one additional normalization defect is confirmed for `cq_q_116c85df5f0d148fc71487b5e00d1c8f`: the current stored wording adds requirements absent from the raw source.

Batch 0014 therefore cannot be treated as “10 coding answers to fill”. C7/C8/C9 final DoD requires real questions to be source-faithful and fully reachable, while extraction/meta/incomplete records need explicit exclusion reasons instead of synthetic answers.
