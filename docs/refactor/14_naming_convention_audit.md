# 14 Naming Convention Audit

> Scope: audit the current refactor hotspots against the previously agreed naming convention. This document does **not** invent a shorter naming style. The governing rule remains: a symbol should be understandable even when seen outside its directory.

## 1. Naming convention to preserve

The agreed naming model is:

```text
Business concept        = BusinessNoun
Business operation      = Verb + BusinessObject + ArchitectureRole
Business decision       = BusinessObject + Concern + ArchitectureRole
Infrastructure impl     = Technology + PortName + AdapterRole
```

The architecture-role vocabulary is intentionally small and stable.

### 1.1 Application roles

```text
UseCase
Command
Query
Result
Workflow
Coordinator
Saga
```

### 1.2 Domain roles

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

### 1.3 Outbound / persistence roles

```text
Repository
QueryRepository
Gateway
Publisher
Reader
Generator
```

### 1.4 Interface roles

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

### 1.5 Infrastructure roles

```text
Adapter
Client
Entity
Mapper
Record
Properties
Configuration
```

### 1.6 Core constraints

1. A public/exported symbol must remain understandable without relying on its path.
2. Directory/package location adds context but must not replace responsibility in the symbol name.
3. The suffix should identify the architectural reason the component changes.
4. Do not create uncontrolled synonyms such as `Loader`, `Provider`, `Accessor`, `Fetcher`, `Manager`, `Helper`, `Util`, or `Service` when an approved role already describes the responsibility.
5. `Store` is also **not** an approved outbound role. Existing `*Store` names are migration debt / grandfathered terminology, not precedent for new naming.
6. Avoid technical mechanism names such as `read/write/load/save` when the business capability has a clearer architecture role.
7. Avoid names that combine multiple responsibilities or hide the distinguishing lifecycle phase in the middle of a long phrase.
8. A long name is acceptable when every word adds independent responsibility information. Length alone is not a reason to remove business or role semantics.

The target is not “shortest name”. The target is:

> the shortest name that still lets a reader infer business object, responsibility, and architectural role with minimal ambiguity.

## 2. Audit conclusion

The current refactor is structurally much clearer than the legacy code, but naming has started to drift in three places:

```text
A. non-standard role suffixes: Writer / Provider / Loader / Store
B. lifecycle phases whose names are not symmetric
C. near-collision names where the distinguishing responsibility is buried
```

This is primarily a naming-governance problem, not evidence that the current layer boundaries should be collapsed.

The change strategy is deliberately incremental: fix unambiguous read/publication roles first, then settle mutation names together with the final `review mark` consistency design.

## 3. Review namespace audit

### 3.1 Names that remain readable

The current public Application factories preserve business context plus architectural role:

```text
createReviewIntegrityUseCase
createReviewTodayUseCase
createReviewNextUseCase
createReviewWeakUseCase
createReviewPrepareUseCase
```

Their command API is predictable:

```text
app.review.integrity(...)
app.review.today(...)
app.review.next(...)
app.review.weak(...)
app.review.prepare(...)
```

These names are not candidates for shortening to ambiguous forms such as `createIntegrity()` or `createPrepare()`.

### 3.2 `ReviewPlanPublisher` — P0 completed

The former `ReviewPlanWriter` name described the filesystem mechanism even though the Port was already a publication boundary.

The active names are now:

```text
ReviewPlanPublisher
assertReviewPlanPublisher()
FileReviewPlanPublisherAdapter
createFileReviewPlanPublisherAdapter()
publish(plan)
```

Responsibility remains unchanged:

```text
Application chooses which rows belong in a Review plan
Application decides whether publication occurs
ReviewPlanPublisher publishes the selected plan
FileReviewPlanPublisherAdapter owns safe path + Markdown + filesystem persistence
```

No `Writer` compatibility alias is retained in the migrated Review architecture.

### 3.3 `ReviewStrategyReader` — P0 completed

The former `ReviewStrategyProvider` exposed one read-only capability and used a vague non-standard role word.

The active names are now:

```text
ReviewStrategyReader
assertReviewStrategyReader()
FileReviewStrategyReaderAdapter
createFileReviewStrategyReaderAdapter()
read()
```

The responsibility remains intentionally narrow:

```text
Reader  = outbound capability requested by Application
Adapter = concrete config-file implementation
Domain  = interprets strategy values; it does not load files
```

No `Provider` compatibility alias is retained in the migrated Review architecture.

### 3.4 `ReviewQueueStateLoader` — remaining naming candidate

`createReviewQueueStateLoader` does not merely load one resource. It coordinates:

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

`Loader` therefore both violates the role vocabulary and understates the responsibility.

Preferred direction after implementation review:

```text
ReviewQueueStateCoordinator
```

with an operation such as:

```text
buildReviewQueueState(input)
```

Because this collaborator is shared by all queue use cases and participates in progress persistence, its rename should be done as a separate slice rather than hidden inside the Publisher/Reader rename.

### 3.5 `ReviewProgressWriter` — defer until `review mark`

`Writer` is outside the agreed outbound-role vocabulary, but this port should **not** be mechanically renamed to `Publisher`:

```text
Review progress = persisted mutable state
Review plan     = published document/artifact
```

Possible approved roles may eventually be:

```text
ReviewProgressRepository
ReviewProgressGateway
```

but the correct answer depends on the final `review mark` consistency boundary.

Decision:

```text
flag now
settle with review mark
```

### 3.6 Review mutation consistency role — not yet named

Previous architecture notes used `ReviewMutationStore` as a provisional label. `Store` is not an approved outbound role, so that label is no longer treated as a production target.

During `review mark`, determine the capability first:

```text
persistence ownership of Review mutation state
    → consider Repository

transactional/consistency boundary over multiple persistence mechanisms
    → consider Gateway
```

The responsibility determines the suffix. Existing grandfathered `*Store` names elsewhere in the repository are not precedent for new Review naming.

## 4. Canonical namespace audit

Canonical currently has the highest naming-readability risk because one business flow is represented by multiple differently named lifecycle stages.

### 4.1 Current stages

```text
createPlanCanonicalizeQuestionGroupUseCase
createPrepareCanonicalizeQuestionGroup
createPlanCanonicalizeQuestionGroupMutationUseCase
createCanonicalizeQuestionGroupUseCase
```

The problem is not simply character count. The lifecycle vocabulary is asymmetric:

```text
Plan...
Prepare...
Plan...Mutation...
Canonicalize...
```

and the distinguishing responsibility often appears late in the symbol.

### 4.2 Required Canonical naming rule

Before renaming, establish one lifecycle vocabulary for this flow. The responsibilities must be distinguishable near the beginning or role-bearing end of the name.

The next Canonical naming pass must answer:

```text
Is the prepare stage a Coordinator or private implementation detail?
Is mutation planning externally meaningful enough to remain a UseCase?
Should execution use Apply/Execute terminology rather than the broad Canonicalize verb?
Can the phase be obvious without duplicating the entire business phrase?
```

Only after those questions are answered should the related names move together in one atomic rename.

## 5. Port naming consistency

A Port name should answer both:

```text
What business capability is requested?
What architectural role does the abstraction play?
```

Preferred Review examples now include:

```text
ReviewIssueLinkReader
ReviewPlanPublisher
ReviewStrategyReader
```

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
```

If an existing component uses one of these words, mark it as a grandfathered exception until its responsibility is reviewed. Do not let the exception expand the vocabulary.

## 6. Path, file, and symbol responsibilities

Path and symbol names have different jobs:

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

Over-specified by mechanism:

```text
createFsReviewPlanMarkdownFileWriterService()
```

Preferred active style:

```text
src/application/review/review-prepare.js
createReviewPrepareUseCase()

src/ports/services/review-plan-publisher.js
assertReviewPlanPublisher()

src/infrastructure/filesystem/review-plan-publisher-adapter.js
createFileReviewPlanPublisherAdapter()
```

File-name casing remains repository-consistent (`kebab-case`); semantic predictability matters more than character count.

## 7. Naming governance gates

Do not add a broad automated naming gate in the middle of the final Review mutation migration. First stabilize the Review namespace, then add lightweight architecture tests.

Recommended later checks:

```text
Application exported component names use approved Application roles
Domain exported decision components use approved Domain roles
Ports use approved outbound roles
named concrete infrastructure implementations use approved Infrastructure roles
new generic suffixes are rejected unless explicitly allow-listed
migration-era exceptions are enumerated rather than silently accepted
```

Initial forbidden/new-use candidates:

```text
Manager
Helper
Util
Provider
Loader
Fetcher
Accessor
Service
Store
Writer   # unless the naming convention is explicitly amended
```

Do **not** enforce filename length, word count, or arbitrary abbreviation rules.

## 8. Priority and change strategy

```text
P0  Stop introducing new non-standard role words
P0  ReviewPlanWriter       -> ReviewPlanPublisher ✅
P0  ReviewStrategyProvider -> ReviewStrategyReader ✅
P0/P1 ReviewQueueStateLoader -> ReviewQueueStateCoordinator (separate slice)
P1  Settle ReviewProgressWriter with review mark
P1  Choose an approved Review mutation consistency role during mark design
P1  Audit grandfathered CanonicalMutationStore naming
P1  Resolve Canonical lifecycle near-collisions atomically
P2  Add naming architecture tests after Review migration stabilizes
```

Sequencing rule:

> fix obvious read-only/publication naming first; settle persistence/mutation naming only once the consistency responsibility is explicit.

## 9. Next step

The two unambiguous public/outbound naming corrections are complete.

Next, review `ReviewQueueStateLoader` as its own naming/refactoring slice because its responsibility is broader than loading and includes orchestration plus optional persistence.

After that, implement `review mark` with naming as part of the architecture:

```text
MarkReview... Application operation
Review result transition Domain role
Review mutation intent/plan value
approved outbound consistency-boundary role
concrete filesystem Adapter
```

The governing test remains:

> A reader seeing only the symbol name should be able to infer the business object, the responsibility, and the architectural role with minimal ambiguity.
