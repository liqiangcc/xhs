# 14 Naming Convention Audit

> Scope: keep the refactor aligned with the previously agreed naming convention. This document does **not** introduce a shorter naming style. Public symbols must remain understandable outside their directory.

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

### 2.1 Application UseCases

```text
createReviewIntegrityUseCase
createReviewTodayUseCase
createReviewNextUseCase
createReviewWeakUseCase
createReviewPrepareUseCase
createReviewMarkUseCase
```

These names keep business context plus Application role and should not be shortened to ambiguous forms such as `createPrepare()` or `createMark()`.

### 2.2 ReviewPlanPublisher — completed

Former:

```text
ReviewPlanWriter
```

Active:

```text
ReviewPlanPublisher
assertReviewPlanPublisher()
FileReviewPlanPublisherAdapter
createFileReviewPlanPublisherAdapter()
publish(plan)
```

`Publisher` describes the outbound business capability; the filesystem Adapter owns safe path and Markdown mechanics.

### 2.3 ReviewStrategyReader — completed

Former:

```text
ReviewStrategyProvider
```

Active:

```text
ReviewStrategyReader
assertReviewStrategyReader()
FileReviewStrategyReaderAdapter
createFileReviewStrategyReaderAdapter()
read()
```

### 2.4 ReviewQueueStateCoordinator — completed

Former:

```text
ReviewQueueStateLoader
```

Active:

```text
ReviewQueueStateCoordinator
createReviewQueueStateCoordinator()
buildReviewQueueState(input)
```

The component coordinates multiple outbound capabilities, Domain progress initialization, optional CAS persistence, and queue projection; `Coordinator` matches the responsibility better than `Loader`.

### 2.5 ReviewProgressRepository — completed

Former:

```text
ReviewProgressWriter
```

Active:

```text
ReviewProgressRepository
assertReviewProgressRepository()
FileReviewProgressRepositoryAdapter
createFileReviewProgressRepositoryAdapter()
snapshot({ date })
save(progress, { expected_revision, date })
```

Why `Repository`:

```text
ReviewProgress is persisted mutable aggregate state
queue initialization reads a current snapshot
queue initialization may save a new aggregate state
save is compare-and-set against an opaque progress revision
```

It is deliberately separate from `ReviewProgressReader`, which remains a narrow read-only capability for integrity inspection.

No `Writer` compatibility alias remains in active Review architecture.

### 2.6 ReviewMutationGateway — completed

Earlier design notes used the provisional term:

```text
ReviewMutationStore
```

The actual responsibility proved to be broader than owning one persisted aggregate:

```text
coordinate progress + session consistency
cover both resources with one opaque revision
recheck that revision at commit
stage both filesystem writes
publish as an atomic/recoverable unit
recover an interrupted prepared transaction
```

Therefore the approved role is:

```text
ReviewMutationGateway
assertReviewMutationGateway()
FileReviewMutationGatewayAdapter
createFileReviewMutationGatewayAdapter()
snapshot({ date })
commit(review_mutation.v1)
```

`Gateway` communicates that Application crosses one consistency boundary without learning the two underlying files or transaction protocol.

No `ReviewMutationStore` production alias is introduced.

## 3. Final Review separation vocabulary

```text
ReviewIntegrityUseCase          # Application operation
ReviewTodayUseCase              # Application operation
ReviewNextUseCase               # Application operation
ReviewWeakUseCase               # Application operation
ReviewPrepareUseCase            # Application operation
ReviewMarkUseCase               # Application operation
ReviewQueueStateCoordinator     # shared Application orchestration

Review result Policy            # Domain state transition
Review mark Policy              # Domain validation/event semantics

ReviewProgressReader            # narrow read capability
ReviewProgressRepository        # mutable progress aggregate persistence
ReviewSessionReader             # narrow read capability
ReviewStrategyReader            # config read capability
ReviewIssueLinkReader           # issue-link read capability
ReviewPlanPublisher             # plan publication capability
ReviewMutationGateway           # cross-resource consistency capability
```

The existing Canonical-merge `ReviewRepository` remains a separate merge-specific capability and must not expand into generic Review CRUD.

## 4. Path, file, and symbol responsibilities

```text
path/package = location + bounded context
symbol       = independently understandable responsibility + architecture role
```

Good active examples:

```text
src/application/review/review-mark.js
createReviewMarkUseCase()

src/application/review/review-queue-state-coordinator.js
createReviewQueueStateCoordinator()

src/ports/repositories/review-progress-repository.js
assertReviewProgressRepository()

src/ports/repositories/review-mutation-gateway.js
assertReviewMutationGateway()

src/infrastructure/filesystem/review-mutation-gateway-adapter.js
createFileReviewMutationGatewayAdapter()
```

Rejected extremes:

```text
createMark()                            # too vague
createFsReviewProgressJsonWriter()     # implementation mechanism, no architecture role
ReviewEverythingService                # mixed responsibility + unapproved role
```

## 5. Review naming gates now encoded in tests

`test/review_naming_convention.test.js` freezes the active Review decisions:

```text
Coordinator instead of Loader
Publisher instead of Writer for plan publication
Reader instead of Provider for strategy retrieval
Repository instead of Writer for ReviewProgress persistence
Gateway instead of Store for cross-resource Review mutation consistency
```

Migration-era exceptions elsewhere in the repository do not expand the Review vocabulary.

## 6. Remaining repository-wide naming debt

Review is now settled. The largest remaining readability risk is Canonical lifecycle naming:

```text
createPlanCanonicalizeQuestionGroupUseCase
createPrepareCanonicalizeQuestionGroup
createPlanCanonicalizeQuestionGroupMutationUseCase
createCanonicalizeQuestionGroupUseCase
CanonicalMutationStore
```

The issue is not only length. Lifecycle vocabulary is asymmetric:

```text
Plan
Prepare
Plan...Mutation
Canonicalize
```

and `Store` remains grandfathered terminology.

This group should be reviewed atomically after Review migration because renaming one phase alone would make the lifecycle less predictable.

## 7. Governance rule

Do not introduce new architecture-role suffixes merely because they sound convenient:

```text
Loader
Provider
Accessor
Fetcher
Manager
Helper
Util
Service
Store
Writer
```

If none of the approved roles fits, clarify the responsibility before naming the component.

Do **not** enforce filename length or arbitrary word-count limits. Semantic predictability is the goal.

## 8. Completed Review naming sequence

```text
ReviewPlanWriter
→ ReviewPlanPublisher ✅ completed

ReviewStrategyProvider
→ ReviewStrategyReader ✅ completed

ReviewQueueStateLoader
→ ReviewQueueStateCoordinator ✅ completed

ReviewProgressWriter
→ ReviewProgressRepository ✅ completed

provisional ReviewMutationStore
→ ReviewMutationGateway ✅ completed
```

The governing test remains:

> A reader seeing only the symbol name should be able to infer the business object, the responsibility, and the architectural role with minimal ambiguity.
