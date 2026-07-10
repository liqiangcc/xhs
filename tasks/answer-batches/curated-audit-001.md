# Curated audit batch 001

- Status: `in_progress`
- Canonical count: `10`
- Purpose: independently audit the first ten historical curated answers against `answer_quality.v1`.
- Required evidence: official or primary sources, claim mappings, source-question coverage, and a reviewer decision.
- Pilot rule: the root task requires human review for all first 60 upgraded/audited answers; AI review may prepare a decision but cannot replace that sign-off.
- Record an approval through `node scripts/xhs.js answer human-review --canonical-id <id> --evidence <path> --review <human-review.json>`; the record must bind Canonical ID, candidate hash, reviewer ID, date, batch ID, decision and attestation. Promotion blocks until 60 valid human approvals are accumulated.

## Canonicals

- `cq_aof_e522aa87`
- `cq_aqs_f718305c`
- `cq_bean_319a398d`
- `cq_binlog_86a375fd`
- `cq_cms_collector_c069b541`
- `cq_equals_hashcode_e7fe32f7`
- `cq_g1_collector_828f806c`
- `cq_hashmap_4d9f15d2`
- `cq_hashmap_d74d2fd7`
- `cq_io_multiplexing_6e30840f`

## Recorded result

- `cq_aof_e522aa87`: historical-answer audit decision `revise`; score `86/100`; hard failures `missing_evidence`, `unsupported_factual_claim`.
- Its version-bounded candidate then received a second isolated review: `90/100`, decision `revise`, hard failure `unsupported_factual_claim`. The reviewer found that Redis 7 manifest publication/recovery and incomplete-publication behavior still lack direct evidence mapping.
- Formal answer was atomically demoted to `needs_update` / `curated_audit_failed`, and its Canonical status was synchronized. The candidate exhausted the two-revision limit and must remain unpromoted.
- `cq_aqs_f718305c`: independent review decision `revise`; score `82/100`; hard failures `unsupported_factual_claim`, `missing_version_boundary`. It was atomically demoted to `needs_update` / `curated_audit_failed`; the required revision must pin the JDK/API boundary and cover cancellation, parking, wake-up and fairness trade-offs with source mappings.
