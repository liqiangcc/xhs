# Answer Batch 0019 — Source-First Boundary Audit

## Scope

- Batch: `TASK-20260711-0313-answer-batch-0019`
- Original Canonicals reviewed: `10/10`
- Repository source packet: `review/reports/ANSWER_BATCH_0019_SOURCE_PACKET.{json,md}`
- Policy: repository source first; do not import unstated problem contracts, algorithm identities, complexity requirements, language/runtime choices, schemas, or personal facts.
- Initial disposition: `4` original Canonicals were candidate-qualified and `6` required normalization/source remediation.
- Post-remediation disposition: all `6` source-boundary blockers are resolved. `4` source-unrecoverable singleton Canonicals are retired with explicit `incomplete_or_unreadable` decisions; equal-sum is normalized and candidate-qualified; the merged tree/sequence Canonical is retired and split into `2` source-exact descendants. The downstream answerable set is therefore `7` active source-supported Canonicals.

## Decisions

### `cq_q_2d3c2cbca1d43c2ab3acad0e91726695` — candidate-qualified

Repository source explicitly records `给两个树判断是否相等`. A candidate may implement structural/value equality, but must label the concrete node/value/null API as an implementation assumption rather than an original-prompt fact. It must not add BST-specific, serialization, balancing, or identity semantics.

### `cq_q_2dcc4ae8850241c339c211516c55b307` — retired source-first

Repository source records `给一个shell脚本(遍历目录)，用java实现相关功能`, but the actual Shell script is absent. The legacy Canonical title turned the parenthetical into a complete recursive-directory-traversal contract even though source does not preserve traversal order, filters, symlink behavior, output, errors, or the script body. The singleton Question is therefore explicitly excluded as `incomplete_or_unreadable`; its placeholder Answer and ReviewProgress are retired rather than inventing an equivalent Java program.

### `cq_q_2e11155d7a78e8fda6758fc98aa44029` — retired source-first

The strongest repository source says only `一道sql`; no schema, rows, requested result, dialect, constraints, or query text is preserved. `SQL 实操题。` cannot support a strict-valid answer. The singleton Question is explicitly excluded as `incomplete_or_unreadable`, and stale Answer/ReviewProgress ownership is retired rather than inventing a SQL exercise.

### `cq_q_2e26508950e5da505c44621129f41a26` — retired and split source-first

Repository source lists two separate hand-written tasks: `二叉树路径和` and `最长连续序列长度`. The merged Canonical is retired and replaced by `cq_q_84bd83ff8f06510515f6b71534cd2ac5` and `cq_q_2a5006d66e022875a36106ef0c25c2c2`, using those source-exact titles only. The repository does not support silently adding `LeetCode 437`, target-value/path-count semantics, `HashSet`, `O(N)`, or a concrete API contract. Each descendant may proceed to candidate generation only with any missing semantics clearly labeled as implementation assumptions.

### `cq_q_2f07ba5f8d6e6ad366d2cd13c6d1d1ab` — candidate-qualified

Repository source explicitly records `手撕代码（真手撕）：无向图的深拷贝`. A candidate may implement graph cloning with a visited/original-to-clone map. Concrete node fields, language, entry-point shape, and null handling must be identified as implementation assumptions. Do not silently replace the task with an unrelated generic object deep-copy problem.

### `cq_q_2f278e6b489feb680f8b173047815566` — normalized; candidate-qualified

Repository source says `给一个数组判断能否拆成两个数组，这两个数组的元素和相等`. The Question and Canonical are normalized to that recoverable partition/group meaning, and the misleading contiguous `子数组` wording is removed. A candidate may now implement equal-sum partition, but input constraints, non-empty-group requirements, integer sign/range, and concrete API remain implementation assumptions unless separately sourced.

### `cq_q_2f351e2a49d14ad9643e8daed49006b0` — candidate-qualified

Caption and image transcript both preserve `将堆抽象成类，实现获取元素、删除元素等的操作方法`. A candidate may define a small heap class and demonstrate retrieval/deletion while explicitly declaring min-vs-max heap, constructor/input type, duplicate handling, and empty-heap behavior as implementation choices. Those choices are not source facts.

### `cq_q_2fcd783bcefb0f3ab525b18afe3a7591` — candidate-qualified

Image transcript explicitly records `手写Promise.all的实现` and includes an array-oriented reference implementation. A candidate can be source-bounded to that interview task. If it implements full ECMAScript iterable semantics instead of the source's array-oriented form, that must be labeled as a deliberate spec-completeness extension, not as recovered prompt text. Order preservation, empty input, value assimilation, and first rejection must be tested.

### `cq_q_3022a886d714c0fc8bc2fa4d0b7812a5` — retired source-first

Repository source preserves only `深拷贝` in a front-end interview list. It does not preserve language, supported data types, cycles, prototypes/descriptors, collection types, functions, or the expected API. A production-like JavaScript deep-clone contract would therefore be invented. The singleton Question is explicitly excluded as `incomplete_or_unreadable`, and its placeholder Answer/ReviewProgress are retired.

### `cq_q_3022eb4f8a66f69b09a2d019164f0bb5` — retired source-first

Repository narrative says `最长回文序列`, reports an `O(n^2)` implementation, and then says a second approach used `马拉车算法`. The legacy Canonical expanded this to **longest palindromic subsequence** while also asking for Manacher. That combination is technically inconsistent: Manacher addresses contiguous palindromic substrings, not the longest palindromic subsequence problem. The source may be using `序列` colloquially for a substring, but repository evidence is insufficient to choose that interpretation silently. The singleton Question is therefore explicitly excluded as `incomplete_or_unreadable`, with stale Answer/ReviewProgress retired rather than authoring against a mixed contract.

## Post-remediation answerable descendants

The retired merged source record yields two active source-exact Canonicals not present as separate records in the frozen original packet:

- `cq_q_84bd83ff8f06510515f6b71534cd2ac5` — `二叉树路径和`; source supports the title only. Target semantics, whether the result is existence/count/paths, path direction, node type, language, and API must be explicit candidate assumptions unless separately sourced.
- `cq_q_2a5006d66e022875a36106ef0c25c2c2` — `最长连续序列长度`; source supports the title only. What constitutes continuity, input type, duplicate handling, complexity target, language, and API must be explicit candidate assumptions unless separately sourced.

## Gate

No formal answer is promoted by this audit. Source normalization/remediation is complete for the original batch boundary. Candidate generation is allowed for the `7` active source-supported Canonicals: `cq_q_2d3c2cbca1d43c2ab3acad0e91726695`, `cq_q_2f07ba5f8d6e6ad366d2cd13c6d1d1ab`, `cq_q_2f278e6b489feb680f8b173047815566`, `cq_q_2f351e2a49d14ad9643e8daed49006b0`, `cq_q_2fcd783bcefb0f3ab525b18afe3a7591`, `cq_q_84bd83ff8f06510515f6b71534cd2ac5`, and `cq_q_2a5006d66e022875a36106ef0c25c2c2`. Each candidate still requires bound evidence, deterministic code validation where applicable, isolated source-first review, the repository's required human approval, formal audit, and atomic promotion. The `4` retired source-unrecoverable records must not re-enter answer generation without newly recovered source evidence.
