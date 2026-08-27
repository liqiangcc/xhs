# Batch 0040 Subarray-Sum-K Source-First Relation Review

## Primary-source facts

- `d63322aa9fd4048a05c37c235c47ce2c`: “算法：和为 K 的子数组（LeetCode 560）”.
- `a4a80af48b7e1af0a3cdd334e8e43506`: “算法：和为 K 的子数组 (LeetCode 560 - 前缀和 + 哈希表)”.
- Both repository sources explicitly identify LeetCode 560, Subarray Sum Equals K. The second wording additionally names the standard prefix-sum + hash-map technique, but that is an implementation cue for the same problem rather than a different input/output contract. Neither source preserves a variant such as longest subarray, non-negative-only sliding window, returning indices, or counting subsequences.

No historical relation/remediation record was consulted before this conclusion.

## Decision

Relation: `same`. Consolidate Batch 0040 singleton `cq_q_a4a80af48b7e1af0a3cdd334e8e43506` into survivor `cq_q_d63322aa9fd4048a05c37c235c47ce2c`, preserving both Questions.

## Content consequence

This relation slice does not promote content. The survivor still requires source-bounded curation, executable tests, isolated review, evidence/code gates, required human approval, and real-review policy.
