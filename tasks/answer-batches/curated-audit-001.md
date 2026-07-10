# Curated audit batch 001

- Status: `in_progress`
- Canonical count: `10`
- Purpose: independently audit the first ten historical curated answers against `answer_quality.v1`.
- Required evidence: official or primary sources, claim mappings, source-question coverage, and a reviewer decision.
- Pilot rule: the root task requires human review for all first 60 upgraded/audited answers; AI review may prepare a decision but cannot replace that sign-off.

## Canonicals

- `cq_ai_055f19f9`
- `cq_aof_e522aa87`
- `cq_aqs_f718305c`
- `cq_arch_layering_02c49d25`
- `cq_arraylist_9d3444a1`
- `cq_async_tradeoff_bef9a76a`
- `cq_bean_319a398d`
- `cq_binlog_86a375fd`
- `cq_cache_consistency_a83eeb36`
- `cq_cas_64fa0b00`

## Recorded result

- `cq_aof_e522aa87`: independent review decision `revise`; score `86/100`; hard failures `missing_evidence`, `unsupported_factual_claim`.
- Formal answer was atomically demoted to `needs_update` / `curated_audit_failed`, and its Canonical status was synchronized. It requires a version-bounded rewrite and a fresh independent review before any re-promotion.
