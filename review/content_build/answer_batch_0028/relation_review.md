# Answer Batch 0028 — Current Relation Review

This review is downstream of the frozen source-first boundary audit. It does not amend the frozen source packet or infer new source facts. It checks only current repository Canonical/Answer facts needed before bounded mutations and records which relationships must be materialized through the current `canonical suggest -> dedup decide -> dedup apply` workflow.

## 1. Linked-list reversal

- Batch member: `cq_q_5d39b5ae05a488c7436cbfa9b21e746c` — source asks how to implement linked-list reversal.
- Existing active Canonical: `cq_q_55c3a35aaf4f76ce9aab78ea39d9fddc` — already source-qualified in batch 0027 as linked-list reversal.
- Boundary conclusion: these are the same answer boundary. No independent constraint, variant, node model, segment range, recursion requirement, or other source distinction justifies two curated Answers.
- Required repository action: generate a fresh RelationCandidate from current facts, record an explicit `same` decision with `actor.type=ai`, then apply it with the existing source-qualified Canonical as survivor. Do not hand-edit `canonical_id`; do not author or promote a second reversal Answer.

## 2. Deep-copy implementation versus deep-copy concept

- Batch member: `cq_q_5e21e188af5c4a9ffdb5eaf97cc39c97` — frontend source explicitly asks to implement a deep-copy function.
- Existing active Canonical: `cq_deep_copy_5cfb8eb4` — current answer-spec contract is Concept-oriented: shallow versus deep copy semantics, cycles/shared references, immutable values and resource-handle limits.
- Boundary conclusion: `related`, not automatically `same`. The Coding source requires an executable JavaScript/TypeScript-style implementation contract and concrete supported-value policy; the Concept asset can explain semantics without satisfying code/type/code-regression gates. Similarity is insufficient to collapse these response contracts.
- Required repository action: generate a fresh RelationCandidate, record an explicit `related` decision with `actor.type=ai`, and apply the relation-only no-Canonical-mutation path. Keep the Coding Canonical separate unless a later explicit decision demonstrates one formal Answer can satisfy both contracts and all type gates.

## 3. Mixed big-number-addition + SQL source row

The legacy batch member `cq_q_5f1aa586172b1a82ebb8cdd65fb6927b` must first be split source-first because the raw caption contains two independent interview questions.

### Big-number string addition child

- Source contract: add two decimal strings, return the sum as a string in `O(n)`; the source example explicitly treats an empty string as zero (`"321" + "" = 321`).
- Existing active Canonical: `cq_topic_cc39dcdb` — `算法：字符串大数加法`, Coding.
- Current candidate fact: the existing candidate/spec requires both inputs to be non-empty and rejects empty strings. Therefore the newly recovered source variant is not covered by the current candidate bytes.
- Boundary conclusion: same conceptual/Coding answer boundary after the source split, but the surviving Canonical's candidate/evidence/review become stale until revised and re-reviewed against the newly attached source variant. The empty-string behavior may not be silently discarded.
- Required repository action: after the split child exists, generate a fresh RelationCandidate, record explicit `same`, apply it to `cq_topic_cc39dcdb`, then mark/rebuild candidate review artifacts from the new source set before promotion.

### Student/grade average SQL child

- Source contract: from student and grade tables, query student number, student name and average grade.
- Repository search did not identify an existing exact Canonical for this source wording/answer boundary.
- `JOIN` and `GROUP BY` are solution techniques, not source requirements; schema/column names are absent from source.
- Required repository action: create the source-exact Question during the guarded split, run current relation suggestion against fresh repository state, and only create/retain a distinct Canonical if explicit relation review finds no reusable same-boundary Canonical. Candidate SQL must state a minimal schema assumption rather than rewriting that assumption into source evidence.

## 4. Mutation sequencing / fail-closed rules

1. Apply source-text normalizations and the unrecoverable exclusion first; rebuild projections and verify exact source dispositions.
2. Split the mixed big-number/SQL source Question using the established guarded source-question split pattern, without promoting either child.
3. Re-run current RelationCandidate discovery after those Questions exist; do not reuse a stale similarity result captured before the source mutation.
4. Record AI decisions with explicit rationale. Never fabricate `human` review state.
5. Apply only current, fresh Decisions. `same` may mutate Canonical ownership; `related` records relation only.
6. Re-run Question coverage, Canonical, ReviewProgress, strict Answer, type, semantic, evidence, code and full CI gates after mutation.
7. Any surviving Answer whose source set or response contract changes is stale by construction and must complete fresh candidate -> isolated review -> evidence/code gate -> required human approval before atomic promotion.
