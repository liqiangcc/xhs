# 16 Repository Architecture Role Term Audit — Completed

> Scope: classify and close the active architecture-role naming debt after the Review and Canonical migrations. The implementation is behavior-preserving: persisted schemas, CLI contracts, Domain rules, revision coverage and transaction behavior remain unchanged.

## 1. Approved vocabulary

Current outbound roles are:

```text
Repository
QueryRepository
Gateway
Publisher
Reader
Generator
```

Role names are selected from responsibility, not folder names or spelling alone. Repository-local callers, tests, Composition Root wiring and documentation move atomically; no compatibility aliases remain merely to preserve old names.

## 2. Completed migrations

### 2.1 Canonical quality report publication

Completed:

```text
CanonicalQualityReportWriter      -> CanonicalQualityReportPublisher
assertCanonicalQualityReportWriter -> assertCanonicalQualityReportPublisher
write(report)                      -> publish(report)
```

Current files:

```text
src/ports/services/canonical-quality-report-publisher.js
src/infrastructure/filesystem/canonical-quality-report-publisher.js
```

Application decides whether a `canonical_quality_report.v1` is published. The Publisher owns only the outbound publication capability; Infrastructure owns the path and filesystem encoding.

### 2.2 Dedup relation candidate publication

Completed:

```text
RelationCandidateStore -> RelationCandidatePublisher
```

Current Port:

```text
src/ports/relation-candidate-publisher.js
RelationCandidatePublisher.replaceQueue(queue)
```

The read side remains separate:

```text
RelationCandidateRepository.get(relationCandidateKey)
```

The Publisher replaces one pending review queue for a scope/seed. It cannot authorize a relation decision or mutate Canonical state.

### 2.3 Dedup relation decision consistency boundary

The boundary was characterized before the final rename. Executable tests freeze:

```text
pending queue revision coverage
Question / entity-index / hotspot-index source revision coverage
lock ownership and busy rejection
stale-state rejection before append
atomic decision-log replacement
lock cleanup after success or failure
absence of Canonical Apply capabilities
```

Completed:

```text
RelationDecisionStore -> RelationDecisionGateway
```

Current Port:

```text
src/ports/relation-decision-gateway.js
RelationDecisionGateway.record(decision, { expected_revisions })
```

The read side remains:

```text
RelationDecisionRepository.get(relationCandidateKey)
```

The Gateway compares the exact expected revision set while holding the decision lock and atomically appends the auditable decision. It does not perform Canonical Apply.

## 3. Settled naming

Review remains:

```text
ReviewQueueStateCoordinator
ReviewProgressReader
ReviewProgressRepository
ReviewStrategyReader
ReviewIssueLinkReader
ReviewPlanPublisher
ReviewMutationGateway
```

Canonical Question-group lifecycle remains:

```text
Resolve -> Prepare -> Plan -> Execute

ResolveQuestionGroupCanonicalizationUseCase
QuestionGroupCanonicalizationPreparationCoordinator
PlanQuestionGroupCanonicalizationMutationUseCase
ExecuteQuestionGroupCanonicalizationUseCase
CanonicalMutationGateway
FileCanonicalMutationGatewayAdapter
```

`CanonicalizationPlan` and `CanonicalMutationPlan` remain separate concepts.

## 4. Legacy technical modules

The following compatibility modules remain historical technical modules, not approved examples for new architecture naming:

```text
scripts/lib/answer_store.js
scripts/lib/canonical_store.js
scripts/lib/index_store.js
scripts/lib/issue_store.js
scripts/lib/question_store.js
scripts/lib/review_store.js
```

Do not mass-rename them. Each is migrated or retired only with its remaining callers and compatibility obligations. Likewise, the directory name `src/ports/services` is not a reason to perform a bulk folder move; path restructuring is a separate concern.

## 5. Governance gate

Future role changes follow:

```text
understand responsibility
-> freeze the separation point
-> choose an approved role
-> migrate all repository-local callers atomically
-> remove old aliases
-> prove behavior unchanged with CI
```

## 6. Completion evidence

Completion requires all of the following to stay green:

```text
repository_role_term_audit.test.js
canonical_check_application.test.js
dedup_suggestion_ports.test.js
dedup_relation_decision_application.test.js
dedup_relation_decision_filesystem.test.js
architecture_boundaries.test.js
npm run ci:check
```

There is no remaining active `next_target` in this audit. New naming work requires a new responsibility audit rather than extending this completed migration implicitly.
