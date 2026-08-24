# Answer Batch 0023 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0023_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It separates source recoverability from answer correctness and fails closed when the surviving source cannot uniquely define an executable coding/command contract.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 6
- Recoverable wording normalization: 1
- Answer-type metadata correction: 1
- Source-unrecoverable / excluded: 2
- Active after boundary remediation: 8

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_3e7bd1708ff77403d01141eed87a0d38` | candidate-qualified | Caption preserves the full minimum-window contract: shortest substring of `S` containing every character of `T`, including duplicate multiplicity, or empty string if absent. |
| `cq_q_3e94666b4738de5e0a5df40052329f18` | candidate-qualified | The original tag carried a stale Question id, but an exact normalized wording match recovers the repository image transcript for LeetCode 72, including both words, the insert/delete/replace operations, and examples. |
| `cq_q_3f45aeaf42ea66632927d3dfc96608bf` | candidate-qualified | Caption explicitly identifies “字符串相乘，Leetcode43”; the stable problem identity is recoverable without inventing a different big-integer task. |
| `cq_q_3f6b196a94cc495fb482d88305f9ab94` | candidate-qualified | Caption states: from a given array choose three values as triangle sides and maximize perimeter. The objective and input object are preserved. |
| `cq_q_40513b5c52db7d66bb1432079733783c` | candidate-qualified | Image transcript explicitly records “手撕：排序链表”; this is a stable executable problem identity. |
| `cq_q_449cb09687b14bdba2c6864c7787239f` | normalize, then candidate-qualified | Source says only “Linux命令，批量终止名字包含abc的进程”. The current Canonical invents a mandatory `ps|grep|awk|xargs`-style pipeline. Normalize to the source-backed process-termination goal; the answer may compare safe command choices instead of pretending one pipeline was required. |
| `cq_q_44ff2aad182c5458e01efb1d5e71d10f` | reclassify Concept, then candidate-qualified | Caption explicitly asks how to obtain values from a Python dictionary. It is an API/enumeration question, not an algorithm-handwriting contract; the current Coding tag and placeholder Java implementation are classification debt. |
| `cq_q_454acf00cd919a7e95a309068e8eaf5a` | exclude / `incomplete_or_unreadable` | Source only says an interviewer gave a “斗地主发牌程序”. It does not preserve deck/player/bottom-card rules, shuffle/deal order, I/O representation, or requested interface, so common tutorial implementations cannot safely substitute for the interview contract. |
| `cq_q_454e063c3dff5366f28907955aa777e3` | exclude / `incomplete_or_unreadable` | Three repository captions all say only “对于日志文件，查看前10的URL，用什么命令”. None says “按出现频率”, and none preserves the log format or URL field. The current Canonical adds unsupported ranking semantics; a unique command contract cannot be reconstructed. |
| `cq_q_458ab81f23e2fde622c12a1a85c8438a` | candidate-qualified | Image transcript explicitly asks to implement equality comparison for two trees, return `1` when equal, another value otherwise, and state complexity. |

## Normalization

`cq_q_449cb09687b14bdba2c6864c7787239f` remains the Canonical identity, but its source Question is narrowed from the unsupported pipeline-specific wording to:

> Linux 命令：批量终止名字包含 abc 的进程

The normalized Question id is `55ee94f1cd20c8f85bc43f9f932f602f`. The source does not distinguish process-name matching from full-command-line matching, so the final answer must state that boundary when comparing commands; it must not claim the interview required a particular pipeline.

## Type correction

`cq_q_44ff2aad182c5458e01efb1d5e71d10f` keeps its Question identity and is reclassified from `算法手撕_Coding` to `八股文_Concept`. Its source asks for Python dictionary value-access methods and does not request a runnable algorithm or Java implementation. The answer-type audit must resolve this Canonical to `concept` before candidate authoring.

## Fail-closed exclusions

The two excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with `incomplete_or_unreadable` and a specific explanation. Stronger future repository evidence may restore a unique contract through the normal migration path.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, answer type audit, and all answer CI gates pass may batch 0023 candidate work begin.
