# 14 Naming Convention Audit

> Scope: audit the refactor against the previously agreed naming convention. This document does **not** introduce a shorter naming style. A public symbol should remain understandable even when seen outside its directory.

## 1. Naming convention to preserve

The agreed model is:

```text
Business concept        = BusinessNoun
Business operation      = Verb + BusinessObject + ArchitectureRole
Business decision       = BusinessObject + Concern + ArchitectureRole
Infrastructure impl     = Technology + PortName + AdapterRole
```

Approved role vocabulary remains intentionally small.

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

1. Public/exported names must remain understandable without relying on the path.
2. Directory/package provides bounded-context location, but does not replace responsibility in the symbol name.
3. Architecture-role suffixes should reveal why the component changes.
4. Do not introduce uncontrolled synonyms such as `Loader`, `Provider`, `Accessor`, `Fetcher`, `Manager`, `Helper`, `Util`, `Service`, or `Store` when an approved role fits.
5. `Writer` is also not an approved outbound role; existing write-side names are migration debt until their real persistence/publication responsibility is settled.
6. Do not shorten names merely to reduce character count. Long names are acceptable when every word contributes independent responsibility information.

The target is:

> the shortest name that still lets a reader infer business object, responsibility, and architectural role with minimal ambiguity.

## 2. Current Review naming status

### 2.1 Application UseCases — keep

```text
createReviewIntegrityUseCase
createReviewTodayUseCase
createReviewNextUseCase
createReviewWeakUseCase
createReviewPrepareUseCase
```

They preserve business context plus Application role and should not be shortened to ambiguous names such as `createPrepare()`.

### 2.2 `ReviewPlanPublisher` — completed

The former `ReviewPlanWriter` described a technical mechanism. The active naming is:

```text
ReviewPlanPublisher
assertReviewPlanPublisher()
FileReviewPlanPublisherAdapter
createFileReviewPlanPublisherAdapter()
publish(plan)
```

Responsibility split:

```text
Application chooses rows and decides whether publication occurs
Publisher exposes the outbound publication capability
File...Adapter owns safe path + Markdown + filesystem persistence
```

### 2.3 `ReviewStrategyReader` — completed

The former `ReviewStrategyProvider` used the vague non-standard `Provider` role. The active naming is:

```text
ReviewStrategyReader
assertReviewStrategyReader()
FileReviewStrategyReaderAdapter
createFileReviewStrategyReaderAdapter()
read()
```

Reader is the outbound capability requested by Application; the Adapter owns config-file mechanics.

### 2.4 `ReviewQueueStateCoordinator` — completed

The former `ReviewQueueStateLoader` was misleading because the component does more than load one resource. It coordinates:

```text
CanonicalCatalogRepository
QuestionCatalogRepository
ReviewProgressReader
ReviewProgressWriter
ReviewIssueLinkReader
ReviewStrategyReader
Domain progress initialization
optional progress persistence
queue row projection
```

The active Application role is now:

```text
ReviewQueueStateCoordinator
createReviewQueueStateCoordinator()
buildReviewQueueState(input)
```

All queue-backed Review UseCases use the same coordinator:

```text
review today
review next
review weak
review prepare
```

This is a naming-only responsibility clarification; queue-state behavior is unchanged.

### 2.5 `ReviewProgressWriter` — defer to `review mark`

`Writer` is outside the agreed outbound-role vocabulary, but it must **not** be mechanically renamed to `Publisher`:

```text
Review progress = persisted mutable state
Review plan     = published artifact
```

The correct final role depends on the mutation consistency design. Likely approved candidates are:

```text
ReviewProgressRepository
ReviewProgressGateway
```

Decision:

```text
flag now
settle together with review mark
```

### 2.6 Review mutation consistency boundary — role must follow responsibility

Earlier design notes used `ReviewMutationStore` provisionally. `Store` is not an approved outbound role and must not become production naming by inertia.

During `review mark`, determine the responsibility first:

```text
owns Review mutation persistence state
    → Repository may fit

coordinates atomic/recoverable consistency across progress + session persistence
    → Gateway may fit better
```

The suffix must follow the actual boundary.

## 3. Canonical namespace remains the largest readability risk

Current related names include:

```text
createPlanCanonicalizeQuestionGroupUseCase
createPrepareCanonicalizeQuestionGroup
createPlanCanonicalizeQuestionGroupMutationUseCase
createCanonicalizeQuestionGroupUseCase
```

The issue is not only length. Lifecycle vocabulary is asymmetric and the distinguishing responsibility is buried:

```text
Plan...
Prepare...
Plan...Mutation...
Canonicalize...
```

Before renaming, first establish the actual lifecycle and then move all related names atomically. Do not fix one symbol in isolation.

The Canonical pass must answer:

```text
Is prepare a Coordinator or private implementation detail?
Is mutation planning externally meaningful enough to remain a UseCase?
Should execution use Apply/Execute terminology?
Which phase words represent real business concepts rather than implementation mechanics?
```

## 4. Path, file, and symbol responsibilities

```text
path/package = location + bounded context
symbol       = independently understandable responsibility + architecture role
```

Both extremes are rejected.

Too vague:

```text
src/application/review/prepare.js
createPrepare()
```

Too mechanism-heavy:

```text
createFsReviewPlanMarkdownFileWriterService()
```

Preferred active style:

```text
src/application/review/review-prepare.js
createReviewPrepareUseCase()

src/application/review/review-queue-state-coordinator.js
createReviewQueueStateCoordinator()

src/ports/services/review-plan-publisher.js
assertReviewPlanPublisher()

src/infrastructure/filesystem/review-plan-publisher-adapter.js
createFileReviewPlanPublisherAdapter()
```

## 5. Governance rule

Do not introduce new role suffixes merely because they sound convenient:

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

Existing migration-era exceptions must be reviewed explicitly; they do not expand the approved vocabulary.

After the Review namespace stabilizes, add lightweight architecture/naming gates. Do not enforce filename length or arbitrary word counts.

## 6. Priority

```text
P0  Stop introducing non-standard role words
P0  ReviewPlanWriter          -> ReviewPlanPublisher ✅ completed
P0  ReviewStrategyProvider    -> ReviewStrategyReader ✅ completed
P0  ReviewQueueStateLoader    -> ReviewQueueStateCoordinator ✅ completed
P1  Settle ReviewProgressWriter together with review mark
P1  Name the Review mutation consistency boundary using an approved role
P1  Audit grandfathered CanonicalMutationStore terminology
P1  Resolve Canonical lifecycle near-collisions atomically
P2  Add automated naming architecture tests after Review migration stabilizes
```

## 7. Next step

The unambiguous Review naming corrections are complete. The next development slice is `review mark`.

Naming must be designed together with its consistency boundary:

```text
MarkReview... Application operation
Review result transition Domain role
Review mutation intent/plan value
approved outbound consistency role
concrete filesystem Adapter
```

Do not introduce `Service`, `Manager`, `Loader`, `Provider`, `Helper`, `Util`, `Store`, or another new role word to resolve uncertainty.

The governing test remains:

> A reader seeing only the symbol name should be able to infer the business object, the responsibility, and the architectural role with minimal ambiguity.
