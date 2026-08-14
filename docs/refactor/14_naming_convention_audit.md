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

The immediate goal is therefore **not** a broad rename. It is to stop role-vocabulary drift, fix low-risk obvious violations, and let mutation naming settle together with the final `review mark` consistency design.

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

Their command API is also predictable:

```text
app.review.integrity(...)
app.review.today(...)
app.review.next(...)
app.review.weak(...)
app.review.prepare(...)
```

These names are not candidates for shortening to ambiguous forms such as:

```text
createIntegrity()
createPrepare()
```

because directory context must not be required to understand exported symbols.

### 3.2 `ReviewPlanWriter` — P0 rename candidate

Current responsibility:

```text
Application chooses which rows belong in a Review plan
Application decides whether publication occurs
outbound port publishes the selected plan
filesystem implementation owns safe path + Markdown rendering + persistence
```

The existing port comment already describes this as a **publication boundary**. `Writer` therefore exposes an implementation mechanism instead of the business capability.

Preferred port name:

```text
ReviewPlanPublisher
```

Preferred concrete implementation naming pattern:

```text
FileReviewPlanPublisherAdapter
```

The exact factory/file rename may follow JavaScript conventions, but the semantic role should remain `Publisher` / `Adapter`.

### 3.3 `ReviewStrategyProvider` — P0 rename candidate

The port exposes one read-only capability: obtaining Review strategy data. `Provider` is vague and is outside the approved outbound vocabulary.

Preferred port name:

```text
ReviewStrategyReader
```

Preferred implementation pattern:

```text
FileReviewStrategyReaderAdapter
```

This keeps the distinction clear:

```text
Reader  = outbound capability requested by Application
Adapter = concrete infrastructure implementation
```

### 3.4 `ReviewQueueStateLoader` — P0/P1 rename candidate

`createReviewQueueStateLoader` does not merely load one resource. It coordinates:

```text
CanonicalCatalogRepository
QuestionCatalogRepository
ReviewProgressReader
ReviewProgressWriter
ReviewIssueLinkReader
ReviewStrategyProvider
Domain progress initialization
optional progress persistence
queue row projection
```

`Loader` therefore both violates the role vocabulary and understates the responsibility.

Because this is an internal Application collaborator that coordinates several capabilities, the preferred direction is:

```text
ReviewQueueStateCoordinator
```

with an operation such as:

```text
buildReviewQueueState(input)
```

If it later becomes an independently exposed application operation, then an explicit `...UseCase` / `...Query` name should be chosen instead. Do not replace `Loader` with `Manager`, `Service`, `Helper`, or `Util`.

### 3.5 `ReviewProgressWriter` — defer until `review mark`

`Writer` is outside the agreed outbound-role vocabulary, but this port should **not** be mechanically renamed to `Publisher`:

```text
Review progress = persisted mutable state
Review plan     = published document/artifact
```

Those are different semantics.

Possible approved roles may eventually be:

```text
ReviewProgressRepository
ReviewProgressGateway
```

but the correct answer depends on the final `review mark` mutation boundary. Renaming it immediately would risk two consecutive naming migrations.

Decision:

```text
flag now
settle with review mark
```

### 3.6 `ReviewMutationStore` — provisional architecture label only

Previous architecture notes used:

```text
ReviewMutationStore
```

as a convenient name for the atomic/recoverable mutation boundary. Under the agreed role vocabulary, however, `Store` is not an approved outbound role.

Therefore `ReviewMutationStore` must **not** be copied into production as if its naming were already settled.

During `review mark`, determine the actual capability first:

```text
if it represents persistence ownership of Review mutation state
    → consider Repository

if it represents a transactional/consistency boundary over multiple persistence mechanisms
    → consider Gateway
```

The responsibility determines the suffix; the old design label does not.

Existing `CanonicalMutationStore` / `FsCanonicalMutationStore` terminology is grandfathered naming debt and should be audited separately. It is not a precedent for introducing another `*Store`.

## 4. Canonical namespace audit

Canonical currently has the highest naming-readability risk because one business flow is represented by four differently named lifecycle stages.

### 4.1 The actual four stages

Code inspection shows these distinct responsibilities.

#### Stage 1 — business canonicalization plan

```text
createPlanCanonicalizeQuestionGroupUseCase
```

Responsibility:

```text
validate intent
resolve/create target canonical identity
produce the business canonicalization plan
```

#### Stage 2 — prepare current state

```text
createPrepareCanonicalizeQuestionGroup
```

Responsibility:

```text
load current canonical/question/ownership state
capture revisions / current facts
build the prepared state used by mutation planning
```

This name is especially inconsistent because the component lives in Application but has no approved Application role suffix.

#### Stage 3 — construct semantic mutation plan

```text
createPlanCanonicalizeQuestionGroupMutationUseCase
```

Responsibility:

```text
consume prepared state
construct expected revisions/facts/writes
produce a semantic mutation plan
```

#### Stage 4 — execute and verify mutation

```text
createCanonicalizeQuestionGroupUseCase
```

Responsibility:

```text
build the mutation plan
preflight integrity
commit mutation
post-commit integrity verification
handle mutation markers/results
```

### 4.2 Why these names are hard to scan

The problem is not simply the number of characters.

The lifecycle vocabulary is asymmetric:

```text
Plan...
Prepare...
Plan...Mutation...
Canonicalize...
```

and the distinguishing responsibility often appears late in the symbol:

```text
PlanCanonicalizeQuestionGroupUseCase
PlanCanonicalizeQuestionGroupMutationUseCase
```

A reader has to parse almost the whole symbol before discovering whether it means business planning or mutation planning.

### 4.3 Required Canonical naming rule

Before renaming, establish one lifecycle vocabulary for this flow. The four responsibilities must be distinguishable near the beginning or role-bearing end of the name.

A candidate direction could be based on concepts such as:

```text
Plan ... UseCase
Prepare ... Coordinator
Plan ... Mutation ... UseCase
Apply ... UseCase
```

but this document does **not** approve exact replacement names yet.

Reason: the rename must follow the actual responsibility boundaries and the existing external API surface, not grammatical preference alone.

The next Canonical naming pass should answer:

```text
Is Stage 2 a Coordinator or should it be private implementation detail?
Is Stage 3 externally meaningful enough to remain a UseCase?
Should Stage 4 use Apply/Execute terminology rather than the broad Canonicalize verb?
Can the lifecycle phase be made obvious without duplicating the whole business phrase?
```

Only after those questions are answered should the four names move together in one atomic rename.

## 5. Port naming consistency

The current refactor correctly avoids broad generic CRUD abstractions such as a universal Review repository. Preserve that.

A Port name should answer both:

```text
What business capability is requested?
What architectural role does the abstraction play?
```

Preferred examples:

```text
CanonicalCatalogRepository
QuestionCatalogRepository
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

If an existing legacy/refactor component uses one of these words, mark it as a grandfathered exception until its responsibility is reviewed. Do not let the exception expand the vocabulary.

## 6. Path, file, and symbol responsibilities

Path and symbol names have different jobs:

```text
path/package = location + bounded context
symbol       = independently understandable responsibility + architecture role
```

Therefore both extremes are rejected.

Too vague:

```text
src/application/review/prepare.js
createPrepare()
```

Over-specified by mechanism:

```text
createFsReviewPlanMarkdownFileWriterService()
```

Preferred style keeps context and role explicit without re-encoding every filesystem detail:

```text
src/application/review/review-prepare.js
createReviewPrepareUseCase()

src/ports/services/review-plan-publisher.js
assertReviewPlanPublisher()

src/infrastructure/filesystem/review-plan-publisher-adapter.js
createFileReviewPlanPublisherAdapter()
```

File-name casing may remain repository-consistent (`kebab-case`); the semantic rule matters more than character count.

## 7. Naming governance gates

Do not add a broad automated rename gate in the middle of the final Review mutation migration. First stabilize the Review namespace, then add lightweight architecture tests.

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

Do **not** enforce filename length, word count, or arbitrary abbreviation rules. The gate is for semantic predictability.

## 8. Priority and change strategy

```text
P0  Stop introducing new non-standard role words
P0  ReviewPlanWriter       -> ReviewPlanPublisher
P0  ReviewStrategyProvider -> ReviewStrategyReader
P0  ReviewQueueStateLoader -> ReviewQueueStateCoordinator (subject to implementation check)
P1  Settle ReviewProgressWriter with review mark
P1  Replace provisional ReviewMutationStore label with an approved role during mark design
P1  Audit grandfathered CanonicalMutationStore naming
P1  Resolve the four Canonical lifecycle near-collisions atomically
P2  Add naming architecture tests after Review migration stabilizes
```

The sequencing rule is important:

> fix obvious read-only/publication naming now; settle mutation naming only once the mutation consistency responsibility is explicit.

This minimizes rename churn.

## 9. Next step

Before implementing `review mark`, apply the low-risk Review naming corrections that do not depend on mutation design:

```text
ReviewPlanWriter       -> ReviewPlanPublisher
ReviewStrategyProvider -> ReviewStrategyReader
ReviewQueueStateLoader -> ReviewQueueStateCoordinator
```

Run the full CI after that rename-only slice.

Then design `review mark` with naming as part of the architecture:

```text
MarkReview... Application operation
Review result transition Domain role
Review mutation intent/plan value
approved outbound consistency-boundary role (not assumed *Store)
concrete filesystem Adapter
```

The governing test remains:

> A reader seeing only the symbol name should be able to infer the business object, the responsibility, and the architectural role with minimal ambiguity.
