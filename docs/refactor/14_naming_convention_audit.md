# 14 Naming Convention Audit

> Scope: keep the refactor aligned with the previously agreed naming convention. Public symbols must remain understandable outside their directory; shortening must never erase responsibility.

## 1. Naming convention

```text
Business concept        = BusinessNoun
Business operation      = Verb + BusinessObject + ArchitectureRole
Business decision       = BusinessObject + Concern + ArchitectureRole
Infrastructure impl     = Technology + PortName + AdapterRole
```

Approved architecture roles remain intentionally small.

### Application

```text
UseCase
Command
Query
Result
Workflow
Coordinator
Saga
```

### Domain

```text
Rule
Policy
Calculator
Classifier
Selector
Specification
StateMachine
Factory
Event
Exception
```

### Outbound / persistence

```text
Repository
QueryRepository
Gateway
Publisher
Reader
Generator
```

### Interface

```text
Controller
Consumer
Listener
Job
Scheduler
Tool
CliCommand
Request
Response
```

### Infrastructure

```text
Adapter
Client
Entity
Mapper
Record
Properties
Configuration
```

Core constraints:

1. A public/exported name must remain understandable without its path.
2. Path/package adds bounded-context location but does not replace responsibility in the symbol name.
3. The role suffix should reveal why the component changes.
4. Do not introduce uncontrolled synonyms such as `Loader`, `Provider`, `Accessor`, `Fetcher`, `Manager`, `Helper`, `Util`, `Service`, `Store`, or `Writer` when an approved role fits.
5. Do not shorten names merely to reduce character count.
6. Existing grandfathered names are migration debt, not vocabulary precedent.

Target:

> the shortest name that still lets a reader infer business object, responsibility, and architectural role with minimal ambiguity.

## 2. Review naming — completed

The Review namespace now consistently uses the approved role vocabulary.

```text
ReviewPlanWriter
→ ReviewPlanPublisher ✅

ReviewStrategyProvider
→ ReviewStrategyReader ✅

ReviewQueueStateLoader
→ ReviewQueueStateCoordinator ✅

ReviewProgressWriter
→ ReviewProgressRepository ✅

provisional ReviewMutationStore
→ ReviewMutationGateway ✅
```

Final separation vocabulary:

```text
ReviewIntegrityUseCase
ReviewTodayUseCase
ReviewNextUseCase
ReviewWeakUseCase
ReviewPrepareUseCase
ReviewMarkUseCase
ReviewQueueStateCoordinator

ReviewProgressReader
ReviewProgressRepository
ReviewSessionReader
ReviewStrategyReader
ReviewIssueLinkReader
ReviewPlanPublisher
ReviewMutationGateway
```

`ReviewProgressRepository` owns mutable progress aggregate persistence with opaque-revision compare-and-set semantics. `ReviewMutationGateway` owns the cross-resource progress + session consistency boundary. The existing Canonical-merge `ReviewRepository` remains a separate merge-specific capability and must not expand into generic Review CRUD.

## 3. Canonical lifecycle naming — completed

The former Canonical Question-group lifecycle used overlapping phase language:

```text
Plan
Prepare
Plan...Mutation
Canonicalize
```

and the consistency boundary used the grandfathered role `Store`.

The completed lifecycle is now:

```text
Resolve → Prepare → Plan → Execute
```

with explicit responsibilities:

```text
ResolveQuestionGroupCanonicalizationUseCase
  → resolves the non-authorizing business CanonicalizationPlan

QuestionGroupCanonicalizationPreparationCoordinator
  → gathers current facts, projection evidence, and opaque revisions

PlanQuestionGroupCanonicalizationMutationUseCase
  → constructs the executable-shaped CanonicalMutationPlan

ExecuteQuestionGroupCanonicalizationUseCase
  → preflights, commits, and post-validates the mutation
```

The two Plan values remain intentionally separate:

```text
CanonicalizationPlan
schema = canonicalization_plan.v1
meaning = resolved business outcome
mutation_authorized = false

CanonicalMutationPlan
schema = canonical_mutation_plan.v1
meaning = storage-agnostic semantic state transition
```

They must not be collapsed into one generic Plan because they sit on opposite sides of the business-resolution / persistence-consistency separation point.

## 4. Canonical mutation boundary — completed

Former:

```text
CanonicalMutationStore
createFsCanonicalMutationStore
```

Active:

```text
CanonicalMutationGateway
assertCanonicalMutationGateway()

FileCanonicalMutationGatewayAdapter
createFileCanonicalMutationGatewayAdapter()
```

Why `Gateway`:

```text
one mutation may coordinate
Canonical records
Question bindings
Review state
Answer state/archive
indexes
history
```

The boundary exposes only:

```text
preflight(plan)
commit(plan, preflightResult)
```

while the filesystem Adapter owns revision revalidation, lock, staging, backups, journal, multi-file publication, rollback, and crash recovery.

This rename was behavior-free. It did not change:

```text
canonicalization_plan.v1
canonical_mutation_plan.v1
dedup_relation_apply_intent.v1
create/extend semantics
revision scope
projection and ownership rules
preflight/commit behavior
journal/rollback/recovery behavior
post-commit validation
```

No old `CanonicalMutationStore` or old Canonicalization lifecycle aliases remain in active source code.

## 5. Final public Canonical Application surface

```text
canonical.list
canonical.stats
canonical.check
canonical.merge
canonical.split
canonical.resolveQuestionGroupCanonicalization
canonical.planQuestionGroupCanonicalizationMutation
canonical.executeQuestionGroupCanonicalization
```

The Preparation Coordinator remains internal. Dedup Apply reads:

```text
prepareRelationApply
→ resolveQuestionGroupCanonicalization
→ executeQuestionGroupCanonicalization
```

Execution rebuilds fresh mutation evidence immediately before the Gateway boundary, preserving anti-forgery and concurrency guarantees.

## 6. Path, file, and symbol responsibilities

```text
path/package = location + bounded context
symbol       = independently understandable responsibility + architecture role
```

Good active examples:

```text
src/application/review/review-mark.js
createReviewMarkUseCase()

src/application/canonical/resolve-question-group-canonicalization.js
createResolveQuestionGroupCanonicalizationUseCase()

src/application/canonical/question-group-canonicalization-preparation-coordinator.js
createQuestionGroupCanonicalizationPreparationCoordinator()

src/ports/canonical-mutation-gateway.js
assertCanonicalMutationGateway()

src/infrastructure/filesystem/file-canonical-mutation-gateway-adapter.js
createFileCanonicalMutationGatewayAdapter()
```

Rejected extremes:

```text
createMark()                         # too vague
createFsCanonicalJsonWriter()        # mechanism without architecture role
CanonicalEverythingService          # mixed responsibility + unapproved role
```

## 7. Naming gates

Executable architecture tests now freeze the completed decisions:

```text
Review: Coordinator / Publisher / Reader / Repository / Gateway roles
Canonicalization: Resolve → Prepare → Plan → Execute
Canonical mutation consistency: Gateway, not Store
old Canonical lifecycle files/symbols/public keys must remain absent
CanonicalizationPlan and CanonicalMutationPlan must remain separate
```

These tests make the naming system an architecture constraint rather than a documentation preference.

## 8. Remaining repository-wide naming debt

Review and the Question-group Canonicalization lifecycle are settled. Remaining grandfathered names elsewhere must be audited separately against their actual responsibility before renaming.

Do not use the completed Canonical slice as permission to mass-rename unrelated `Store`, `Writer`, `Provider`, or lifecycle terms. For every future rename:

```text
understand responsibility first
freeze separation point
choose an approved role
rename all repository-local callers atomically
remove old aliases
prove behavior unchanged with CI
```

Do not enforce filename length or arbitrary word-count limits. Semantic predictability is the goal.

The governing test remains:

> A reader seeing only the symbol name should be able to infer the business object, the responsibility, and the architectural role with minimal ambiguity.
