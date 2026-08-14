# 16 Repository Architecture Role Term Audit

> Audited head: `7386a61f38176e23aa4b3237fdec95fba9f54c8f`. Scope: classify remaining architecture-role terms after the completed Review and Canonical naming migrations. This audit is behavior-free: it changes no production symbol, persisted schema, CLI contract, business rule, revision scope, or transaction behavior.

## 1. Purpose

The repository now has a small approved architecture vocabulary, but older modules still contain generic role words such as `Store` and `Writer`. Those names must not be mass-renamed by spelling alone. The responsibility must be understood first, the separation point must be frozen, and only then may the role be renamed.

Approved outbound roles remain:

```text
Repository
QueryRepository
Gateway
Publisher
Reader
Generator
```

Words such as the following are migration debt when an approved role describes the responsibility more precisely:

```text
Store
Writer
Provider
Loader
Manager
Helper
Util
Service
Accessor
Fetcher
```

A path or folder name does not by itself decide the architecture role. Public/exported symbols must remain understandable outside their directory.

## 2. Classification rules

Each observed term is classified into one of four groups:

1. **settled** — already uses an approved role and should not be renamed again without a responsibility change;
2. **rename candidate** — responsibility is already clear enough for a behavior-free atomic rename;
3. **boundary audit required** — the current component has consistency/concurrency semantics that must be characterized before renaming;
4. **legacy technical module** — compatibility/script code that is not precedent for new architecture vocabulary and should be migrated or retired separately.

No compatibility alias should be introduced merely to make a rename easier. Repository-local callers, tests, Composition Root wiring, and documentation move in the same bounded slice.

## 3. Settled naming

### 3.1 Review

Review now consistently distinguishes:

```text
ReviewQueueStateCoordinator
ReviewProgressReader
ReviewProgressRepository
ReviewStrategyReader
ReviewIssueLinkReader
ReviewPlanPublisher
ReviewMutationGateway
```

`ReviewMutationGateway` is the cross-resource progress + session consistency boundary; `ReviewProgressRepository` owns the mutable progress aggregate; the Canonical-merge-specific `ReviewRepository` remains separate.

### 3.2 Canonical Question-group lifecycle

The completed lifecycle is:

```text
Resolve → Prepare → Plan → Execute
```

with:

```text
ResolveQuestionGroupCanonicalizationUseCase
QuestionGroupCanonicalizationPreparationCoordinator
PlanQuestionGroupCanonicalizationMutationUseCase
ExecuteQuestionGroupCanonicalizationUseCase
CanonicalMutationGateway
FileCanonicalMutationGatewayAdapter
```

`CanonicalizationPlan` and `CanonicalMutationPlan` remain separate concepts and must not be collapsed.

## 4. Active architecture naming debt

### 4.1 P0 — CanonicalQualityReportWriter → CanonicalQualityReportPublisher

Current Port:

```text
src/ports/services/canonical-quality-report-writer.js
CanonicalQualityReportWriter
assertCanonicalQualityReportWriter()
write(report)
```

Observed responsibility:

```text
Application decides whether a Canonical quality report should be published
Infrastructure decides how and where that report is persisted
```

This is publication, not generic writing. The target role is therefore:

```text
CanonicalQualityReportPublisher
assertCanonicalQualityReportPublisher()
publish(report)
```

Classification: **rename candidate**.

Why P0:

- the Port has one narrow outbound capability;
- its existing documentation already describes publication semantics;
- it has no transaction/concurrency protocol of its own;
- Review already provides a proven `Publisher` precedent;
- the rename can be mechanical and behavior-free.

### 4.2 P1 — RelationCandidateStore → RelationCandidatePublisher

Current write Port:

```text
src/ports/relation-candidate-store.js
RelationCandidateStore
replaceQueue(queue)
```

The read side is already separate:

```text
src/ports/repositories/relation-candidate-repository.js
RelationCandidateRepository
getPending(...)
```

The filesystem implementation replaces/publishes one pending review queue for a scope/seed. It does not represent a generic persistence Store and it does not own a multi-resource Canonical mutation transaction.

Target role:

```text
RelationCandidatePublisher
replaceQueue(queue)
```

`replaceQueue` may remain the operation name if its replacement semantics are useful at the call site; the architecture role is `Publisher`.

Classification: **rename candidate**.

This is P1 rather than P0 only to keep naming changes in small independently reviewable slices.

### 4.3 P2 — RelationDecisionStore → RelationDecisionGateway

Current write Port:

```text
src/ports/relation-decision-store.js
RelationDecisionStore
record(decision, {
  expected_queue_revision,
  expected_source_revisions
})
```

The read side is already separate:

```text
src/ports/repositories/relation-decision-repository.js
RelationDecisionRepository
getLatest(...)
```

The filesystem write implementation is more than an audit-log writer. Before appending the decision it coordinates consistency checks across the pending review queue and the source facts used by the decision, revalidates opaque revisions, acquires a lock, and rejects stale state.

Target role candidate:

```text
RelationDecisionGateway
record(...)
```

Classification: **boundary audit required**.

The likely role is `Gateway`, but it must not be renamed mechanically. A dedicated pre-rename slice must first freeze:

```text
queue revision semantics
Question/index source revision semantics
lock ownership and stale-state rejection
audit append atomicity
failure behavior
```

Only after those characteristics are executable tests should the Store → Gateway rename occur.

## 5. Legacy technical modules — deferred, not vocabulary precedent

The following `scripts/lib` modules remain legacy technical/compatibility modules:

```text
scripts/lib/answer_store.js
scripts/lib/canonical_store.js
scripts/lib/index_store.js
scripts/lib/issue_store.js
scripts/lib/question_store.js
scripts/lib/review_store.js
```

They are not approved examples of the `Store` architecture role. Do not mass-rename them in this audit. Rename, migrate, or retire each only when its remaining callers and compatibility obligations are understood.

Likewise, the directory name `src/ports/services` is not a reason to perform a bulk folder move. Public symbol roles are governed first; path restructuring is a separate concern and must have its own benefit and migration boundary.

## 6. What this audit deliberately does not do

This slice does not:

```text
rename production files or symbols
add compatibility aliases
change persisted schemas
change CLI JSON or exit semantics
change Domain rules
change revision coverage
change lock/journal/rollback behavior
move src/ports/services as a directory
rename scripts/lib compatibility modules
```

The purpose is to make the next changes predictable before touching code.

## 7. Next bounded slice

```text
next_target: CanonicalQualityReportWriter -> CanonicalQualityReportPublisher
```

That is the next implementation slice because it has the clearest responsibility and the smallest behavioral surface.

Expected atomic migration set:

```text
Port + assertion
filesystem Adapter / factory names
Composition Root wiring
Application dependency name
repository-local tests
naming/audit documentation
```

The operation should become `publish(report)` if the current adapter/callers can be migrated mechanically in the same slice. No `write()` or Writer compatibility alias should remain solely for backward compatibility inside this repository.

## 8. Subsequent sequence

After the P0 slice is green:

```text
P1 RelationCandidateStore -> RelationCandidatePublisher
P2 characterize RelationDecision consistency boundary
P2 RelationDecisionStore -> RelationDecisionGateway only after characterization is green
```

One semantic rename per bounded commit. Do not combine the Decision consistency audit with an unrelated rename.

## 9. Governance gate

For future architecture-role cleanup:

```text
understand responsibility
→ freeze the separation point
→ choose an approved role
→ migrate all repository-local callers atomically
→ remove old aliases
→ prove behavior unchanged with CI
```

The objective is semantic predictability, not fewer characters and not elimination of every historical occurrence of words such as `Store` or `Writer`.