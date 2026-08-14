# 15 Canonical Naming Lifecycle Audit

> Scope: freeze the real responsibilities of the Question-group Canonicalization flow before renaming it. This audit follows the previously agreed naming convention: names must remain understandable outside their directory, architecture roles come from the approved vocabulary, and shortening is never allowed to erase responsibility.

## 1. Why this audit exists

The current Canonical flow contains several near-collision names:

```text
createPlanCanonicalizeQuestionGroupUseCase
createPrepareCanonicalizeQuestionGroupUseCase
createPlanCanonicalizeQuestionGroupMutationUseCase
createCanonicalizeQuestionGroupMutationPlan
createCanonicalizeQuestionGroupUseCase
CanonicalMutationStore
createFsCanonicalMutationStore
```

The problem is not character count. The problem is that lifecycle words are asymmetric and overloaded:

```text
Plan...
Prepare...
Plan...Mutation...
Canonicalize...
```

A reviewer has to reconstruct the lifecycle before they can tell which component only resolves business intent, which gathers concurrency evidence, which builds executable mutation intent, and which actually commits state.

This document does not collapse those responsibilities. It makes them explicit first.

## 2. Two plans are intentionally different concepts

The current architecture contains two distinct plan values and both must remain.

### 2.1 `CanonicalizationPlan`

Current schema:

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
requested title
preserve-existing vs use-requested title
planned Question ids
Decision provenance
```

It explicitly carries:

```text
mutation_authorized = false
```

Therefore this value is **not** an executable persistence plan.

### 2.2 `CanonicalMutationPlan`

Current schema:

```text
canonical_mutation_plan.v1
```

Meaning:

```text
storage-agnostic semantic mutation intent that can be preflighted/committed
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

Infrastructure decides how those semantics map to files or another storage mechanism.

### 2.3 Naming invariant

Do not merge these concepts into one generic `Plan` object.

```text
CanonicalizationPlan = what the business operation should become
CanonicalMutationPlan = what semantic state transition will be committed
```

The lifecycle names around them must make this distinction obvious.

## 3. Current lifecycle by real responsibility

### Stage A — resolve business Canonicalization

Current entry:

```text
createPlanCanonicalizeQuestionGroupUseCase
```

Actual responsibility:

```text
validate ready Dedup apply intent
inspect current Canonical target identity
resolve absent vs existing target
resolve create vs extend
resolve effective title
produce canonicalization_plan.v1
```

It does **not**:

```text
load all Question bindings
project final Canonical aggregate state
collect all mutation revisions
build canonical_mutation_plan.v1
commit anything
```

Therefore `Plan` is too broad at this stage. The distinctive responsibility is target/business **resolution**.

Approved target:

```text
ResolveQuestionGroupCanonicalizationUseCase
```

Target factory/function/file direction:

```text
createResolveQuestionGroupCanonicalizationUseCase()
resolveQuestionGroupCanonicalization()
src/application/canonical/resolve-question-group-canonicalization.js
```

Production Application key:

```text
canonical.resolveQuestionGroupCanonicalization
```

## 4. Stage B — prepare current mutation evidence and projection

Current entry:

```text
createPrepareCanonicalizeQuestionGroupUseCase
```

Actual responsibility:

```text
re-inspect Canonical target identity
load every resulting Question binding snapshot
load Canonical ownership snapshots
validate ownership/binding consistency
invoke Domain Question-group projection policy
collect opaque expected revisions
capture planned Question binding states
```

It does **not**:

```text
make the original create-vs-extend business decision
construct canonical_mutation_plan.v1
preflight/commit mutation
publish state
```

This collaborator is not a top-level user-facing Application capability. It coordinates several outbound reads plus Domain projection for the mutation-planning stage.

Approved architecture role:

```text
Coordinator
```

Approved target:

```text
QuestionGroupCanonicalizationPreparationCoordinator
```

Target factory/function/file direction:

```text
createQuestionGroupCanonicalizationPreparationCoordinator()
prepareQuestionGroupCanonicalizationMutation()
src/application/canonical/question-group-canonicalization-preparation-coordinator.js
```

It should remain internal to the mutation planning/execution workflow and should **not** be added as another public `app.canonical` capability.

## 5. Stage C — plan executable Canonical mutation

Current entry:

```text
createPlanCanonicalizeQuestionGroupMutationUseCase
```

Current pure factory:

```text
createCanonicalizeQuestionGroupMutationPlan
```

Actual responsibility:

```text
invoke the preparation Coordinator
validate prepared projection/revision evidence
convert prepared semantic state into canonical_mutation_plan.v1
remain side-effect free
```

This is the one stage where the verb **Plan** should be reserved: it produces the executable-shaped mutation plan.

Approved target Application capability:

```text
PlanQuestionGroupCanonicalizationMutationUseCase
```

Approved pure factory:

```text
createQuestionGroupCanonicalizationMutationPlan
```

Target files:

```text
src/application/canonical/plan-question-group-canonicalization-mutation.js
src/application/canonical/question-group-canonicalization-mutation-plan.js
```

Production Application key:

```text
canonical.planQuestionGroupCanonicalizationMutation
```

This keeps the distinction visible near the beginning of the name:

```text
Resolve... = resolve business CanonicalizationPlan
Plan...Mutation = build executable CanonicalMutationPlan
```

## 6. Stage D — execute Canonicalization

Current entry:

```text
createCanonicalizeQuestionGroupUseCase
```

Actual responsibility:

```text
rebuild fresh mutation evidence inside Application
build CanonicalMutationPlan
preflight mutation boundary
commit mutation boundary
re-read committed Canonical/Question ownership state
post-commit validate projection and ownership
return execution result
```

The current verb `Canonicalize` names the business operation but does not make its lifecycle position explicit when compared with the three preceding near-collision names.

Approved target:

```text
ExecuteQuestionGroupCanonicalizationUseCase
```

Target factory/function/file direction:

```text
createExecuteQuestionGroupCanonicalizationUseCase()
executeQuestionGroupCanonicalization()
src/application/canonical/execute-question-group-canonicalization.js
```

Production Application key:

```text
canonical.executeQuestionGroupCanonicalization
```

`Execute` means exactly one thing in this lifecycle: cross the mutation consistency boundary and validate the committed result.

## 7. Final lifecycle vocabulary

The Question-group Canonicalization lifecycle should read:

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
post-commit validation
```

The stable lifecycle verbs are:

```text
Resolve → Prepare → Plan → Execute
```

Rules:

1. `Resolve` produces/resolves the non-authorizing business CanonicalizationPlan.
2. `Prepare` is an internal Coordinator that gathers current facts and projection evidence.
3. `Plan` is reserved for construction of the executable CanonicalMutationPlan.
4. `Execute` is reserved for preflight/commit/post-validation.
5. Do not add another lifecycle synonym such as `Build`, `Process`, `Handle`, `Perform`, or `Run` for the same stages.

## 8. `CanonicalMutationStore` naming decision

Current Port:

```text
CanonicalMutationStore
```

Its actual responsibility is broader than persistence ownership of one aggregate. It is the consistency boundary across semantic operations that may touch:

```text
Canonical records
Question bindings
Review progress/sessions
Answer state/archive
indexes
history
```

Its contract is:

```text
preflight(plan)
commit(plan, preflightResult)
```

and the filesystem implementation already owns:

```text
opaque revision revalidation
lock ownership
staging
backups
journal
multi-file publish
rollback
crash recovery
```

That responsibility matches the approved outbound role **Gateway**, not the grandfathered word `Store`.

Approved target Port:

```text
CanonicalMutationGateway
assertCanonicalMutationGateway()
```

Approved target Infrastructure implementation:

```text
FileCanonicalMutationGatewayAdapter
createFileCanonicalMutationGatewayAdapter()
```

Target files:

```text
src/ports/canonical-mutation-gateway.js
src/infrastructure/filesystem/file-canonical-mutation-gateway-adapter.js
```

Do not rename it to `CanonicalRepository`: it coordinates one atomic/recoverable consistency boundary across multiple persistence concerns rather than owning a single Canonical aggregate repository.

## 9. Public Application surface after rename

Current:

```text
canonical.planQuestionGroup
canonical.planQuestionGroupMutation
canonical.canonicalizeQuestionGroup
```

Target:

```text
canonical.resolveQuestionGroupCanonicalization
canonical.planQuestionGroupCanonicalizationMutation
canonical.executeQuestionGroupCanonicalization
```

The internal Preparation Coordinator remains absent from the public surface.

The public call chain in Dedup should become readable without opening implementation files:

```text
prepareRelationApply
→ resolveQuestionGroupCanonicalization
→ executeQuestionGroupCanonicalization
```

Execution internally rebuilds the mutation plan immediately before preflight/commit, preserving the existing anti-forgery/concurrency behavior.

## 10. Compatibility boundaries

The naming migration must be behavior-free.

Do **not** rename or change persisted/wire schemas in the same slice:

```text
canonicalization_plan.v1
canonical_mutation_plan.v1
dedup_relation_apply_intent.v1
```

Do **not** change:

```text
create vs extend semantics
mutation_authorized=false semantics
revision scope
projection policy
Question ownership rules
preflight/commit behavior
journal/rollback/recovery behavior
post-commit validation
Dedup decision semantics
```

Do not retain compatibility aliases for the old internal JavaScript names after all repository-local callers/tests are migrated. Parallel old/new names would recreate the ambiguity this audit is removing.

## 11. Atomic rename set

The next implementation slice must rename the lifecycle as one coordinated change rather than one symbol at a time.

```text
createPlanCanonicalizeQuestionGroupUseCase
→ createResolveQuestionGroupCanonicalizationUseCase

createPrepareCanonicalizeQuestionGroupUseCase
→ createQuestionGroupCanonicalizationPreparationCoordinator

createPlanCanonicalizeQuestionGroupMutationUseCase
→ createPlanQuestionGroupCanonicalizationMutationUseCase

createCanonicalizeQuestionGroupMutationPlan
→ createQuestionGroupCanonicalizationMutationPlan

createCanonicalizeQuestionGroupUseCase
→ createExecuteQuestionGroupCanonicalizationUseCase

CanonicalMutationStore
→ CanonicalMutationGateway

createFsCanonicalMutationStore
→ createFileCanonicalMutationGatewayAdapter
```

Public Application keys move in the same atomic slice.

## 12. Why this remains SoC / SRP compliant

The rename must **not** collapse stages simply because they share the phrase `QuestionGroupCanonicalization`.

Each component has a different reason to change:

```text
Resolve UseCase
  changes when business target-resolution semantics change

Preparation Coordinator
  changes when current-state evidence/projection orchestration changes

Plan Mutation UseCase
  changes when semantic mutation-plan construction changes

Execute UseCase
  changes when execution/post-validation workflow changes

CanonicalMutationGateway
  changes when the consistency contract changes

File...GatewayAdapter
  changes when filesystem transaction mechanics change
```

This is the separation point that naming should expose.

## 13. Next step

Perform one behavior-free atomic rename of the complete lifecycle and update all callers/tests/docs together.

After that rename is green, the next naming audit should examine other grandfathered `Store` names separately rather than expanding the Canonical slice.
