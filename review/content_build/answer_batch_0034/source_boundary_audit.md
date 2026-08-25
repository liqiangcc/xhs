# Answer Batch 0034 Source Boundary Audit

## cq_q_7b295050485d85a9831398730c0ce1a5

- Exact repository source: `note_tagged/68bc0218000000001d02a145.json` note question `43f70cfb3ecc582e11bf3dc305a18f3c`; canonical context maps the preserved wording to library question `7b295050485d85a9831398730c0ce1a5`.
- Preserved wording: `算法：业务场景题（购物车合并）？`
- Source-preserved facts: this is a coding/business-scenario prompt about merging shopping carts.
- Not preserved by the source: cart ownership model, item identity key, duplicate-line semantics, quantity conflict rule, quantity cap, inventory/price/promotion behavior, ordering, persistence, idempotency, concurrency, API shape, or failure handling.
- Candidate executable policy only: merge two in-memory carts by SKU; aggregate positive quantities; saturate at an explicit per-SKU cap; preserve account-first first-seen order; do not mutate inputs; reject malformed lines. This is answer-side policy, not recovered source fact.
- Promotion remains blocked until isolated source-first review, evidence gate, required human approval, and real-review policy are satisfied.

## cq_q_7bf6988f5dc924ebd953a660966d019f

- Exact repository source: `note_tagged/68234a600000000023013b38.json`, question `7bf6988f5dc924ebd953a660966d019f`.
- Preserved wording: `算法：计算一个 Data 的均值和方差（第一个维度）？`
- Source-preserved facts: compute mean and variance of a Data object along the first dimension.
- Not preserved by the source: Data rank/shape/type, whether “first dimension” means axis 0, population vs sample variance, NaN/missing-value policy, output shape, language/API, mutation policy, or numerical-stability requirements.
- Candidate executable policy only: treat Data as a non-empty rectangular finite `double[][]`; first dimension means rows/axis 0; return per-column mean and population variance (divide by N); reject empty/ragged/non-finite input; use one-pass Welford updates. These are answer-side contracts, not recovered facts.
- Promotion remains blocked until isolated review, evidence gate, required human approval, and real-review policy are satisfied.

## cq_q_7ca6615c45d3aeb785c27dc7796d1afb

- Exact tagged source: `note_tagged/6888685a0000000005008900.json`, question `7ca6615c45d3aeb785c27dc7796d1afb`: `算法：最大版本号 (165. 比较版本号)`.
- Stronger repository image text: `note_img_txt/6888685a0000000005008900.txt` explicitly says the interview variant supplied multiple version numbers to compare.
- The source identifies LeetCode 165, so the pairwise revision semantics are recoverable from the official problem: dot-separated numeric revisions, leading zeros ignored, missing revisions treated as zero.
- Answer-side adapter: linearly reduce multiple versions with the LeetCode-165 comparator; semantically equal versions retain the first original representation.
- The repository does not preserve concrete ACM stdin/stdout layout or tie-representation rules; those remain explicit adapter choices.
- Promotion remains blocked until isolated review, evidence gate, required human approval, and real-review policy are satisfied.

## cq_q_7d3154a0b8c8da4bf0d09accd6921e94

- Exact repository source: `note_tagged/670b6b1a000000001b03d867.json`, question `7d3154a0b8c8da4bf0d09accd6921e94`.
- Preserved wording: `算法思路：如何判断并找到两个单链表的相交节点？请口述双指针思路`
- Preserved response shape: explain the two-pointer idea for finding the intersection node of two singly linked lists.
- Not preserved by the source: node class/value type, whether cycles are allowed, or any mutation allowance.
- Candidate executable policy only: lists are finite acyclic singly linked lists; intersection means the same node object/shared suffix rather than equal values; return the first shared node or null; do not mutate either list.
- A cyclic-list variant is deliberately outside the candidate contract because the switch-head termination proof assumes finite acyclic traversals.
- Promotion remains blocked until isolated review, evidence gate, required human approval, and real-review policy are satisfied.

## cq_q_7cf94a421237d5445dc8e6a277be9489

- Exact repository source: `note_tagged/685696fe0000000012033bb6.json`, question `7cf94a421237d5445dc8e6a277be9489`.
- Preserved wording: `编程题：如何将数组拆分成和小于等于 k 的最少数量子数组？`
- Preserved intent: minimize the number of subarrays whose sums are at most k.
- Not preserved: whether values are non-negative, explicit bounds, empty-input behavior, impossible-case return value, or whether “子数组” was intended in the standard contiguous sense versus arbitrary grouping.
- Candidate executable policy: interpret a split into subarrays as a partition of the whole input, in original order, into non-empty contiguous segments; allow signed int values; each segment sum must be <= k; empty input returns 0; return -1 when no valid partition exists.
- Because non-negativity is not preserved, the main solution uses prefix sums + DP rather than assuming the one-pass greedy optimization; the greedy variant is described only conditionally for non-negative inputs.
- Promotion remains blocked until isolated review, evidence gate, required human approval, and real-review policy are satisfied.
