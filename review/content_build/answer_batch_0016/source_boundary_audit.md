# Answer Batch 0016 — Source Boundary Audit

Date: 2026-08-22

This audit is intentionally source-first. It records only facts recoverable from repository source material before candidate generation. Missing contracts remain explicit; a coding answer must not silently import a familiar LeetCode/API variant. This audit covers **10/10 Canonicals** and performs **no formal promotion**.

## `cq_q_1c3afe7ade1a261841b8309882ba00eb`

- Source: `note_desc/68a48170000000001d00673e.txt` plus matching structured/tagged records.
- Raw wording/context: `手撕，股票交易的升级版，给出一个数组表示股票涨跌情况，只进行一次交易，给出所有的最优交易区间`.
- Boundary result: **recoverable with an input-representation gap**. The source explicitly requires one transaction and all intervals attaining the optimum, but does not state whether the array stores absolute prices or per-period rises/falls.
- Required candidate boundary: state the chosen representation as an API assumption, or present both equivalent formulations separately. Do not claim the source is a named LeetCode variant. Preserve ties: every interval attaining the same best result must be returned.
- Disposition: `candidate_allowed_with_explicit_input_representation_assumption`.

## `cq_q_1c8f7c5e39f56e9ebb53d85b155858c3`

- Source: `note_desc/66642034000000000e0304ab.txt` plus matching structured/tagged records.
- Raw wording/example: `一个非递减数组，原地修改数组使得数组中重复的元素按非递减顺序移到后面（如[1,2,2,3,4,5,5] -> [1,2,3,4,5,2,5]）`.
- Boundary result: **recoverable**. The input is nondecreasing, mutation is in-place, first occurrences form the unique nondecreasing prefix, and the remaining duplicate occurrences form the nondecreasing suffix illustrated by the retained example.
- Missing source details: null/empty handling, primitive type, and whether object identity matters are not stated.
- Required candidate boundary: keep API/null choices explicit and preserve the recovered stable value grouping. An `O(n)` time, `O(1)` extra-space compaction/rotation implementation is source-compatible.
- Disposition: `candidate_allowed_with_explicit_api_assumptions`.

## `cq_q_1f1bcfca5e814405d8f577ae7f3bab1e`

- Source: `note_desc/681767b20000000023014f2f.txt` plus matching structured/tagged records.
- Raw wording: `场景题：N个数的文件中，怎么搜索到前10大的数字？`.
- Boundary result: **recoverable as a streaming Top-K problem with small policy gaps**. The data is file-backed and the requested `K` is 10; materializing/sorting the whole file is not required by the source.
- Missing source details: number type, file encoding, duplicate semantics, malformed rows, and behavior when `N < 10` are not stated.
- Required candidate boundary: state these choices explicitly. A size-10 min-heap gives one-pass `O(N log 10)` time and `O(10)` auxiliary state; if the interviewer means distinct values, deduplication is a separate policy and must be labelled as such.
- Disposition: `candidate_allowed_with_explicit_file_and_duplicate_policy`.

## `cq_q_1f9a7116293b8b8dc6b3f9e1a516221a`

- Source: `note_desc/67e53be1000000001c02f9d7.txt` plus matching structured/tagged records.
- Raw wording: `算法：漏桶的限流算法` (structured form: `请实现漏桶 (Leaky Bucket) 限流算法`).
- Boundary result: **recoverable with API/time/concurrency choices**. The algorithm family is explicit: finite bucket capacity plus steady leak/output rate, with arrivals accepted only while capacity remains.
- Missing source details: request weight, clock source, numeric precision, blocking-vs-reject behavior, concurrency model, and exact public API are not stated.
- Required candidate boundary: expose capacity/rate/time assumptions, use a monotonic time source in the fixture, define boundary behavior exactly, and do not conflate leaky bucket with token bucket burst semantics.
- Disposition: `candidate_allowed_with_explicit_bucket_api_and_time_assumptions`.

## `cq_q_1faf52d8bcec0d3af379225718b09715`

- Source: `note_desc/67499957000000000702aff7.txt`, compared with `note_structured/67499957000000000702aff7.json` and matching tagged data.
- Raw wording: the retained raw note says only `股票问题` in the coding segment.
- Source-widening finding: the structured/current wording expands this to `买卖股票的最佳时机系列题目思路分析`, which is not present in the raw note and silently chooses a whole family of incompatible transaction/cooldown/fee contracts.
- Boundary result: **not deterministic enough for a strict coding answer in its current form**.
- Required remediation: recover stronger original source defining the actual stock variant. If none exists, remove the unsupported widening and classify the Question as `incomplete_or_unreadable`, retiring its unsupported singleton Canonical/Answer/ReviewProgress through the supported maintenance flow. Do not synthesize a stock-series tutorial and present it as the recovered interview contract.
- Disposition: `normalization_and_question_remediation_required_unless_stronger_source_is_recovered`.

## `cq_q_1fd171406c7a78f4a38f274cbb08bcc0`

- Source: `note_structured/6663cea0000000000e03281a.json` and `note_tagged/6663cea0000000000e03281a.json`; the raw caption file contains no question text, so the image-derived structured/tagged pair is the retained repository evidence.
- Preserved wording: `能不能写一个函数，由于指令重排序导致其输出的结果不是想要的？`; the immediately adjacent preserved questions are `volatile 修饰符的作用` and `解释下 happen-before 的规则`.
- Boundary result: **recoverable as a Java Memory Model litmus/example, with a reproducibility caveat**. The requested behavior is an example where lack of ordering permits an observation that source-order reasoning would not expect.
- Required candidate boundary: ground the explanation in JMM happens-before/reordering semantics, clearly state that a racy litmus outcome is *permitted rather than deterministically reproducible*, and show the synchronization/`volatile` repair. Do not attribute every surprising outcome solely to one CPU reorder mechanism.
- Disposition: `candidate_allowed_with_explicit_jmm_nondeterminism_boundary`.

## `cq_q_2187211b75379f7996ea11952ce75e90`

- Source: `note_desc/672207f0000000001b013994.txt` plus matching structured/tagged records.
- Raw wording/context: `做了一道类似于滑动窗口的题，给定字符串s和p，最少删除s中的几个字符才能使得p是s的子串。`
- Boundary result: **recoverable**. Because deletions are from `s` and the target is for `p` to become a contiguous substring of the resulting string, the core task is to find a shortest span of `s` containing `p` as a subsequence; characters inside that span but not used by the matched `p` are exactly the necessary deletions. If no such subsequence exists, the candidate must define an impossible result explicitly.
- Missing source details: character model, impossible sentinel, and exact API are not stated.
- Required candidate boundary: state those choices, test repeated characters and overlapping candidate windows, and avoid changing the problem into ordinary minimum-window-anagram matching.
- Disposition: `candidate_allowed_with_explicit_api_and_impossible_result_assumptions`.

## `cq_q_21a9060b741ad865a51b0d12f1a80372`

- Source: `note_desc/6668516a000000000e033155.txt` plus matching structured/tagged records.
- Raw wording: `镜像二叉树(递归和非递归)`.
- Boundary result: **recoverable**. The required transformation is the usual tree mirror operation and both recursive and iterative implementations are explicitly requested.
- Missing source details: whether the tree is mutated or copied, node type, and empty-tree API behavior are not stated.
- Required candidate boundary: make mutation/copy choice explicit, implement both forms against the same fixture, and verify the involution property (mirroring twice restores the original shape/values).
- Disposition: `candidate_allowed_with_explicit_tree_api_assumptions`.

## `cq_q_2252853d112b2d159896cf5fb9f0a32b`

- Source: `note_desc/68c18d20000000001d0376f9.txt` plus matching structured/tagged records.
- Raw wording: `给一个数组，一个int型target。求使得子数组和大于等于target时，最小的子数组长度。`
- Boundary result: **recoverable, but positivity is not recoverable from the source**. The source does not say array elements or `target` are positive, so an answer that unconditionally uses the classic positive-only shrinking window would invent a precondition.
- Required candidate boundary: either implement the general arbitrary-integer shortest-subarray solution (prefix sums + monotonic deque), or label positivity as an explicit restricted variant and separately state why negative numbers break that window invariant. Define the no-solution result explicitly.
- Disposition: `candidate_allowed_with_general_integer_solution_or_explicit_positive_only_variant`.

## `cq_q_22931d194fbc9e4559ca98bc675b3677`

- Source: `note_desc/684acd11000000002001fe99.txt` plus matching structured/tagged records.
- Raw wording/context: `给你一个链表，奇数节点正序，偶数节点逆序，且奇数节点和偶数节点没有关系，时间复杂度O（n）、空间复杂度O（1）实现将链表变成总体有序。` The source also records the intended solution direction: split odd/even positions, reverse the even-position list, then merge the two sorted lists.
- Boundary result: **recoverable**. Position parity, monotonic directions, target global ordering, and `O(n)` / `O(1)` requirements are all preserved.
- Missing source details: duplicate-value tie stability, node type, and null/single-node API behavior are not stated.
- Required candidate boundary: keep those API choices explicit and implement the recovered split → reverse → merge flow without allocating a second list of values.
- Disposition: `candidate_allowed_with_explicit_tie_and_api_assumptions`.

## Batch disposition

The source-first pass covers all 10 Canonicals in batch 0016:

- source-qualified candidate path with explicit boundaries: `cq_q_1c3afe7ade1a261841b8309882ba00eb`, `cq_q_1c8f7c5e39f56e9ebb53d85b155858c3`, `cq_q_1f1bcfca5e814405d8f577ae7f3bab1e`, `cq_q_1f9a7116293b8b8dc6b3f9e1a516221a`, `cq_q_1fd171406c7a78f4a38f274cbb08bcc0`, `cq_q_2187211b75379f7996ea11952ce75e90`, `cq_q_21a9060b741ad865a51b0d12f1a80372`, `cq_q_2252853d112b2d159896cf5fb9f0a32b`, `cq_q_22931d194fbc9e4559ca98bc675b3677`;
- normalization / Question remediation rather than fabricated answer generation: `cq_q_1faf52d8bcec0d3af379225718b09715`.

Counts alone do not complete the batch. No candidate is promoted by this audit. Each candidate-path item still requires primary-source research where applicable, candidate content, schema-valid evidence, isolated review, executable tests, and the repository's promotion requirements; the remediation item must be resolved through the Question/Canonical SSOT before final content closure.
