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
- Boundary result: **not a recoverable coding question**. It describes only the difficulty/category of an unspecified algorithm question and preserves no problem statement, input/output, operation, objective, example, or named problem that could identify the missing contract.
- Quality finding: the tagged source currently marks this record `is_valid_for_library=true`, and a Canonical plus placeholder answer were created from it. That conflicts with the content SSOT rule that only real, recoverable questions remain valid.
- Required remediation: reclassify the Question SSOT record as invalid with `exclusion_reason=not_a_question` (or another repository-approved reason only if later source evidence shows the actual problem text), clear/remove its Canonical assignment according to the canonical maintenance procedure, and remove/retire the orphan Canonical/Answer/ReviewProgress atomically. Do **not** write a fabricated coding answer for this item.

## `cq_q_0f228d6d7628cae5c8a2b224451eb8f2`

- Source: `note_structured/6744571d00000000060179e9.json`.
- Recovered wording: `算法：智能水龙头流量控制算法（逻辑设计/实现）`.
- Boundary result: the topic is identifiable, but the actual algorithm contract is **not recoverable** from the stored source. There is no definition of sensors/inputs, actuator/output, flow objective, time model, safety constraints, target volume/rate, feedback behavior, or examples. Many mutually incompatible algorithms could fit this label.
- Required remediation: do not promote a candidate that invents control rules. Unless an earlier/raw source can recover the missing contract, classify the underlying Question as `incomplete_or_unreadable`, record why the problem cannot be reconstructed, and retire the resulting orphan Canonical/Answer/ReviewProgress through the supported atomic maintenance flow.

## Gate impact

Batch 0014 cannot be treated as “10 coding answers to fill”. At least two entries already fail the source-boundary gate and need Question/Canonical remediation instead of answer generation. This is required by C7/C8/C9 final DoD: true questions must be fully reachable; extraction/meta/incomplete records must have explicit exclusion reasons rather than synthetic answers.
