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
