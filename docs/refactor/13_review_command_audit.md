# 13 Review Command SoC / SRP Audit

> Scope: audit and track the staged migration of `review integrity / today / next / weak / prepare / mark`. `review integrity` and `review today` have completed their vertical migrations; the remaining Review commands are still legacy.

## 1. Target dependency direction

```text
CLI / Interface
    ↓
Application use case
    ↓
Domain policies + outbound Ports
                    ↑
             Infrastructure
```

The migration preserves current behavior before redesigning Review business rules. Commands that look read-only today are not necessarily side-effect free.

No new Review business rule should be added to `scripts/commands/review.js`, `scripts/lib/review_store.js`, or `scripts/lib/review_scheduler.js` while the remaining commands wait for migration.

## 2. Migration order and current status

```text
1. review integrity  ✅ completed
2. review today      ✅ completed
3. review next       ← next
4. review weak
5. review prepare
6. review mark
```

`integrity` established the first genuinely read-only Review vertical slice. `today` established the shared queue-state pattern, including the historically important missing-progress initialization side effect. `next` should now reuse the same state, projection and ranking boundaries rather than create another loader.

## 3. Current mixed responsibilities outside migrated slices

`scripts/commands/review.js` still directly coordinates the pending commands' concerns:

```text
argv parsing / aliases / syntax validation
Canonical JSONL loading
Question JSONL loading
ReviewProgress loading and persistence
missing-progress initialization for next / weak / prepare
Issue-link loading and mapping
review strategy loading
Question → Canonical metadata enrichment
upcoming selection
weak-card selection
prepare filters
Markdown plan rendering and filesystem writing
Review result input validation
ReviewProgress state transition
session-event construction and append
result DTOs
CLI exit semantics
run manifest writing
```

`review integrity` and `review today` are no longer part of these implementation responsibilities in the CLI.

## 4. Domain SSOT extraction status

### 4.1 Review progress scheduling policy

The following rules have moved from `scripts/lib/review_store.js` to:

```text
src/domain/review/progress-policy.js
```

Current Domain SSOT now owns:

```text
addDays()
defaultProgressItem()
ensureProgressItems()
isDue()
```

The legacy `review_store.js` keeps compatibility wrapper functions so pending commands still behave identically, but those wrappers delegate to the Domain policy rather than carrying copied rules.

`applyReviewResult()` remains in the legacy helper for now because it belongs to the final `review mark` mutation slice. It still contains:

```text
again / hard / good / easy transitions
level clamp 0..5
confidence changes
difficulty changes
mistake_count changes
next-review intervals
mastered / weak / learning status derivation
```

Those rules must eventually move to Review Domain unchanged before `mark` retires its legacy path.

### 4.2 Review ranking policy

The scoring and ordering rules have moved from `scripts/lib/review_scheduler.js` to:

```text
src/domain/review/ranking-policy.js
```

The legacy scheduler now only keeps compatibility wrappers plus config loading for pending legacy commands.

The declarative weight SSOT remains:

```text
config/review_strategy.json
```

Production migrated Review use cases obtain it through `ReviewStrategyProvider`; Domain interprets the values. Config-file loading does not occur in Domain.

## 5. `review integrity` — completed

Current flow:

```text
review integrity CLI
        ↓
app.review.integrity
        ↓
ReviewIntegrity Application
        ↓
Review integrity Domain policy
        ↓
CanonicalCatalogRepository
ReviewProgressReader
ReviewSessionReader
        ↑
Filesystem adapters
```

Responsibilities:

```text
CanonicalCatalogRepository
  → raw Canonical records

ReviewProgressReader
  → current ReviewProgress facts

ReviewSessionReader
  → parsed session facts or parse_error with opaque source label

Review integrity Domain policy
  → duplicate / stale / malformed / missing classification
  → hard-failure semantics

ReviewIntegrity Application
  → review_integrity.v1 DTO
  → maps opaque session source to historical `file` output field
```

Frozen behavior remains:

```text
hard failures =
    malformed progress items
  + duplicate progress canonical IDs
  + stale progress canonical IDs
  + stale/malformed session events

missing progress is reported
but does NOT count as a hard failure

review integrity result.ok=false
→ review CLI exits 1
```

The existing Canonical-merge-specific `ReviewRepository.loadMergeState()` was intentionally not broadened.

## 6. `review today` — completed

Previous flow:

```text
CLI loadReviewState()
  ↓
CLI synthesized missing progress and optionally wrote it
  ↓
CLI joined Canonical / Question / Progress / optional IssueLink
  ↓
CLI selected due rows
  ↓
legacy scheduler ranked rows
  ↓
CLI limited and projected review_today.v1
```

Current flow:

```text
review today CLI
        ↓
app.review.today
        ↓
ReviewToday Application
        ↓
CanonicalCatalogRepository
QuestionCatalogRepository
ReviewProgressReader
ReviewProgressWriter
ReviewStrategyProvider
ReviewIssueLinkReader
        ↓
Review progress Domain policy
Review ranking Domain policy
        ↑
Filesystem/config adapters
```

### Responsibility split

```text
Interface
  → resolves date
  → maps limit / with-issues / noWrite to Application DTO

Application
  → loads required facts through Ports
  → synthesizes missing ReviewProgress through Domain SSOT
  → explicitly decides whether initialized progress is persisted
  → joins Canonical / Question / Progress / optional IssueLink facts
  → selects due rows
  → applies Domain ranking
  → limits and returns review_today.v1

Infrastructure
  → reads/writes ReviewProgress
  → loads review_strategy.v1
  → reads optional issue-link facts
  → knows filesystem/config paths only

Domain
  → missing-progress defaults
  → due predicate
  → scoring/ranking semantics
```

### Frozen `today` compatibility behavior

```text
schema_version = review_today.v1
default limit = 20
date = current/explicit review date
total_due_count = due count before limit
returned_count = limited row count
optional --with-issues adds issue_url
```

The historically important side effect is preserved exactly:

```text
missing ReviewProgress
→ always synthesized in memory
→ participates in returned rows
→ persisted unless --noWrite
```

`--noWrite` suppresses persistence only; it does not suppress initialization in the returned model.

The Production filesystem implementation remains synchronous, preserving the existing direct `runToday()` calling convention.

### Queue row semantics established by `today`

The shared Application row projection joins:

```text
CanonicalQuestion
Question
ReviewProgress
optional IssueLink
```

and produces:

```text
canonical_id
canonical_title
review_priority
answer_status
frequency
primary_domain
primary_entities
companies
levels
question_ids
progress
optional issue_url
```

`companies` begins with Canonical companies and incorporates matching Question companies. `levels` comes from matching Question rows. Both preserve the current Chinese-locale ordering behavior.

This projection is storage-independent Application query semantics and should be reused by `next / weak / prepare`.

## 7. Shared queue-state behavior still used by legacy commands

`loadReviewState()` remains only for:

```text
review next
review weak
review prepare
```

It still performs:

```text
load Canonical records
load Question rows
load ReviewProgress
ensure missing progress items in memory
if !noWrite:
    save initialized progress
optionally load issue links
load review strategy
```

The compatibility rule therefore still applies to those three pending commands:

> they are not pure reads by default; missing progress is persisted unless `--noWrite` is present.

`review today` now models the same behavior explicitly in Application instead of hiding it inside a repository.

## 8. `review next` — next

Current pending behavior:

```text
loadReviewState()
  ↓
shared enriched rows
  ↓
next_review_at absent OR <= date + days
  ↓
shared ranking
  ↓
limit
  ↓
review_next.v1
```

Frozen behavior:

```text
default days = 7
default limit = 20
schema_version = review_next.v1
missing progress initialization behavior = same as today
rows include current due rows as well as upcoming rows inside the horizon
ranking = shared review strategy
```

The next slice should reuse:

```text
Review progress Domain policy
Review ranking Domain policy
shared Review queue row projection
CanonicalCatalogRepository
QuestionCatalogRepository
ReviewProgressReader / Writer
ReviewStrategyProvider
ReviewIssueLinkReader
```

Do not create another queue-state repository or duplicate `today` orchestration.

## 9. `review weak` — pending

Current weak selector:

```text
progress.status === 'weak'
OR mistake_count > 0
OR (review_count > 0 AND confidence < 0.5)
```

Frozen behavior:

```text
schema_version = review_weak.v1
returned_count
rows
optional --with-issues
missing progress initialization behavior = same as today/next
```

The weak predicate is business/query policy and must not remain in CLI or Infrastructure.

## 10. `review prepare` — pending

Selection:

```text
if --days:
    upcoming rows
else:
    due rows
```

Additional filters:

```text
priority       exact equality
status         exact progress.status equality
domain         exact primary_domain.l1 equality
company        substring match against enriched companies
level          substring match against enriched levels
topic          case-insensitive substring across canonical title/entities/domain
```

Side effects:

```text
missing progress may be initialized/persisted
Markdown review/plans/<safe target>.md is written unless --noWrite
```

Output remains `review_prepare_result.v1`.

Target separation:

```text
Application
  → select/filter rows
  → decide whether a plan is published

ReviewPlanWriter Port / Infrastructure
  → safe path + Markdown/file publication
```

Migrate `prepare` only after `next/weak` reuse the shared queue model.

## 11. `review mark` — last / highest risk

Current responsibilities include:

```text
Canonical existence check
result/status alias handling
oral-version validation
quality-defect de-duplication
hard-failure de-duplication
feedback-closed-at validation
progress initialization
applyReviewResult() state transition
ReviewProgress persistence
session-event construction
session append
review_mark_result.v1 projection
```

Frozen behavior includes:

```text
result alias: --result or --status
allowed oral-version: one_minute
feedback-closed-at requires YYYY-MM-DD
feedback-closed-at requires at least one quality-defect
--noWrite returns proposed progress/session event but writes neither
```

### Current consistency risk

The current write order remains:

```text
saveProgress(...)
    ↓
appendSessionEvent(...)
```

These are separate filesystem writes. If session append fails after progress persistence, ReviewProgress and ReviewSession diverge.

Do not simply wrap those two calls in an Application use case.

Required target:

```text
MarkReview Application
    ↓
Review Domain transition policy
    ↓
ReviewMutationPlan / ReviewMutationStore
    ↓
preflight + atomic/recoverable progress/session commit
```

`mark` therefore remains last.

## 12. Current Port / responsibility map

```text
CanonicalCatalogRepository
  → raw Canonical records

QuestionCatalogRepository
  → raw Question records for queue enrichment

ReviewProgressReader
  → current ReviewProgress facts

ReviewProgressWriter
  → persists an already-decided ReviewProgress store

ReviewSessionReader
  → session facts for integrity

ReviewStrategyProvider
  → review_strategy.v1 declarative weights

ReviewIssueLinkReader
  → optional issue-link facts

Future ReviewPlanWriter
  → publish selected plans only

Future ReviewMutationStore
  → atomic/recoverable formal Review mutation
```

The existing Canonical-merge `ReviewRepository` stays merge-specific.

## 13. Remaining Domain SSOT work

Already migrated:

```text
review_store.js::defaultProgressItem / ensureProgressItems / isDue / addDays
  → src/domain/review/progress-policy.js

review_scheduler.js::scoreReviewRow / rankReviewRows
  → src/domain/review/ranking-policy.js

review integrity classification
  → src/domain/review/integrity-policy.js
```

Still pending until `mark`:

```text
review_store.js::applyReviewResult
  → Review result transition Domain SSOT
```

A later business-rule change should have one obvious place to edit and test.

## 14. Completion criteria

After the whole Review namespace migrates, `scripts/commands/review.js` should no longer directly import or use:

```text
node:fs
legacy Canonical / Question stores
issue_store
review_store persistence helpers
review_scheduler config loader
ensureDir
```

Final Interface responsibility:

```text
parse syntax/options
→ construct Application DTO
→ call app.review.<useCase>
→ emit result
→ preserve command-specific exit code
```

The Review Domain must not depend on filesystem paths, `process.argv`, config-file loading or Markdown rendering.

## 15. Non-targets

This migration line does not change:

- Canonical/Dedup runtime;
- Canonical merge Review migration behavior;
- current Review interval or ranking values;
- `next/weak/prepare/mark` runtime until their own slices;
- current Review files or session data except through the already-characterized `today` progress initialization side effect.
