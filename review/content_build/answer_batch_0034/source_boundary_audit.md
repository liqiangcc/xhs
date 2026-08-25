# Answer Batch 0034 Source Boundary Audit

## cq_q_7b295050485d85a9831398730c0ce1a5

- Exact repository source: `note_tagged/68bc0218000000001d02a145.json` note question `43f70cfb3ecc582e11bf3dc305a18f3c`; canonical context maps the preserved wording to library question `7b295050485d85a9831398730c0ce1a5`.
- Preserved wording: `算法：业务场景题（购物车合并）？`
- Source-preserved facts: this is a coding/business-scenario prompt about merging shopping carts.
- Not preserved by the source: cart ownership model, item identity key, duplicate-line semantics, quantity conflict rule, quantity cap, inventory/price/promotion behavior, ordering, persistence, idempotency, concurrency, API shape, or failure handling.
- Candidate executable policy only: merge two in-memory carts by SKU; aggregate positive quantities; saturate at an explicit per-SKU cap; preserve account-first first-seen order; do not mutate inputs; reject malformed lines. This is answer-side policy, not recovered source fact.
- Promotion remains blocked until isolated source-first review, evidence gate, required human approval, and real-review policy are satisfied.
