# Answer Batch 0041 — source-first recoverability review

Date: 2026-08-27

Scope: repository-local source evidence only. This review is intentionally performed before drafting the remaining candidates. It distinguishes source-preserved contract from assumptions that a later candidate may state explicitly; it does not treat task-level type hints or existing long-tail baseline prose as source evidence.

## Inputs checked

- `review/content_build/answer_batch_0041/source_inventory.json`
- `note_tagged/67d25ca8000000000b017d2a.json`
- `note_structured/67d25ca8000000000b017d2a.json`
- `note_desc/67d25ca8000000000b017d2a.txt`
- `note_tagged/681055de000000000900d6df.json`
- current Question/Canonical ownership as frozen by the batch inventory

## Decisions

### `cq_q_a7016342ea74a55c817ed58e69009a64` — fail closed / source-unrecoverable

Preserved wording: `算法实现：给定原数组为 [a...z]，编写一个简单的 Hash 算法将其映射为新的整数数组？`

The repository preserves neither a hash-table size/modulus nor a required hash function, output length, collision rule, expected mapped values, samples, or correctness oracle. Several materially different contracts fit the same wording: ordinal encoding (`a -> 0` ... `z -> 25`), a polynomial/string hash modulo an arbitrary integer, Java-style hash values, or bucket indices with a collision policy. These are not interchangeable, and ordinal encoding is not even a hash in the collision-oriented sense normally meant by a hash-table exercise.

`note_desc/67d25ca8000000000b017d2a.txt` contains only the post caption and adds no missing algorithm contract. `note_tagged` and `note_structured` repeat the same normalized wording; they do not recover an executable oracle. Therefore a strict-valid Coding answer cannot choose one mapping without fabricating the original task. The safe next action is to retire this singleton with an explainable `incomplete_or_unreadable` decision, preserving the archived baseline but removing active Canonical/Answer/ReviewProgress reachability.

### `cq_q_a791750e006147b75dcb2c13b7fa90e9` — recoverable as Scenario

Preserved wording: `场景题：从两个包含上亿 URL 的大文件中找出重复 URL（布隆过滤器/哈希切分）？`

The objective is recoverable: identify URLs present in both very large files under memory pressure. Exact RAM/disk limits are not preserved, so a candidate must label capacity numbers as assumptions rather than source facts. The current source inventory resolves `answer_type=scenario`; the task file's older `coding` hint must not override this SSOT.

A source-bounded candidate may explain exact external hash partitioning as the correctness-preserving path and Bloom filters only as a probabilistic prefilter/negative filter unless false-positive handling is explicitly resolved. It must cover partition skew/hot buckets, duplicate rows within each file, disk I/O, collision-safe equality checking, and a verification fixture using deterministic partitions.

### `cq_q_a7ba6548994bab4e4412f98bf4a8dee2` — recoverable as Coding with explicit API boundary

Preserved wording: `算法：实现 setInterval 和 clearInterval`

The requested API pair is clear enough to implement a bounded JavaScript polyfill. Runtime-specific timer precision, event-loop scheduling guarantees, argument forwarding, `this` binding, numeric-handle compatibility, and reentrancy semantics are not source-preserved and must not be presented as required behavior.

A strict candidate can define a minimal contract: schedule repeated callback attempts via recursive `setTimeout`, return an opaque handle, and make `clearInterval(handle)` prevent future scheduling; clear-before-first-fire and clear-from-inside-callback require deterministic tests. It must explicitly state that it is not a byte-for-byte browser/Node timer specification implementation and cannot guarantee exact wall-clock intervals.

### `cq_q_a811de1b146bd3b47f2f7ca524ac1c3b` — recoverable as Coding

Preserved wording: `算法：手撕去重链表（Remove Duplicates from Sorted List），使用双指针实现。`

The sorted-list precondition and the named problem identity provide a recoverable contract: collapse adjacent equal values while retaining one node from each run. The candidate must not silently switch to the `Remove Duplicates from Sorted List II` contract, which removes all duplicated values. It should state node shape and null-input behavior as local implementation assumptions and verify empty, singleton, all-equal, head/middle/tail duplicates, and already-unique lists.

### `cq_q_a873b7b82bcca35bc35609aa914b70c9` — recoverable as Coding with declared digit assumption

Preserved wording: `算法 1：计算二叉树中根节点到叶子节点路径所组成的数字之和`

The operation is recoverable: concatenate node values along each root-to-leaf path and sum the resulting numbers. The source does not explicitly preserve the node-value range; a candidate may use the standard minimal assumption that each node stores one decimal digit `0..9`, but must label that as an assumption because multi-digit or negative node values change the concatenation rule. Verification must include a single node, asymmetric tree, leading zero, and multiple leaves, and should use `long` or state overflow limits rather than silently relying on `int`.

### `cq_q_a9a3cdad804b0bdf8732d7d22dcb03c2` — recoverable as Coding

Preserved wording: `算法：自实现堆结构并完成堆排序 (从大到小排列)`

The output order is explicit. A candidate must actually implement heap operations rather than delegate to a library sort/priority queue. Either a min-heap that repeatedly emits the minimum into the array from right to left or a max-heap with a final reversal can satisfy descending order, provided the invariant is stated and verified. The candidate must cover duplicates, negative numbers, already sorted/reverse-sorted input, and empty/singleton arrays, and distinguish heap construction complexity from repeated sift operations.

### `cq_q_aa5412e581a46db5a2dbf3f5bc6262eb` — recoverable, but keep problem-identity boundary explicit

Preserved wording: `算法：手撕螺旋矩阵（Spiral Matrix）。`

The parenthetical problem identity is the strongest surviving signal and supports the standard spiral traversal interpretation; the repository does not preserve a separate `Spiral Matrix II`/matrix-generation requirement. A candidate must therefore say explicitly that it is answering traversal of a provided matrix, not generation of an `n x n` matrix. Rectangular matrices, one row/column, empty input, and the shrinking-boundary termination condition require tests. If stronger raw source later shows a generation task, this decision must be reopened instead of force-fitting the traversal answer.

## Batch consequence

- Already retired fail-closed: `cq_q_a6ed4f0f01d44463de7f8af046ccd001`, `cq_q_a70af552af23eb909cd728cbd46fdbac`.
- Already source-first reviewed candidate: `cq_q_a735fdca7e7f00dbb5349db43e5f3987`.
- Newly classified fail-closed: `cq_q_a7016342ea74a55c817ed58e69009a64`; remediation must update validity projection, Canonical, active baseline Answer, ReviewProgress, generated indexes/manifests, and all repository gates atomically.
- Candidate drafting may safely proceed for `cq_q_a791750e006147b75dcb2c13b7fa90e9`, `cq_q_a7ba6548994bab4e4412f98bf4a8dee2`, `cq_q_a811de1b146bd3b47f2f7ca524ac1c3b`, `cq_q_a873b7b82bcca35bc35609aa914b70c9`, `cq_q_a9a3cdad804b0bdf8732d7d22dcb03c2`, and `cq_q_aa5412e581a46db5a2dbf3f5bc6262eb` using the boundaries above.

This review does not itself promote, retire, or mutate any Canonical. Promotion still requires candidate evidence, executable/type-appropriate validation, isolated review, and the repository's current human/S11 gates.