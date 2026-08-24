# Answer Batch 0029 — House Robber Relation Review

## Source-first facts

- `64fba5a4c506e237a3a3cf3a91414c8b`: 算法手撕：打家劫舍（House Robber, 简单动态规划）。
- `6634a5c9294a3f0117a0a029020256ae`: 算法手撕：LeetCode 198 - 打家劫舍。给定一个代表每个房屋存放金额的非负整数数组，计算在不触发报警装置（不进入相邻房屋）的情况下，一夜之内能够偷取的最高金额

No historical relation/remediation record was consulted to reach the conclusion below. Both current source Questions ask the same coding contract: maximize the sum selected from a linear sequence of house values under the constraint that adjacent houses cannot both be selected. The second wording identifies the standard problem as LeetCode 198 and states the non-negative-array contract explicitly; it does not introduce a distinct output, algorithmic objective, topology, or failure model.

## Decision

Relation: `same`. Preserve `cq_q_6634a5c9294a3f0117a0a029020256ae` as the survivor because its source wording is the more explicit contract. Retire the singleton duplicate `cq_q_64fba5a4c506e237a3a3cf3a91414c8b` through the reviewed Select → Decide → Apply path. The survivor Answer must remain invalid/rebuildable if source consolidation changes its audited source set; this relation decision does not by itself promote any Answer.
