# Answer Batch 0015 — Source Boundary Audit

Date: 2026-08-22

This is an incremental source-first audit. It records only facts recoverable from repository source material before candidate generation. The audit is currently **4/10 complete**; it is not a batch-completion or promotion record.

## `cq_q_12ddfcc24143adac1b20b63f547516e7`

- Source: `note_desc/67dcc3ec000000001c007e3a.txt` plus matching structured/tagged records.
- Raw wording: `算法：遍历一次，翻转从m到n的链表结点`.
- Boundary result: **recoverable**. The source establishes a linked-list subrange reversal, endpoints `m` and `n`, and the requirement to traverse once.
- Missing source details: whether positions are zero- or one-based, behavior for invalid ranges, null input, and whether the list must be mutated in place are not stated.
- Required candidate boundary: keep those API choices explicit; do not present them as recovered source facts. A one-pass pointer-rewiring implementation is source-compatible.
- Disposition: `candidate_allowed_with_explicit_api_assumptions`.

## `cq_q_149617b44a4092a42317fcdc4912ca2d`

- Source: `note_desc/67de17c2000000001a005fa3.txt` plus matching structured/tagged records.
- Raw wording: `求三个有序数组的中位数且空间复杂度为O(1)`.
- The same source also records the interviewee's solution note: treat it like merging three sorted sequences and stop after reaching the middle position. That note is useful evidence of the intended linear-selection direction, but it is not a stronger problem contract than the question itself.
- Boundary result: **recoverable with small contract gaps**. The three inputs are sorted and auxiliary space must be `O(1)`.
- Missing source details: numeric type, whether arrays may be empty, and the exact convention for even total length are not explicitly preserved.
- Required candidate boundary: state the median convention and empty-input behavior as implementation assumptions; do not invent size bounds or claim the source requires a particular time complexity.
- Disposition: `candidate_allowed_with_explicit_api_assumptions`.

## `cq_q_151d0e35bf49f36b6d51c686a232a636`

- Source: `note_desc/646768f30000000014026af6.txt` plus matching structured/tagged records.
- Raw wording: `算法题: 对角线打印矩阵`.
- Raw-source check: the surrounding note lists interview questions only; it does not preserve a matrix example, start corner, diagonal direction, zig-zag rule, rectangular/square restriction, or expected output sequence.
- Boundary result: **not deterministic enough for a strict coding answer**. Several incompatible traversal contracts fit the same label (for example anti-diagonals vs main-diagonal families, and fixed-direction vs zig-zag traversal).
- Required remediation: recover stronger source evidence if available; otherwise classify the Question as `incomplete_or_unreadable` and retire its orphan Canonical/Answer/ReviewProgress through the supported atomic maintenance flow. Do not choose an arbitrary diagonal order and present it as the original problem.
- Disposition: `question_remediation_required_unless_stronger_source_is_recovered`.

## `cq_q_1547f601c5bd6746da03d6b3cc246ee8`

- Source: `note_desc/67d6d9fd000000001d026e12.txt` plus matching structured/tagged records.
- Raw wording: `把一个只包含1-9（可能不全有）的字符串分割成3个以上的数字，然后判断此字符串是否可以分割成斐波那契数列（如果是，必须是连着的。最后return bool）`.
- Boundary result: **recoverable**. The source establishes the input alphabet (`1`–`9` only), contiguous partitioning of the whole string into at least three numbers, Fibonacci recurrence across adjacent parts, and Boolean output.
- Missing source details: maximum input length, integer width/overflow policy, and whether arbitrarily large decimal segments are expected are not stated.
- Required candidate boundary: preserve the no-zero source constraint, state the numeric/overflow strategy explicitly, and test both successful and failing partitions without importing unrelated LeetCode constraints.
- Disposition: `candidate_allowed_with_explicit_numeric_boundary`.

## Incremental disposition

Audited in this increment: 4 of 10 Canonicals.

- candidate path with explicit source boundaries: 3
- question remediation unless stronger source is recovered: 1
- formal promotions performed: 0

Remaining Canonicals must receive the same raw-source check before any batch-level conclusion is recorded.
