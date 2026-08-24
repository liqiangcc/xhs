# Answer Batch 0026 — Source-First Boundary Audit

- Evidence boundary: frozen `review/reports/ANSWER_BATCH_0026_SOURCE_PACKET.{json,md}` only, with raw caption/image text preferred over derived tagged wording.
- Audit rule: preserve real recoverable Questions; normalize only source-inflated wording; fail closed when no unique executable problem identity can be recovered.
- Result: original 10 Canonicals → 8 active, 2 excluded as `incomplete_or_unreadable`.

| Canonical | Disposition | Source-first basis |
| --- | --- | --- |
| `cq_q_4fc0d124be6bf13d0fcfe8b0394a23a1` | candidate-qualified | Raw caption explicitly records “实现虚拟滚动和图片懒加载的结合”; the answer may state its component/API assumptions instead of inventing a hidden judge contract. |
| `cq_q_50d730f280e48c997fa9f9e662eb95ac` | candidate-qualified | Image transcript preserves LeetCode 5, the longest-palindromic-substring statement, length bound, and examples. |
| `cq_q_50ef484fd29fe4ba23065db1b1439c74` | candidate-qualified | Raw caption explicitly records deleting duplicate nodes from a linked list. Because “duplicate” can mean keep-one or delete-all, the formal answer must surface and handle both standard contracts rather than silently choosing one. |
| `cq_q_51683d4359a08f525adc2fead28a44aa` | candidate-qualified | Image transcript explicitly asks to partition intervals into the minimum number of groups with no overlap inside a group. Endpoint-touch semantics must be declared in the answer. |
| `cq_q_53686d4f6b7cd986269f67826d29b4ba` | candidate-qualified | Raw caption explicitly records deleting a node from a binary-search tree. |
| `cq_q_54e8509938a2d444e8bbc86d62206ef8` | candidate-qualified | Raw caption explicitly asks to validate whether an arbitrary input string conforms to IPv4 rules. |
| `cq_q_54f9a2d007c671b36e91b98db69f6c2d` | candidate-qualified | Raw caption explicitly asks for overlapping date intervals and states an O(n) target. A correct answer must distinguish general unsorted input from the extra ordering/bounded-domain assumptions needed for linear time. |
| `cq_q_5438416849074df945e61753490c7651` | normalize + candidate-qualified | Raw caption asks only “有一个List<User>，将他转成Map，其中key为userId有哪些方法？”; derived wording added unsupported “three or more” and mandatory Stream API constraints. Canonical identity is retained while source Question wording/id is narrowed. |
| `cq_q_53e13c85c2e7c270c46b64027dbd64f6` | exclude — incomplete_or_unreadable | 最强原始 caption 只说明“一面回溯题思路正确但未去重，算法未 AC”，没有保留题目、输入输出、约束或题号。当前结构化 Question 进一步具体化成“子集、排列 II / 搜索空间剪枝与去重”，这些细节无法由原始来源唯一恢复；因此不能据此生成可验证 Coding 合同，按 incomplete_or_unreadable fail closed。 |
| `cq_q_542633986c66e30d8935d192f98137be` | exclude — incomplete_or_unreadable | 最强原始 caption 仅保留“手撕 mid，常见题”（三面另有“mid-hard 手撕，不是很常见”），没有任何具体题目身份、输入输出、约束或样例。“常见中等难度手撕题”不是可唯一还原的问题，无法形成确定性 Coding 合同，按 incomplete_or_unreadable fail closed。 |

## Guardrails for the next stage

- `cq_q_50ef...`: do not silently choose between “deduplicate while keeping one” and “delete all values that repeat”; a formal answer must surface both contracts or explicitly require clarification.
- `cq_q_51683...`: state whether touching endpoints overlap before presenting a greedy implementation.
- `cq_q_54f9...`: do not claim O(n) for arbitrary unsorted intervals; explain the ordering/bounded-domain condition that makes the requested linear bound achievable.
- No answer is promoted by this boundary remediation. Candidate authoring, isolated review, evidence/code gates and pilot approval remain separate stages.
