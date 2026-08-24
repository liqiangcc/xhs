# Answer Batch 0022 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0022_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It separates source recoverability from answer correctness and fails closed when the surviving source cannot uniquely define an executable coding contract.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 6
- Recoverable normalization: 1
- Source-unrecoverable / excluded: 3
- Active after boundary remediation: 7

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_3aa1637d60f1dbea7bb4279a4ae3f6a1` | candidate-qualified | Image transcript preserves the exact JavaScript closure code, including the `where = "inside"` line and the “comment this line out” variation; answer can analyze lexical lookup without inventing missing input. |
| `cq_q_3ae198b1c39ab778836b9d3b8bd106b0` | candidate-qualified | Caption explicitly names LeetCode 63 / “不同路径 II”, making the obstacle-grid problem identity recoverable. |
| `cq_q_3bd9ce7e8b983c0e09e7b573588a0d3a` | exclude / `incomplete_or_unreadable` | Source says only “类似于股票卖出的最佳时机” and mentions a loop/DP discussion; transaction count and other state-defining constraints are absent, so no unique executable variant can be restored. |
| `cq_q_3bf259d7b6e7b206848ba45de660e99a` | normalize, then candidate-qualified | Caption says input `ab12cd34`, output `12`, solved with regex; image transcript shows `\d+` + first `matcher.find()`. The current “specified substring” wording is broader than the source and is normalized to “first continuous digit substring”. |
| `cq_q_3c1de47a37045804edd3e2e78ec3856d` | candidate-qualified | Source explicitly asks “二维数组找 target”. No sorted-row/column property survives, so the answer must treat the matrix as arbitrary unless it clearly labels sorted-matrix approaches as variants. |
| `cq_q_3c7d96b17f91a649fa290bd93958f08c` | candidate-qualified | Source explicitly asks for the number of leaf-node pairs in a tree whose distance is less than a specified `distance`; tree-DP implementation can preserve that strict boundary. |
| `cq_q_3d550dfc40061007739e893f666d49f2` | candidate-qualified | Source gives both tables/columns and the exact requirement: users who bought at least two distinct products. |
| `cq_q_3de03dc6dea1f4c4fa3022b5283db2ea` | exclude / `incomplete_or_unreadable` | Source preserves only the sample plus “奇数递增，偶数递减的链表排序”; it does not define whether odd/even means positions or values, the input invariant, or the required final order, so common interview variants cannot be safely substituted. |
| `cq_q_3e0fe4f12f951128a2a1fb250199dcd6` | candidate-qualified | Source directly names “对称二叉树”; this is a stable, executable problem identity. |
| `cq_q_3e406e6dedb661f2b0b02d4355917de0` | exclude / `incomplete_or_unreadable` | Strongest source only records “代码题（贪心加双指针）”; it preserves a technique category but no problem object, input/output, objective or constraints. |

## Normalization

`cq_q_3bf259d7b6e7b206848ba45de660e99a` remains the Canonical identity. Its source Question is normalized from the unsupported generic “提取指定子串” wording to:

> 编程实现：给定字符串，提取第一个连续数字子串；例如输入 "ab12cd34"，输出 "12"。

The normalized Question id is `5f1229da81132a7214d064e2a8fc0b4c`. This wording is supported by both the caption and image transcript. A regex implementation is source-backed; a linear character scan may be discussed as an alternative, but neither should expand the Question beyond extracting the first continuous digit run.

## Fail-closed exclusions

The three excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with `incomplete_or_unreadable` and a specific explanation. If stronger repository evidence later restores a unique executable contract, the source row can be re-included through the normal migration path.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, and all answer CI gates pass may batch 0022 candidate work begin.
