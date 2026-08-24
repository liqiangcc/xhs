# Answer Batch 0024 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0024_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It separates source recoverability from answer correctness and fails closed when the surviving source cannot uniquely define an executable coding contract.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 6
- Source-unrecoverable / excluded: 4
- Active after boundary remediation: 6

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_458d73b3af53aae38af2eaf83473ef2f` | candidate-qualified | Caption explicitly requires Java synchronized code that deterministically reaches a deadlock. |
| `cq_q_4715e4cb7c542d15146981fcac350958` | candidate-qualified | Caption explicitly asks to find the most frequent element in an integer list and write tests; tie behavior is not preserved and must remain an answer-level stated assumption. |
| `cq_q_48bf70b4872cce81f798c61fe039ef47` | candidate-qualified | Caption explicitly lists both underscore-to-camel and camel-to-underscore implementations. |
| `cq_q_48d51539a85aabde9bd294e902c0cd86` | candidate-qualified | Caption explicitly asks rand5() to rand7(), preserving the stable equal-probability construction problem identity. |
| `cq_q_494b0b68c1f4eb41cf7ec520babc8f11` | candidate-qualified | Image transcript explicitly states building a binary tree with the array maximum as root and recursively doing left/right. |
| `cq_q_496dcfbf2235c39f2f484c991f151e76` | candidate-qualified | Caption explicitly asks to build a binary tree from preorder and inorder traversals. |
| `cq_q_45e7ff4427260a3df4b31c08cad14141` | exclude / `incomplete_or_unreadable` | 仓库来源把“给出 SQL 创建索引”“手撕具体 SQL 加锁语句”“手撕并发死锁代码”列为三个独立二面题，但当前抽取把它们合成一个 Canonical。来源没有保留表结构、索引目标、加锁对象/事务上下文或死锁场景，无法恢复一个语义边界单一且可唯一验证的可执行合同；因此按 incomplete_or_unreadable fail closed，不能用通用 SQL 示例替代原题。 |
| `cq_q_46a0db137d9b355e6858b744d86f5d26` | exclude / `incomplete_or_unreadable` | 仓库来源只说明面试有“两道 SparkSQL 题”，其中一道考察数据构造，没有保存具体输入数据、目标结果、表/字段结构或查询约束。当前 Canonical 的“复杂数据构造与查询实操”是类别概括而不是可执行题目，无法唯一恢复原题，因此按 incomplete_or_unreadable fail closed。 |
| `cq_q_46f480936190e2b68c9f9dc6cba0d866` | exclude / `incomplete_or_unreadable` | 仓库来源只保留“手撕：前缀和”这一题名，没有说明是一维/二维、构造数组还是区间查询、输入输出接口、是否需要动态更新等合同。前缀和是一类技术而非唯一题目；直接选择任一常见模板会超出来源，因此按 incomplete_or_unreadable fail closed。 |
| `cq_q_46fe1307494a9f56b39e0d9f76796f61` | exclude / `incomplete_or_unreadable` | 仓库来源文字写“链表，每三个结点逆转顺序”，但唯一保留示例把 1 2 3 4 5 6 7 8 变为 7 8 4 5 6 1 2 3；这并不是当前 Canonical 所声称的标准 K 个一组节点反转（该操作会得到 3 2 1 6 5 4 7 8）。来源 wording 与示例支持的变换语义冲突，也没有更多样例定义余数组、组内/组间顺序和一般 K 的规则。不能把 LeetCode 25 或自创“反转分组顺序”合同擅自代入，因此按 incomplete_or_unreadable fail closed。 |

## Fail-closed exclusions

The four excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with `incomplete_or_unreadable` and a specific explanation. Stronger future repository evidence may restore a unique contract through the normal migration path.

In particular, `cq_q_46fe1307494a9f56b39e0d9f76796f61` is not silently normalized to LeetCode 25: the preserved example contradicts standard K-group node reversal, so choosing that well-known problem would be an unsupported semantic substitution.

## Candidate constraints

- `cq_q_4715e4cb7c542d15146981fcac350958`: the source does not define tie behavior; a candidate must state its tie assumption rather than claim the interviewer required one.
- `cq_q_494b0b68c1f4eb41cf7ec520babc8f11`: the source preserves the maximum-as-root recursive construction; any duplicate-value convention must be stated as an implementation assumption.
- `cq_q_496dcfbf2235c39f2f484c991f151e76`: a candidate may state the usual unique-value prerequisite for unique reconstruction, but must not attribute that prerequisite to the source.
- `cq_q_458d73b3af53aae38af2eaf83473ef2f`: the image transcript is tool-dialogue noise; the caption is the authoritative repository-local evidence for the deadlock prompt.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, answer type audit, and all answer CI gates pass may batch 0024 candidate work begin.
