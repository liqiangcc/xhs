# Answer Batch 0036 — Temperature / Daily Temperatures Relation Review

## Source-first facts

- shorthand source `85d552bc1c5e793996cb2ea34fe2e614`: 算法：温度 (单调栈)
- explicit source `870fc85ff34de337bdcf1e05799217ca`: 算法手撕：每日温度（Daily Temperatures）。
- both are current valid Coding Questions and both are tagged with the monotonic-stack entity.
- repository-wide source-near enumeration for “每日温度 / 温度+单调栈 / Daily Temperatures” returns exactly these two Questions and exactly these two singleton Canonicals.

No historical relation/remediation record was consulted to form this conclusion. The shorthand source does not preserve a full formal statement, but within the current corpus its combination of “温度” plus the explicit “单调栈” method uniquely resolves to the same recoverable coding problem identified by the second source as Daily Temperatures. Treating it as a separate unknown temperature problem would duplicate one source-bounded problem while providing no distinct input/output or constraint evidence.

## Decision

Relation: `same`. Preserve `cq_q_870fc85ff34de337bdcf1e05799217ca` as the survivor because it has the source-explicit Daily Temperatures title. Retire singleton `cq_q_85d552bc1c5e793996cb2ea34fe2e614` through the reviewed Select → Decide → Apply path. The survivor Answer remains `needs_update` until rebuilt and independently reviewed against both source Questions; this consolidation does not promote content.
