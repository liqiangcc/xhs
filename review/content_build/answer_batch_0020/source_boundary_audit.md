# Answer Batch 0020 — source-first boundary audit

## Audit rule

This audit was formed from `review/reports/ANSWER_BATCH_0020_SOURCE_PACKET.{json,md}` before reading or relying on the existing long-tail Answer bodies. Repository caption/image-transcript material is authoritative for what the original interview source actually preserves. Structured/tagged wording and existing Canonical wording are treated as derived data that must not silently strengthen the source. No external problem statement is imported at this stage.

A `candidate-qualified` disposition means the repository source preserves enough of the task to research and write a candidate **provided every missing language/API/edge-case choice is labelled as a candidate assumption**. `normalization-required` means the Canonical currently asserts source detail that the repository source does not preserve. `source-unrecoverable` means the surviving repository source is too incomplete or ambiguous to support a faithful executable coding contract without invention.

## Dispositions

### `cq_q_314a8ebf7f22e3845454fb724d41ed16` — candidate-qualified

- Source: `note_img_txt/67d8d9fc00000000090144c3.txt` explicitly lists “实现一个函数防抖的TypeScript版本” and also preserves a TypeScript debounce reference implementation.
- Preserved contract: TypeScript, debounce/high-order function, delayed execution semantics; the source reference additionally exposes an `immediate` option.
- Boundary: exact public type signature, timer environment (`number` vs `ReturnType<typeof setTimeout>`), cancellation/flush methods, error handling, and whether `immediate` is mandatory are not source requirements unless the candidate explicitly labels them as implementation choices.
- Disposition: source-supported; candidate may proceed after primary-source research for TypeScript/JavaScript timing semantics.

### `cq_q_32099ab899a15a5d7ab610c1477860e1` — normalization-required, then candidate-qualified

- Source: `note_desc/67432048000000000703084c.txt` preserves “非递归且不用额外空间(不用栈)，如何遍历二叉树”.
- Preserved contract: binary-tree traversal, non-recursive execution, no auxiliary stack/extra traversal structure.
- Derived wording to remove from the source contract: the parenthetical solution label “(Morris遍历)” is present in the tagged/Canonical record but not in the retained interview caption. Morris traversal is a valid researched solution technique, not recovered prompt text.
- Boundary: traversal order is not specified in the source. A candidate must not silently assume only inorder/preorder/postorder; it should state which order(s) it demonstrates and explain the temporary-threading/restoration invariant.
- Disposition: remove the inferred solution label from Canonical/source wording before candidate promotion; the underlying task remains answerable.

### `cq_q_32261275f6fd11df329bd168116d64b1` — candidate-qualified

- Source: `note_desc/6668516a000000000e033155.txt` explicitly preserves “先升序后降序的数组排序”.
- Preserved contract: input is a bitonic/unimodal sequence with one nondecreasing/upward portion followed by one nonincreasing/downward portion; produce sorted output.
- Boundary: source does not state element type, duplicate policy, strict-vs-nonstrict monotonicity, ascending-vs-descending desired output, in-place requirement, or language/API. Those choices must be stated and tested rather than attributed to the interview source.
- The image transcript for this note is a failed OCR/tool message and contributes no problem detail.
- Disposition: source-supported; candidate may proceed with explicit assumptions and executable tests.

### `cq_q_3238f5e15ec86e90f7f1a8560c854d9a` — candidate-qualified

- Source: `note_desc/663b7649000000001e038251.txt` preserves “10进制转换其他进制”; the image transcript repeats that wording.
- Preserved contract: convert a decimal value to another radix representation.
- Boundary: target radix range, digit alphabet above 9, negative values, zero, integer-only vs fractional values, overflow policy, and API/language are not preserved. The candidate must choose and state a bounded contract (for example integer values and radix 2–36) rather than claim it was in the source.
- Disposition: source-supported under explicit candidate assumptions.

### `cq_q_3395e0de3268979e86446a8ad2eebb4b` — normalization-required

- Source: `note_desc/68a3331f000000001b022d68.txt` preserves only “编程 / 分发糖果”.
- Unsupported Canonical strengthening: “力扣 135” is present in the tagged/Canonical record but is not present in the retained repository interview caption. The familiar title is not sufficient evidence to import a numbered external problem contract source-first.
- Boundary: ratings array semantics, neighbor rule, minimum-one-candy rule, objective, input/output and complexity target are absent from the repository source.
- Disposition: the current Canonical is not candidate-qualified as written. Normalize it to the source-preserved “分发糖果” wording first. After normalization, external primary research may be used only if the evidence policy explicitly justifies mapping the source title to a concrete problem contract; otherwise keep it non-promotable rather than inventing details.

### `cq_q_339b8eac64f281ce9f9ff7268db622ba` — candidate-qualified

- Source: `note_desc/6892d5250000000023020667.txt` explicitly preserves “给你一个图的邻接矩阵 / 请你对这个图进行深度优先遍历”.
- Preserved contract: adjacency-matrix graph representation and depth-first traversal.
- Boundary: directed/undirected semantics, start vertex, disconnected-component coverage, vertex numbering, matrix value meaning, traversal-order tie-breaking, recursion-vs-explicit-stack requirement and API/language are unspecified. These must be explicit implementation choices.
- The image transcript is only a cover-image summary and contributes no additional algorithm contract.
- Disposition: source-supported; candidate may proceed with a clearly bounded matrix/vertex contract and deterministic tests.

### `cq_q_33d091345ac48812c61f235d00515560` — source-unrecoverable as a coding contract

- Source: `note_desc/67f0ff86000000001c0283b9.txt` preserves “找到最长的区间火柴拼成一个三角形”, notes a sliding-window implementation, and records a follow-up “如果可以打乱顺序怎么优化（排序）”.
- Unsupported Canonical strengthening: the current Canonical adds “给定一个火柴长度数组”, “等边或普通三角形”, and “最长周长”. The retained source does not say that the objective is perimeter, does not define whether every stick in an interval must be used, and does not preserve the exact validity/input/output contract.
- The associated image transcript is a failed image-recognition/tool message and provides no missing problem statement.
- Why fail closed: several materially different algorithms are consistent with the surviving summary. Choosing one would fabricate the interview contract and make an executable test suite look more authoritative than the evidence permits.
- Disposition: mark this singleton source question `incomplete_or_unreadable` / source-unrecoverable unless a stronger repository-local source is later recovered. Do not author a candidate from the current Canonical wording.

### `cq_q_349bf213858328393da46111a614d286` — candidate-qualified

- Source: `note_desc/67dd34b2000000001d021316.txt` explicitly preserves “算法lc49，用的哈希表，问还有什么其他方法”. The image transcript repeats the same interview item.
- Preserved contract: LeetCode 49 / Group Anagrams plus a follow-up asking for approaches other than the interviewee's hash-table solution.
- Boundary: implementation language and which alternative technique the interviewer expected are not preserved. External primary problem evidence may define the LeetCode contract; the candidate should distinguish baseline grouping from alternative key-generation strategies instead of pretending a single “optimization” was required.
- Disposition: source-supported; candidate may proceed with official problem-statement evidence and implementation tests.

### `cq_q_3523542f7ad2ae207715d1fb093c861f` — candidate-qualified

- Source: `note_desc/68caa7b0000000000e02205d.txt` explicitly preserves: a length-`m` circular sequence of balls with `n` colors; find the minimum continuous ball sequence containing all `n` colors; use two pointers.
- Preserved contract: circular sequence, all-color coverage, minimum contiguous window, two-pointer/sliding-window approach.
- Boundary: color representation, indexing, return shape (length vs indices/subsequence), whether every declared color is guaranteed to appear, tie-breaking, and API/language are not preserved. These must be candidate choices and boundary tests.
- Disposition: strongly source-supported; candidate may proceed.

### `cq_q_3534d96489fb54811065d18d51bf1e5b` — candidate-qualified with ordered-child assumption required

- Sources: `note_desc/656de8b6000000001502f038.txt` identifies the Pinduoduo coding round; `note_img_txt/656de8b6000000001502f038.txt` preserves the pair-list example `[(1,4),(3,5),(1,3),(5,2)]`, states that each pair is parent→child, asks to build a binary tree, and asks for preorder traversal.
- Preserved contract: construct a binary tree from parent-child pairs and traverse it preorder.
- Boundary: the source does not define a general left/right-child encoding, root-discovery rule for malformed/multiple-root input, duplicate edges, cycles, >2 children, or API/language. The pictured example is also insufficient to generalize left/right semantics for every possible input.
- Candidate requirement: state an ordering convention (for example, children are attached in first-seen input order) as an implementation choice and validate/decline malformed inputs rather than presenting the convention as source fact.
- Disposition: source-supported under an explicit ordered-child/API contract.

## Batch boundary result

- Source-hit coverage: `10/10` Canonicals have at least one repository-owned source hit.
- Candidate-qualified without Canonical normalization: `7` (`314a…`, `3226…`, `3238…`, `339b…`, `349b…`, `3523…`, `3534…`).
- Normalization required before promotion: `2` (`3209…` removes inferred “Morris遍历” from source wording; `3395…` removes unsupported “力扣 135” unless independently justified after normalization).
- Source-unrecoverable coding contract: `1` (`33d0…` fire-match/triangle summary).
- No candidate should be authored for a normalization/source-unrecoverable record until its disposition is applied to Canonical/Question validity state and the normal repository integrity gates pass.

## Applied remediation

- `cq_q_32099ab899a15a5d7ab610c1477860e1`: normalized to the repository-preserved wording “非递归且不用额外空间(不用栈)，如何遍历二叉树”; the Canonical remains stable while Question ownership moves to the normalized Question hash. “Morris遍历” is now treated only as a researched solution technique.
- `cq_q_3395e0de3268979e86446a8ad2eebb4b`: after fail-closed recheck, retired as source-unrecoverable. “分发糖果” alone does not uniquely justify importing LeetCode 135 semantics.
- `cq_q_33d091345ac48812c61f235d00515560`: retired as source-unrecoverable for the ambiguity already documented above.

Post-remediation answerable set: `8` active source-supported Canonicals. No source-boundary blocker remains for those eight; candidate work must still preserve each record's explicit assumptions and evidence gates.
