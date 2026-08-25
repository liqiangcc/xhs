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
