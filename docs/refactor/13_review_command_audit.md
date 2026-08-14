# 13 Review Command SoC / SRP Audit

> Scope: audit and track the staged migration of `review integrity / today / next / weak / prepare / mark`. `review integrity` has completed its vertical migration; the remaining Review commands are still legacy.

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
2. review today      ← next
3. review next
4. review weak
5. review prepare
6. review mark
```

`integrity` established the first `app.review` capability with a genuinely read-only vertical slice. The next slice should establish the shared Review queue state model through `review today` without pulling `next / weak / prepare / mark` into the same change.

## 3. Current mixed responsibilities outside migrated integrity

`scripts/commands/review.js` still directly coordinates:

```text
argv parsing / aliases / syntax validation
Canonical JSONL loading
Question JSONL loading
ReviewProgress loading and persistence
missing-progress initialization
Issue-link loading and mapping
review strategy loading
Question → Canonical metadata enrichment
due / upcoming selection
weak-card selection
review ranking
prepare filters
Markdown plan rendering and filesystem writing
Review result input validation
ReviewProgress state transition
session-event construction and append
result DTOs
CLI exit semantics
run manifest writing
```

`review integrity` is no longer part of this list: its state loading, session parsing and integrity evaluation have moved behind Application / Domain / Ports.

## 4. Legacy helper split points

### 4.1 `scripts/lib/review_store.js`

This file still mixes persistence with business rules.

Infrastructure responsibilities:

```text
loadProgress()
saveProgress()
appendSessionEvent()
filesystem paths / JSON read-write
```

Storage-independent Review rules:

```text
defaultProgressItem()
ensureProgressItems()
isDue()
applyReviewResult()
addDays()
```

`applyReviewResult()` contains current Review scheduling semantics:

```text
again / hard / good / easy transitions
level clamp 0..5
confidence changes
difficulty changes
mistake_count changes
next-review intervals
mastered / weak / learning status derivation
```

These semantics must move to Domain unchanged before the legacy helper is retired. Do not duplicate them in Application or CLI.

### 4.2 `scripts/lib/review_scheduler.js`

This file still mixes I/O and pure policy:

```text
loadReviewStrategy()   → config I/O
scoreReviewRow()       → scoring policy
rankReviewRows()       → ordering policy
```

`config/review_strategy.json` remains the declarative weight SSOT. Infrastructure should provide the strategy; pure Domain code should interpret it.

## 5. `review integrity` — completed

Previous legacy flow:

```text
CLI loads Canonical records
CLI loads ReviewProgress
CLI enumerates and parses review/sessions/*.json
  ↓
CLI computes duplicate / stale / malformed / missing state
  ↓
review_integrity.v1
```

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

### Responsibility split

```text
CanonicalCatalogRepository
  → raw Canonical records

ReviewProgressReader
  → current ReviewProgress facts

ReviewSessionReader
  → parsed session facts or parse_error with an opaque source label

Review integrity Domain policy
  → duplicate / stale / malformed / missing classification
  → hard-failure semantics

ReviewIntegrity Application
  → review_integrity.v1 DTO
  → maps opaque session source to the historical `file` output field

CLI
  → delegates and preserves process exit semantics
```

The existing Canonical-merge-specific `ReviewRepository.loadMergeState()` was intentionally not broadened or reused.

### Frozen integrity semantics

```text
hard failures =
    malformed progress items
  + duplicate progress canonical IDs
  + stale progress canonical IDs
  + stale/malformed session events

missing progress is reported
but does NOT count as a hard failure
```

Output remains:

```text
schema_version = review_integrity.v1
ok
canonical_count
progress_item_count
initialized_progress_count
missing_progress_count
missing_progress_sample (max 20)
duplicate_progress_canonical_ids
stale_progress_canonical_ids
malformed_progress_items
stale_session_events
hard_failure_count
```

Filesystem session enumeration remains `.json` only and sorted. Invalid session JSON is converted by Infrastructure into `parse_error = invalid_json`; Domain decides that this is a hard integrity failure.

Compatibility rule remains:

```text
review integrity result.ok=false
→ review CLI exits 1
```

This intentionally differs from `canonical check`, whose `ok=false` exits 0.

`review integrity` remains genuinely read-only: it does not initialize missing ReviewProgress and does not write progress/session state.

## 6. Shared queue-state behavior — still pending

`loadReviewState()` currently performs:

```text
load Canonical records
load Question rows
load ReviewProgress
ensure missing progress items in memory
if !noWrite:
    save the initialized progress store
optionally load issue links
load review strategy
```

This produces a compatibility rule that must survive migration:

> `review today`, `review next`, `review weak`, and `review prepare` are not pure reads by default.

If a Canonical lacks ReviewProgress, these commands synthesize a default progress item and persist it unless `--noWrite` is present.

Even with `--noWrite`, missing progress is still synthesized in memory and participates in returned rows; only persistence is suppressed.

This side effect must become explicit Application orchestration. It must not be hidden inside a read repository.

## 7. Shared row projection and ranking

Current `questionMetadata()` + `canonicalRows()` join:

```text
CanonicalQuestion
Question
ReviewProgress
optional IssueLink
```

Review queue rows contain:

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

This join/projection is storage-independent query semantics. It belongs in Application or pure Review query policy, not Filesystem adapters.

Current due/upcoming/weak ranking uses `rankReviewRows()` and `config/review_strategy.json`.

## 8. `review today` — next

Current flow:

```text
loadReviewState()
  ↓
construct enriched Review rows
  ↓
isDue(progress, date)
  ↓
rankReviewRows(strategy)
  ↓
limit
  ↓
review_today.v1
```

Frozen behavior:

```text
default limit = 20
date = current/explicit review date
total_due_count = due count before limit
returned_count = limited row count
optional --with-issues adds issue_url
missing progress is synthesized in memory
missing progress is persisted unless --noWrite
```

Target Application owns initialization orchestration, due selection, ranking, limiting and DTO semantics. Repositories must not know `--noWrite`, `review_today.v1`, or scoring rules.

Before or in this slice, extract only the pure Review rules that `today` actually needs. Do not redesign intervals or ranking weights.

## 9. `review next` — pending

Frozen behavior:

```text
default days = 7
default limit = 20
schema_version = review_next.v1
missing progress initialization behavior = same as today
rows include current due rows as well as upcoming rows inside the horizon
ranking = shared review strategy
```

`next` should reuse the Review state/query boundaries established by `today`.

## 10. `review weak` — pending

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

## 11. `review prepare` — pending

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

Migrate `prepare` only after `today/next/weak` establish the shared Review query model.

## 12. `review mark` — last / highest risk

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

## 13. Port / responsibility guidance

Current/new narrow capabilities should follow caller needs:

```text
CanonicalCatalogRepository      # already reused by review integrity
QuestionCatalogRepository       # reusable for queue enrichment
ReviewProgressReader            # now exists for integrity; future write kept separate
ReviewSessionReader             # now exists for integrity/session facts
ReviewStrategyProvider          # future provider for review_strategy.v1
ReviewIssueLinkReader           # optional issue URLs
ReviewPlanWriter                # publishes selected plans
ReviewMutationStore             # atomic/recoverable formal Review mutation
```

Do not broaden the Canonical-merge `ReviewRepository` just to avoid Review-specific Ports.

## 14. Domain SSOT guidance

Current rules must be moved, not copied:

```text
review_store.js::applyReviewResult
  → Review result transition Domain SSOT

review_store.js::defaultProgressItem / ensureProgressItems / isDue
  → Review progress/scheduling Domain policy

review_scheduler.js::scoreReviewRow / rankReviewRows
  → Review ranking Domain policy

config/review_strategy.json
  → declarative ranking-weight SSOT
```

`loadReviewStrategy()` belongs to Infrastructure/config provision, not Domain.

`src/domain/review/integrity-policy.js` is now the SSOT for Review integrity classification only; it must not absorb queue scheduling or mutation rules.

## 15. Completion criteria

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

## 16. Non-targets

This migration line does not change:

- Canonical/Dedup runtime;
- Canonical merge Review migration behavior;
- current Review interval or ranking values;
- `today/next/weak/prepare/mark` runtime until their own slices;
- current Review files or session data except when a later explicitly authorized mutation slice does so.
