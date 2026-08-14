# 15 Canonical Naming Lifecycle Audit

> Rename status: completed. The Question-group Canonicalization lifecycle now uses one stable vocabulary and the Canonical mutation consistency boundary now uses the approved `Gateway` role. This was a behavior-free naming migration: persisted schemas, business rules, revision scope, transaction semantics, and post-commit validation were not changed.

## 1. Final lifecycle

The lifecycle is now:

```text
Dedup ApplyIntent
    ↓
ResolveQuestionGroupCanonicalizationUseCase
    ↓
CanonicalizationPlan
    ↓
QuestionGroupCanonicalizationPreparationCoordinator
    ↓
PlanQuestionGroupCanonicalizationMutationUseCase
    ↓
CanonicalMutationPlan
    ↓
ExecuteQuestionGroupCanonicalizationUseCase
    ↓
CanonicalMutationGateway
    ↓
FileCanonicalMutationGatewayAdapter
    ↓
post-commit validation
```

Stable lifecycle vocabulary:

```text
Resolve → Prepare → Plan → Execute
```

Each word has one meaning:

- `Resolve` resolves the business-level Canonicalization decision.
- `Prepare` gathers current facts, projection evidence, and opaque revisions; it remains an internal Coordinator.
- `Plan` builds the executable-shaped, storage-agnostic CanonicalMutationPlan.
- `Execute` crosses the mutation consistency boundary and validates the committed result.

Do not add overlapping lifecycle synonyms such as `Build`, `Handle`, `Process`, `Perform`, or `Run` for these same stages.

## 2. Two Plan values must remain separate

The architecture intentionally contains two different values.

### 2.1 CanonicalizationPlan

Persisted/wire schema remains:

```text
canonicalization_plan.v1
```

Meaning:

```text
resolved business decision for Question-group Canonicalization
```

It determines:

```text
create_canonical vs extend_existing_canonical
Canonical target identity
requested/effective title
planned Question ids
Decision provenance
```

It still explicitly carries:

```text
mutation_authorized = false
```

Therefore it is not a persistence mutation plan.

### 2.2 CanonicalMutationPlan

Schema remains:

```text
canonical_mutation_plan.v1
```

Meaning:

```text
storage-agnostic semantic state transition that may be preflighted and committed
```

It contains:

```text
opaque expected revisions
Canonical upserts/removals
Question rebindings
Review migrations
Answer invalidations/archives
index rebuild intent
history intent
```

Infrastructure alone decides how those semantic changes map to files or another persistence technology.

### 2.3 Invariant

`CanonicalizationPlan` and `CanonicalMutationPlan` must remain separate. Combining them would collapse the business-resolution boundary into the persistence-consistency boundary and would make caller-controlled mutation evidence easier to smuggle across layers.

## 3. Final Application names

### Resolve

```text
src/application/canonical/resolve-question-group-canonicalization.js
createResolveQuestionGroupCanonicalizationUseCase()
resolveQuestionGroupCanonicalization()
```

Responsibility:

```text
validate ready Dedup apply intent
inspect target Canonical identity
resolve absent vs existing
resolve create vs extend
resolve effective title
produce canonicalization_plan.v1
```

It does not collect all Question revisions and cannot commit.

### Prepare

```text
src/application/canonical/question-group-canonicalization-preparation-coordinator.js
createQuestionGroupCanonicalizationPreparationCoordinator()
prepareQuestionGroupCanonicalizationMutation()
```

Responsibility:

```text
re-inspect target identity
load resulting Question binding snapshots
load ownership snapshots
validate membership consistency
invoke Domain projection policy
collect opaque expected revisions
capture planned binding states
```

This remains an internal Application Coordinator and is not exposed as another public `app.canonical` capability.

### Plan

```text
src/application/canonical/plan-question-group-canonicalization-mutation.js
createPlanQuestionGroupCanonicalizationMutationUseCase()
```

Pure semantic plan factory:

```text
src/application/canonical/question-group-canonicalization-mutation-plan.js
createQuestionGroupCanonicalizationMutationPlan()
```

Responsibility:

```text
invoke Preparation Coordinator
validate prepared projection/revision evidence
produce canonical_mutation_plan.v1
remain side-effect free
```

### Execute

```text
src/application/canonical/execute-question-group-canonicalization.js
createExecuteQuestionGroupCanonicalizationUseCase()
executeQuestionGroupCanonicalization()
```

Responsibility:

```text
rebuild fresh mutation evidence
build CanonicalMutationPlan
preflight Gateway
commit Gateway
re-read committed state
post-commit validate projection and ownership
```

`Execute` is the only Question-group Canonicalization stage allowed to cross the mutation consistency boundary.

## 4. Final public Application surface

Production `app.canonical` now exposes:

```text
list
stats
check
merge
split
resolveQuestionGroupCanonicalization
planQuestionGroupCanonicalizationMutation
executeQuestionGroupCanonicalization
```

Retired public names are not retained as aliases:

```text
planQuestionGroup
planQuestionGroupMutation
canonicalizeQuestionGroup
```

Dedup Apply now reads naturally:

```text
prepareRelationApply
→ resolveQuestionGroupCanonicalization
→ executeQuestionGroupCanonicalization
```

Execution internally rebuilds mutation evidence immediately before preflight/commit, preserving the existing anti-forgery and concurrency semantics.

## 5. Canonical mutation consistency boundary

The retired name was:

```text
CanonicalMutationStore
```

The final Port is:

```text
src/ports/canonical-mutation-gateway.js
CanonicalMutationGateway
assertCanonicalMutationGateway()
```

Contract remains exactly:

```text
preflight(plan)
commit(plan, preflightResult)
```

The production implementation is:

```text
src/infrastructure/filesystem/file-canonical-mutation-gateway-adapter.js
FileCanonicalMutationGatewayAdapter
createFileCanonicalMutationGatewayAdapter()
```

`Gateway` is the correct approved outbound role because the boundary coordinates one atomic/recoverable state transition across multiple persistence concerns:

```text
Canonical records
Question bindings
Review progress/sessions
Answer state/archive
indexes
history
```

It is not a single-aggregate Repository.

## 6. Filesystem transaction behavior preserved

The filesystem Adapter still owns the same transaction mechanics as before the rename:

```text
opaque revision revalidation
mutation lock
staging
backups
prepared journal
multi-file publish
committed journal marker
rollback on normal failure
process-crash recovery on a later preflight
post-commit cleanup
```

The rename did not change:

```text
canonical_fs_transaction.v1
lock location
journal location
operation materialization order
rollback behavior
crash recovery behavior
fault-injection stages
```

The original fault-injection coverage was migrated to the Gateway-named tests rather than deleted.

## 7. Behavior-free compatibility boundary

The rename intentionally did not change:

```text
canonicalization_plan.v1
canonical_mutation_plan.v1
dedup_relation_apply_intent.v1
create vs extend semantics
mutation_authorized=false semantics
revision scope
projection policy
Question ownership rules
preflight/commit behavior
journal/rollback/recovery behavior
post-commit validation
Dedup Decision semantics
```

No compatibility aliases for the retired JavaScript names are kept in active `src` code. Keeping parallel old/new names would recreate the ambiguity the migration was intended to remove.

## 8. Separation of concerns after rename

Each component has one distinct reason to change:

```text
ResolveQuestionGroupCanonicalizationUseCase
  changes when business target-resolution semantics change

QuestionGroupCanonicalizationPreparationCoordinator
  changes when current-state evidence/projection orchestration changes

PlanQuestionGroupCanonicalizationMutationUseCase
  changes when semantic MutationPlan construction workflow changes

createQuestionGroupCanonicalizationMutationPlan
  changes when pure canonicalize mutation-plan semantics change

ExecuteQuestionGroupCanonicalizationUseCase
  changes when execute/post-validation workflow changes

CanonicalMutationGateway
  changes when the outbound consistency contract changes

FileCanonicalMutationGatewayAdapter
  changes when filesystem transaction mechanics change
```

The names now expose these separation points instead of hiding them behind overlapping `Plan / Prepare / Canonicalize / Store` terminology.

## 9. Regression gate

`test/canonical_naming_lifecycle_audit.test.js` now enforces the post-rename state:

```text
new lifecycle files and symbols must exist
old Application files must not exist
CanonicalMutationStore Port/file must not exist
old exported lifecycle symbols must not appear in active src JavaScript
Composition Root exposes only new public keys
Dedup Apply uses Resolve + Execute
Gateway Adapter contains the recoverable transaction implementation
```

The lifecycle rename is therefore no longer a documentation convention only; it is an executable architecture constraint.

## 10. Next naming work

Do not extend this slice by renaming unrelated grandfathered roles. Any remaining `Store`, `Writer`, `Provider`, or lifecycle ambiguity elsewhere should be audited separately against its actual responsibility before another rename is made.
