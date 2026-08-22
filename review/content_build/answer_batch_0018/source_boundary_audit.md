# Answer Batch 0018 — Source Boundary Audit

Date: 2026-08-23

This audit is intentionally source-first. It is based on `review/reports/ANSWER_BATCH_0018_SOURCE_PACKET.{json,md}` plus the repository-local caption/image-transcript sources referenced by that packet. It records only contracts recoverable from those sources before candidate generation. Familiar online-judge names, inferred schemas, implementation languages, or algorithm templates are not treated as source facts. This audit covers **10/10 Canonicals** in answer batch 0018 and performs **no formal promotion**.

## `cq_q_28ddc5240672730f91363131ba8cc14e`

- Source: `note_desc/68c2c62e000000001b01d168.txt` plus matching tagged/canonical records.
- Raw wording/context: the retained note says only `6.1模式匹配` as one of two coding questions.
- Source-widening finding: the current Question/Canonical expands this to `字符串模式匹配（Pattern Matching）`, but the repository source does not identify substring search, wildcard matching, regular-expression matching, KMP, a pattern syntax, inputs, outputs, examples, or constraints.
- Boundary result: **not recoverable enough for a strict coding answer**. Multiple materially different problems fit the phrase `模式匹配`.
- Required remediation: recover a stronger source that identifies the matching semantics. If none exists, classify the Question as ambiguous/incomplete and retire or remap the unsupported singleton Canonical through the supported normalization flow. Do not choose KMP/regex/wildcards by familiarity.
- Disposition: `normalization_and_question_remediation_required_ambiguous_pattern_matching`.

## `cq_q_294cb4b4464c886329fda6efb26f3d5a`

- Source: `note_img_txt/6678d3f7000000001e013539.txt` is the strongest retained source; `note_desc/6678d3f7000000001e013539.txt` contains only the caption/hashtags.
- Raw wording/context: the image transcript says `两个无序链表如何找出其值相等的节点,两个链表不相交`.
- Boundary result: **recoverable at the algorithm-goal level**. The two lists are unordered and structurally non-intersecting; matching is by node value rather than node identity.
- Missing source details: value type, whether duplicate values can occur, whether the expected result is the first matching pair, all matching nodes, all common values, or merely existence, and the required language/API are not stated.
- Required candidate boundary: choose and label one concrete result API, preserve the distinction between equal values and intersecting nodes, state duplicate semantics explicitly, and validate the hash-based approach against a simple nested-loop oracle. Do not silently reinterpret the task as the classic linked-list intersection problem.
- Disposition: `candidate_allowed_with_explicit_result_and_duplicate_semantics`.

## `cq_q_297402fd71887dbeb07d182f057a1858`

- Source: `note_desc/68ca2ddb0000000013011bbb.txt` plus matching tagged/canonical records.
- Raw wording/context: the retained note says only `算法：大数相乘`.
- Boundary result: **recoverable as arbitrary-precision multiplication, with representation choices missing**.
- Missing source details: decimal versus another base, sign handling, leading-zero policy, whether built-in big integers are forbidden, input size, return type, and implementation language are not stated. The English label `Multiply Strings` is not present in the raw source.
- Required candidate boundary: if using the conventional decimal-string formulation, mark it explicitly as the candidate API choice; handle zero and leading zeros deterministically; avoid built-in arbitrary-precision multiplication in the implementation being demonstrated; prove the digit-accumulation/carry invariant; and differential-test small/random cases against an independent numeric oracle.
- Disposition: `candidate_allowed_with_explicit_decimal_string_api_assumption`.

## `cq_q_2979c00d6ff6c1582ecb289775522412`

- Source: `note_desc/6822deb7000000002100178b.txt` plus matching tagged/canonical records.
- Raw wording/context: the retained note says `SQL题：找 出 最 长 连 续 子 序 (row_number)`.
- Source-widening finding: the current Question/Canonical adds `一个用户` and `连续登录天数`, but neither a login table nor a user/date schema appears in the raw source.
- Boundary result: **the technique family is recoverable, but the concrete SQL contract is not**. `row_number` and “longest consecutive subsequence” point to a gaps-and-islands style task, but the partition key, ordering column, continuity unit, duplicate policy, and expected output are absent.
- Required remediation: remove the unsupported login-specific wording unless a stronger source is recovered. Before authoring SQL, compare this Canonical with `cq_q_2bd82e0bd4203f85f02cca39fb7a67e2`, which is another under-specified `最大连续` SQL source in the same batch. Normalize/merge only if source comparison shows that one generic Canonical can truthfully represent both; otherwise keep the missing schemas explicit.
- Disposition: `normalization_review_required_source_widening_and_possible_duplicate`.

## `cq_q_29ea4b45d754e65e5837153e52ba2abd`

- Source: `note_desc/68b940e2000000001d00c624.txt` plus matching tagged/canonical records.
- Raw wording/context: `编码测试：多线程场景下的转账功能实现`.
- Boundary result: **recoverable as a concurrent in-memory transfer design/coding problem**. Atomic account updates and deadlock avoidance are relevant correctness concerns, but the raw source itself does not prescribe a synchronization primitive or an account API.
- Missing source details: account representation, insufficient-funds behavior, self-transfer, transfer amount constraints, lock primitive, interruption/error policy, transaction durability, and whether the task is purely in-memory or backed by external storage are not stated.
- Required candidate boundary: choose and label an in-memory account contract, update debit/credit within one critical section spanning both accounts, acquire per-account locks in a deterministic total order (or use another demonstrably deadlock-free strategy), define invalid/self/insufficient-funds behavior, and stress-test conservation plus progress under opposing concurrent transfers. Do not claim database/distributed-transaction semantics from this source.
- Disposition: `candidate_allowed_with_explicit_in_memory_transfer_contract`.

## `cq_q_2a09d0d7980006e66439a361880bc83d`

- Source: `note_desc/68cbd296000000000e00c123.txt` plus matching tagged/canonical records.
- Raw wording/context: `用面向对象的思想写一个solution，实现一个功能：输入一个字符串，输出所有字符组合` followed by `写出这个类的拷贝构造、移动构造、拷贝赋值、移动赋值`.
- Source-widening finding: the current Question/Canonical says `字符串全排列组合`, but the raw source says `所有字符组合` and does **not** say permutation/full permutation. The follow-up asks for copy/move construction and assignment, which is C++-specific object-semantics terminology; the current primary domain metadata is Java-oriented.
- Boundary result: **normalization is required before answer generation**. Treating the task as “all permutations” would fabricate a key semantic choice, and answering the copy/move follow-up as Java would contradict the source language signal.
- Required remediation: correct the Question/Canonical wording to the source-supported “all character combinations” only if the intended combination semantics can be recovered; otherwise classify the combinatorial contract as incomplete. Preserve the C++ copy/move follow-up as a separate source requirement or split it into a linked Canonical if the repository model requires one coherent answer goal.
- Disposition: `normalization_required_combination_vs_permutation_and_cpp_object_semantics`.

## `cq_q_2a97bfeb868fc672fcabeb1182608de4`

- Source: `note_desc/67e7d5c3000000000900da5a.txt` plus matching tagged/canonical records.
- Raw wording/context: the retained question list contains `17. 二叉树右视图`.
- Boundary result: **recoverable as the binary-tree right-side-view task**, with API details missing.
- Missing source details: node/value type, empty-tree behavior, recursive versus iterative expectation, return type, and whether only values or node identities are required are not stated.
- Required candidate boundary: choose and label a standard tree/value API, return one visible value per depth, explain either level-order “last node per level” or right-first DFS “first node per depth” invariant, and differential-test both strategies over generated trees including empty/skewed/duplicate-value cases.
- Disposition: `candidate_allowed_with_explicit_tree_api_assumptions`.

## `cq_q_2bd82e0bd4203f85f02cca39fb7a67e2`

- Source: `note_desc/689d4879000000001c008cde.txt` plus matching tagged/canonical records.
- Raw wording/context: the retained note says only `SQL:最大连续问题`.
- Source-widening finding: the tagged/current Question expands this into `最大连续天数/次数`, `Max Consecutive Days`, `ROW_NUMBER自减抵消法`, user activity/sign-in context, and even metadata such as `递归cte`; none of those details are present in the raw source.
- Boundary result: **not recoverable enough for a strict SQL answer in its current form**. No tables, columns, partition key, order key, continuity unit, duplicate policy, or expected projection survive in the raw source.
- Required remediation: remove unsupported schema/algorithm/context additions unless a stronger source is recovered. Compare with `cq_q_2979c00d6ff6c1582ecb289775522412` before deciding whether both belong to one generic gaps-and-islands Canonical; do not create two strict answers from two under-specified variants merely because the tagged records chose different wording.
- Disposition: `normalization_and_question_remediation_required_under_specified_sql_possible_duplicate`.

## `cq_q_2c267f2f448a08e8b1f1e1590ce6df72`

- Source: `note_desc/6842998a000000000303f15c.txt` plus matching tagged/canonical records.
- Raw wording/context: `判断树B是否是树A的子结构 ：输入两颗二叉树，判断B是否是A的子结构`.
- Boundary result: **recoverable**. The source preserves the two-tree input and the substructure predicate goal.
- Missing source details: node/value type, whether an empty B counts as a substructure, whether equality is value-based, recursion-depth constraints, and required language/API are not stated. The canonical metadata entity `二分查找` is not supported by the raw task and should not drive the implementation.
- Required candidate boundary: state the empty-tree/value-equality contract explicitly; search possible matching roots in A and recursively match B while allowing A to contain extra descendants after B is exhausted; test repeated values, skewed trees, root-only matches, nonmatches, and the chosen empty-B policy against an independent brute-force matcher.
- Disposition: `candidate_allowed_with_explicit_empty_tree_and_value_semantics`.

## `cq_q_2d08f15b8ffa1ba609ca2b53d287984e`

- Source: `note_desc/666c3aee000000000e03140b.txt` plus matching tagged/canonical records.
- Raw wording/context: `二叉树中序遍历`.
- Boundary result: **recoverable as binary-tree inorder traversal**, with API details missing.
- Missing source details: recursive versus iterative implementation, node/value type, empty-tree behavior, output container, recursion-depth expectations, and mutation policy are not stated.
- Required candidate boundary: choose and label a tree/value API, define empty input, explain the left-root-right invariant, preferably show both recursive and explicit-stack iterative forms while making one the tested reference implementation, and differential-test them over generated trees without mutating input.
- Disposition: `candidate_allowed_with_explicit_tree_api_assumptions`.

## Batch disposition

The source-first pass covers all 10 Canonicals in batch 0018:

- source-qualified candidate path with explicit boundaries: `cq_q_294cb4b4464c886329fda6efb26f3d5a`, `cq_q_297402fd71887dbeb07d182f057a1858`, `cq_q_29ea4b45d754e65e5837153e52ba2abd`, `cq_q_2a97bfeb868fc672fcabeb1182608de4`, `cq_q_2c267f2f448a08e8b1f1e1590ce6df72`, `cq_q_2d08f15b8ffa1ba609ca2b53d287984e`;
- normalization / Question remediation before answer generation: `cq_q_28ddc5240672730f91363131ba8cc14e`, `cq_q_2979c00d6ff6c1582ecb289775522412`, `cq_q_2a09d0d7980006e66439a361880bc83d`, `cq_q_2bd82e0bd4203f85f02cca39fb7a67e2`.

Counts do not complete the batch. No candidate is promoted by this audit. Candidate-path items still require candidate content, schema-valid evidence, isolated source-first review, executable validation where applicable, and the repository's human/promotion gates. Remediation items must first be normalized against the Question/Canonical SSOT so that strict content closure does not preserve fabricated schemas, widened problem statements, or duplicate concepts.