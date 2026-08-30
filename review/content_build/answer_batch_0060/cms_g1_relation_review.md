# Batch 0060 CMS/G1 Source-First Relation Review

## Primary-source facts

- Target-side repository sources preserve CMS/G1 comparison wording, including one explicit selection variant: “CMS垃圾收集器和G1垃圾收集器什么区别”；“CMS 和 G1 垃圾收集器的区别？”；“CMS 与 G1 垃圾收集器的区别，如何根据场景 choose？”。
- Source-side repository sources preserve CMS/G1 comparison wording: “对比 CMS 和 G1 垃圾回收器的区别”；“对比 G1 与 CMS 垃圾回收器的核心区别”；“CMS和G1垃圾回收器的区别？”。
- Across all six frozen source Questions, the compared collectors are the same CMS and G1 pair. No source preserves a distinct collector pair, a CMS-only execution-flow contract, a G1-only mechanism contract, or a separate quantitative benchmark contract.
- The target-side “how to choose by scenario” wording deepens the same comparison by asking for decision criteria; it does not require an independent Canonical because a complete comparison answer should already cover trade-offs and applicability boundaries.

No historical relation/remediation record was consulted before this conclusion.

## Decision

Relation: `same`. Consolidate `cq_q_7960226d99224c6c8d4411110ff10c8b` into survivor `cq_q_d3fea003c007b50735b8e695473de9ac`, retain every valid source Question, and use the survivor title “CMS 与 G1 垃圾收集器的区别及场景选择” so the deepest preserved source intent remains visible.

## Application safety

The source Canonical owns exactly 3 Questions. The Dedup pair contract reviews each source Question independently against target bridge Question `d3fea003c007b50735b8e695473de9ac`. Every explicit same Decision is re-prepared against current revisions immediately before one guarded Canonical merge. The merge fails closed if the source Question scope or reviewed target bridge ownership drifts.

## Content consequence

Do not write two duplicate CMS/G1 answers. Regenerate Batch 0060 source inventory after consolidation; the surviving Mechanism answer must cover collector architecture, phases/concurrency, fragmentation/compaction, pause goals, remembered-set/region behavior, failure/fallback boundaries, version/deprecation boundaries, and scenario-selection trade-offs.
