# Answer Batch 0015 — Source Boundary Audit

Date: 2026-08-22

This audit is intentionally source-first. It records only facts recoverable from repository source material before candidate generation. A coding prompt that lost its deterministic contract is remediated or excluded rather than completed by invention. This audit covers **10/10 Canonicals** and performs **no formal promotion**.

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
- Boundary result: **not deterministic enough for a strict coding answer**. Several incompatible traversal contracts fit the same label.
- Required remediation: recover stronger source evidence if available; otherwise classify the Question as `incomplete_or_unreadable` and retire its orphan Canonical/Answer/ReviewProgress through the supported atomic maintenance flow. Do not choose an arbitrary diagonal order and present it as the original problem.
- Disposition: `question_remediation_required_unless_stronger_source_is_recovered`.

## `cq_q_1547f601c5bd6746da03d6b3cc246ee8`

- Source: `note_desc/67d6d9fd000000001d026e12.txt` plus matching structured/tagged records.
- Raw wording: `把一个只包含1-9（可能不全有）的字符串分割成3个以上的数字，然后判断此字符串是否可以分割成斐波那契数列（如果是，必须是连着的。最后return bool）`.
- Boundary result: **recoverable**. The source establishes the input alphabet (`1`–`9` only), contiguous partitioning of the whole string into at least three numbers, Fibonacci recurrence across adjacent parts, and Boolean output.
- Missing source details: maximum input length, integer width/overflow policy, and whether arbitrarily large decimal segments are expected are not stated.
- Required candidate boundary: preserve the no-zero source constraint, state the numeric/overflow strategy explicitly, and test both successful and failing partitions without importing unrelated LeetCode constraints.
- Disposition: `candidate_allowed_with_explicit_numeric_boundary`.

## `cq_q_154efbda1c72ac4419f349acb9b14438`

- Source: `note_desc/6811f3490000000022005691.txt`, `note_structured/6811f3490000000022005691.json`, and `note_tagged/6811f3490000000022005691.json`.
- Raw wording: `求两个json 数据的diff`.
- Raw-source check: the note confirms this was one of two hand-written coding tasks, but preserves no example and no diff contract. The structured/tagged layers repeat the same short label and do not recover additional source facts.
- Boundary result: **not deterministic enough for a strict coding answer**. A JSON diff can legitimately mean shallow key comparison, recursive structural changes, JSON Patch-like operations, path/value tuples, or other incompatible output formats; array matching/order semantics are also absent.
- Required remediation: recover stronger source evidence; otherwise classify as `incomplete_or_unreadable` and retire the unsupported Canonical/Answer/ReviewProgress atomically. Do not invent a diff schema and call it the interview question.
- Disposition: `question_remediation_required_unless_stronger_source_is_recovered`.

## `cq_q_17b558215583de1ad3b47eda00479a00`

- Source: `note_desc/6800eaac000000001c033334.txt` plus matching structured/tagged records.
- Raw wording: `一个sql题目，给出一个表，有id、日期和当天购买数量，求每天最多购买的top2`.
- Boundary result: **recoverable with SQL/tie assumptions**. The source preserves one table with `id`, date, and daily purchase quantity and asks for the top two rows within each day.
- Missing source details: SQL dialect, exact column names/types, whether ties should return more than two rows, and the deterministic secondary ordering when quantities tie are not stated.
- Required candidate boundary: use a clearly labelled fixture/schema equivalent to the recovered three columns, state whether the chosen interpretation uses `ROW_NUMBER` or tie-preserving `RANK`/`DENSE_RANK`, and test multiple dates and ties. Do not claim the invented fixture names are source text.
- Disposition: `candidate_allowed_with_explicit_sql_and_tie_assumptions`.

## `cq_q_18099a746a57ce6990cd550546739ac6`

- Source: `note_desc/677d11ea0000000020027cab.txt`; compared against `note_structured/677d11ea0000000020027cab.json` and matching tagged data.
- Raw wording: `算法：二叉树的最大路径和`.
- Source-widening finding: the structured/current wording adds `（LeetCode 124）`, but the raw note does **not** name LeetCode 124 and preserves no definition of what endpoints a valid path may have.
- Boundary result: **current Canonical is source-widened and the raw coding contract is ambiguous**. Root-to-leaf, any-node-to-any-node, and other maximum-path variants are incompatible problems.
- Required remediation: first remove the unsupported `LeetCode 124` attribution. Recover stronger source evidence for the path definition; if none exists, classify the underlying prompt as `incomplete_or_unreadable` rather than silently selecting the LeetCode 124 contract.
- Disposition: `normalization_and_question_remediation_required_unless_stronger_source_is_recovered`.

## `cq_q_187c619f3c62046184546a4f04cc40f2`

- Source: `note_desc/6878ac580000000010026c75.txt` plus matching structured/tagged records.
- Raw wording: `100个协程依次打印1-100`.
- Context: the immediately surrounding questions explicitly discuss Go's GMP model, goroutines and scheduling, so interpreting `协程` here as Go goroutines is source-supported.
- Boundary result: **recoverable with a small scheduling/API boundary**. The required observable result is ordered output `1..100` coordinated by 100 goroutines.
- Missing source details: whether each goroutine must print exactly one number, required channel/lock primitive, output API, timeout/cancellation behavior, and goroutine creation order are not specified.
- Required candidate boundary: keep synchronization mechanism as a solution choice, prove ordered output and termination, and run the repository concurrency-review workflow before any production/concurrency mutation or promotion.
- Disposition: `candidate_allowed_after_concurrency_review_with_explicit_scheduling_assumptions`.

## `cq_q_1b54beec356cebaa5bf68b8935cb9e0a`

- Source: `note_desc/68ca70d2000000000e00f5bb.txt` plus matching structured/tagged records.
- Raw sequence: `手写一个自定义 Hook：usePrevious (用于记录state上一次的值)` followed by `在 usePrevious 基础上，增加新需求：让其值的改变也能触发UI更新。`
- Boundary result: **recoverable**. The source establishes a React custom hook that records the previous state value and adds the requirement that changing the hook-held value participate in rendering rather than being invisible to the UI.
- Missing source details: exact hook return shape, initial previous value, whether the update occurs during render/effect, and the demonstration component are not specified.
- Required candidate boundary: make those API choices explicit and ground React render/state claims in primary React documentation; do not turn the answer into a fabricated project story.
- Disposition: `candidate_allowed_with_explicit_hook_api_assumptions`.

## `cq_q_1b6ddacfba9a37a4613f02dad96d8fe9`

- Source: repository OCR artifact `note_img_txt/657d92d4000000001502fcdf.txt` from the Tencent Music written-test image, plus matching structured/tagged records.
- Recovered prompt line: `字符串解码 3a4[bc] -> aaabcbcbc` in the OCR artifact; an implementation is shown below it.
- Source inconsistency: the visible repeat token `4[bc]` and the OCR-rendered output do not agree arithmetically, and the shown implementation also does not correctly establish semantics for a bare numeric prefix such as `3a` before it later parses `4[bc]`. The repository source therefore does not preserve one trustworthy general grammar merely by having this image-derived code.
- Boundary result: **real coding prompt, but the deterministic decoding grammar is not sufficiently recoverable from the repository artifact**. It is unclear which constructs besides the single example are valid (bare-character repetition, bracket groups, nesting, multi-digit counts, invalid input behavior).
- Required remediation: recover/verify the original image text or stronger source. If that cannot establish a consistent grammar, classify this record as `incomplete_or_unreadable`; do not infer a full decoder grammar from a contradictory OCR/example/solution artifact.
- Disposition: `question_remediation_required_unless_original_contract_is_recovered`.

## Batch disposition

The source-first boundary pass covers all 10 Canonicals in batch 0015:

- source-qualified candidate path with explicit assumptions: `cq_q_12ddfcc24143adac1b20b63f547516e7`, `cq_q_149617b44a4092a42317fcdc4912ca2d`, `cq_q_1547f601c5bd6746da03d6b3cc246ee8`, `cq_q_17b558215583de1ad3b47eda00479a00`, `cq_q_187c619f3c62046184546a4f04cc40f2`, `cq_q_1b54beec356cebaa5bf68b8935cb9e0a`;
- Question/Canonical remediation instead of fabricated answer generation: `cq_q_151d0e35bf49f36b6d51c686a232a636`, `cq_q_154efbda1c72ac4419f349acb9b14438`, `cq_q_18099a746a57ce6990cd550546739ac6`, `cq_q_1b6ddacfba9a37a4613f02dad96d8fe9`.

Counts alone do not complete the batch. No candidate in this batch is promoted by this audit. Each candidate-path item still requires candidate content, evidence, isolated review, applicable code/concurrency gates, and the repository's promotion requirements; remediation items must be resolved through the Question/Canonical SSOT before final content closure.
