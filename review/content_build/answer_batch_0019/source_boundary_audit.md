# Answer Batch 0019 — Source-First Boundary Audit

## Scope

- Batch: `TASK-20260711-0313-answer-batch-0019`
- Canonicals reviewed: `10/10`
- Repository source packet: `review/reports/ANSWER_BATCH_0019_SOURCE_PACKET.{json,md}`
- Policy: repository source first; do not import unstated problem contracts, algorithm identities, complexity requirements, language/runtime choices, schemas, or personal facts.
- Result: `4` Canonicals are candidate-qualified with explicit implementation assumptions; `6` require normalization/source remediation before candidate generation.

## Decisions

### `cq_q_2d3c2cbca1d43c2ab3acad0e91726695` — candidate-qualified

Repository source explicitly records `给两个树判断是否相等`. A candidate may implement structural/value equality, but must label the concrete node/value/null API as an implementation assumption rather than an original-prompt fact. It must not add BST-specific, serialization, balancing, or identity semantics.

### `cq_q_2dcc4ae8850241c339c211516c55b307` — remediation required

Repository source records `给一个shell脚本(遍历目录)，用java实现相关功能`, but the actual Shell script is absent. The current Canonical title turns the parenthetical into a complete recursive-directory-traversal contract even though source does not preserve traversal order, filters, symlink behavior, output, errors, or the script body. Do not fabricate an equivalent Java program. Recover the script or normalize/explain the record as source-incomplete.

### `cq_q_2e11155d7a78e8fda6758fc98aa44029` — source-unrecoverable as an answerable coding question

The strongest repository source says only `一道sql`; no schema, rows, requested result, dialect, constraints, or query text is preserved. `SQL 实操题。` cannot support a strict-valid answer. This row needs an explicit source-incomplete/noise-or-unrecoverable disposition rather than an invented SQL exercise.

### `cq_q_2e26508950e5da505c44621129f41a26` — split/normalization required

Repository source lists two separate hand-written tasks: `二叉树路径和` and `最长连续序列长度`. The current Canonical combines them into one question and adds `LeetCode 437`, `O(N)`, and `HashSet` details that are not present in the repository source. Split or otherwise remediate the ownership boundary before authoring either answer; do not preserve the unsupported embellishments as source facts.

### `cq_q_2f07ba5f8d6e6ad366d2cd13c6d1d1ab` — candidate-qualified

Repository source explicitly records `手撕代码（真手撕）：无向图的深拷贝`. A candidate may implement graph cloning with a visited/original-to-clone map. Concrete node fields, language, entry-point shape, and null handling must be identified as implementation assumptions. Do not silently replace the task with an unrelated generic object deep-copy problem.

### `cq_q_2f278e6b489feb680f8b173047815566` — normalization required

Repository source says `给一个数组判断能否拆成两个数组，这两个数组的元素和相等`. The current title says `两个和相等的子数组`, which can imply contiguous subarrays and therefore narrows the problem beyond the source. Normalize the contract to the recoverable partition/group meaning, or retain the ambiguity explicitly; do not choose contiguous-subarray semantics without evidence.

### `cq_q_2f351e2a49d14ad9643e8daed49006b0` — candidate-qualified

Caption and image transcript both preserve `将堆抽象成类，实现获取元素、删除元素等的操作方法`. A candidate may define a small heap class and demonstrate retrieval/deletion while explicitly declaring min-vs-max heap, constructor/input type, duplicate handling, and empty-heap behavior as implementation choices. Those choices are not source facts.

### `cq_q_2fcd783bcefb0f3ab525b18afe3a7591` — candidate-qualified

Image transcript explicitly records `手写Promise.all的实现` and includes an array-oriented reference implementation. A candidate can be source-bounded to that interview task. If it implements full ECMAScript iterable semantics instead of the source's array-oriented form, that must be labeled as a deliberate spec-completeness extension, not as recovered prompt text. Order preservation, empty input, value assimilation, and first rejection must be tested.

### `cq_q_3022a886d714c0fc8bc2fa4d0b7812a5` — remediation required

Repository source preserves only `深拷贝` in a front-end interview list. It does not preserve language, supported data types, cycles, prototypes/descriptors, collection types, functions, or the expected API. A production-like JavaScript deep-clone contract would therefore be invented. Recover/normalize the intended scope before candidate generation.

### `cq_q_3022eb4f8a66f69b09a2d019164f0bb5` — semantic-conflict remediation required

Repository narrative says `最长回文序列`, reports an `O(n^2)` implementation, and then says a second approach used `马拉车算法`. The current Canonical expands this to **longest palindromic subsequence** while also asking for Manacher. That combination is technically inconsistent: Manacher addresses contiguous palindromic substrings, not the longest palindromic subsequence problem. The source may be using `序列` colloquially for a substring, but the repository evidence is insufficient to choose that interpretation silently. Normalize the question only after resolving the conflict; do not author against the current mixed contract.

## Gate

No formal answer is promoted by this audit. Candidate generation is allowed only for the four candidate-qualified Canonicals above, and each candidate still requires evidence, deterministic code validation where applicable, isolated review, the repository's required human approval, formal audit, and atomic promotion. The six remediation-required records remain blocked until their Question/Canonical/source boundary is explicitly resolved.
