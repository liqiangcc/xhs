# Answer Batch 0041 — source-first recoverability review

Date: 2026-08-27

Scope: repository-local source evidence only. This review is intentionally performed before drafting the remaining candidates. It distinguishes raw-note evidence, image/structured extraction, and later normalized Question metadata; task-level type hints and existing long-tail baseline prose are not source evidence.

## Inputs checked

- `review/content_build/answer_batch_0041/source_inventory.json`
- `note_tagged/67d25ca8000000000b017d2a.json`
- `note_structured/67d25ca8000000000b017d2a.json`
- `note_desc/67d25ca8000000000b017d2a.txt`
- `note_desc/681a34e3000000002102e69d.txt`
- `note_desc/6668131f00000000060061b3.txt`
- `note_desc/67eb383d000000001c01d8fc.txt`
- `note_desc/67dccdb2000000000900ce21.txt`
- `note_desc/67aef7c100000000170382ee.txt`
- `note_tagged/681055de000000000900d6df.json`
- `note_desc/681055de000000000900d6df.txt`
- current Question/Canonical ownership as frozen by the batch inventory

## Decisions

### `cq_q_a7016342ea74a55c817ed58e69009a64` — fail closed / source-unrecoverable

Normalized preserved wording: `算法实现：给定原数组为 [a...z]，编写一个简单的 Hash 算法将其映射为新的整数数组？`

The repository preserves neither a hash-table size/modulus nor a required hash function, output length, collision rule, expected mapped values, samples, or correctness oracle. Several materially different contracts fit the same wording: ordinal encoding (`a -> 0` ... `z -> 25`), a polynomial/string hash modulo an arbitrary integer, Java-style hash values, or bucket indices with a collision policy. These are not interchangeable, and ordinal encoding is not even a hash in the collision-oriented sense normally meant by a hash-table exercise.

`note_desc/67d25ca8000000000b017d2a.txt` contains only the post caption and adds no missing algorithm contract. `note_tagged` and `note_structured` repeat the same normalized wording; they do not recover an executable oracle. Therefore a strict-valid Coding answer cannot choose one mapping without fabricating the original task. The safe next action is to retire this singleton with an explainable `incomplete_or_unreadable` decision, preserving the archived baseline but removing active Canonical/Answer/ReviewProgress reachability.

### `cq_q_a791750e006147b75dcb2c13b7fa90e9` — recoverable as Scenario

Raw-note wording: `场景题：从两个包含上亿 url（最长 64byte ）的文件中找出重复 url`.

The objective and one useful size bound are directly preserved: identify URLs present in both very large files, with each URL at most 64 bytes. Exact RAM/disk limits are not preserved, so a candidate must label capacity numbers as assumptions rather than source facts. The current source inventory resolves `answer_type=scenario`; the task file's older `coding` hint must not override this SSOT.

A source-bounded candidate may explain exact external hash partitioning as the correctness-preserving path and Bloom filters only as a probabilistic prefilter/negative filter unless false-positive handling is explicitly resolved. It must cover partition skew/hot buckets, duplicate rows within each file, disk I/O, hash-collision-safe equality checking, and a deterministic small-file fixture.

### `cq_q_a7ba6548994bab4e4412f98bf4a8dee2` — recoverable as Coding with explicit API boundary

Normalized image-derived wording: `算法：实现 setInterval 和 clearInterval`.

The text caption only says two coding questions were asked and does not recover their bodies, so the structured/tagged extraction is the strongest surviving question text. The requested API pair is nevertheless specific enough for a bounded JavaScript polyfill. Runtime-specific timer precision, event-loop scheduling guarantees, argument forwarding, `this` binding, numeric-handle compatibility, and reentrancy semantics are not source-preserved and must not be presented as required behavior.

A strict candidate can define a minimal contract: schedule repeated callback attempts via recursive `setTimeout`, return an opaque handle, and make `clearInterval(handle)` prevent future scheduling; clear-before-first-fire and clear-from-inside-callback require deterministic tests. It must explicitly state that it is not a byte-for-byte browser/Node timer specification implementation and cannot guarantee exact wall-clock intervals.

### `cq_q_a811de1b146bd3b47f2f7ca524ac1c3b` — fail closed / source-unrecoverable

Raw-note wording: `很简单的去重链表重复元素。（双指针）`.

The later normalized Question expands this to `Remove Duplicates from Sorted List` and adds a sorted-list identity, but those details are not present in the raw note. The raw source does not establish whether the list is sorted, whether duplicate-valued nodes should be collapsed to one representative or all removed, whether duplicates can be non-adjacent, or the expected return contract. Multiple different linked-list problems and algorithms fit “去重链表重复元素（双指针）”.

Because the missing semantics change both correctness and implementation, a strict-valid Coding answer cannot safely choose the LeetCode-83 contract from the normalized title. This singleton should be retired as `incomplete_or_unreadable` unless stronger original image/text evidence is recovered.

### `cq_q_a873b7b82bcca35bc35609aa914b70c9` — recoverable as Coding with declared digit assumption

Raw-note wording: `2道算法题，求根节点到叶子节点的数字之和,多线程打印a,b,c`.

The operation is directly preserved: form root-to-leaf path numbers and sum them. The source does not explicitly preserve the node-value range; a candidate may use the minimal decimal-digit assumption `0..9`, but must label that as an implementation assumption because multi-digit or negative node values change the concatenation rule. Verification must include a single node, asymmetric tree, leading zero, and multiple leaves, and should use `long` or state overflow limits rather than silently relying on `int`.

### `cq_q_a9a3cdad804b0bdf8732d7d22dcb03c2` — recoverable as Coding

Raw-note wording: `堆排序实现从大到小（要求独立补全完整代码）` and `面试官只给main函数，需自实现堆结构！`.

The output order and self-implemented-heap requirement are both directly preserved. A candidate must actually implement heap operations rather than delegate to a library sort/priority queue. Either a min-heap that repeatedly emits the minimum into the array from right to left or a max-heap with a final reversal can satisfy descending order, provided the invariant is stated and verified. It must cover duplicates, negative numbers, already sorted/reverse-sorted input, and empty/singleton arrays, and distinguish linear heap construction from repeated sift operations.

### `cq_q_aa5412e581a46db5a2dbf3f5bc6262eb` — recoverable with explicit problem-identity boundary

Normalized image-derived wording: `算法：手撕螺旋矩阵（Spiral Matrix）。`

The text caption does not contain the question body, so the tagged/structured image extraction is the strongest surviving evidence. The parenthetical `Spiral Matrix` supports the standard traversal problem identity, while the repository does not preserve a separate `Spiral Matrix II`/matrix-generation requirement. A candidate must therefore state explicitly that it is answering traversal of a provided matrix, not generation of an `n x n` matrix. Rectangular matrices, one row/column, empty input, and shrinking-boundary termination require tests. If stronger raw source later shows a generation task, this decision must be reopened instead of force-fitting the traversal answer.

## Batch consequence

- Already retired fail-closed: `cq_q_a6ed4f0f01d44463de7f8af046ccd001`, `cq_q_a70af552af23eb909cd728cbd46fdbac`.
- Already source-first reviewed candidate: `cq_q_a735fdca7e7f00dbb5349db43e5f3987`.
- Newly classified fail-closed: `cq_q_a7016342ea74a55c817ed58e69009a64` and `cq_q_a811de1b146bd3b47f2f7ca524ac1c3b`; remediation must update validity projection, Canonical, active baseline Answer, ReviewProgress, generated indexes/manifests, and all repository gates atomically.
- Candidate drafting may safely proceed for `cq_q_a791750e006147b75dcb2c13b7fa90e9`, `cq_q_a7ba6548994bab4e4412f98bf4a8dee2`, `cq_q_a873b7b82bcca35bc35609aa914b70c9`, `cq_q_a9a3cdad804b0bdf8732d7d22dcb03c2`, and `cq_q_aa5412e581a46db5a2dbf3f5bc6262eb` using the boundaries above.

This review does not itself promote, retire, or mutate any Canonical. Promotion still requires candidate evidence, executable/type-appropriate validation, isolated review, and the repository's current human/S11 gates.