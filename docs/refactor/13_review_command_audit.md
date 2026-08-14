# 13 Review Command SoC / SRP Audit

> Scope: audit and track the staged migration of `review integrity / today / next / weak / prepare / mark`. `review integrity`, `review today`, `review next`, and `review weak` have completed their vertical migrations; `prepare / mark` remain legacy.

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

The migration preserves current behavior before redesigning Review business rules. Commands that look read-only are not necessarily side-effect free.

No new Review business rule should be added to `scripts/commands/review.js`, `scripts/lib/review_store.js`, or `scripts/lib/review_scheduler.js` while the remaining commands wait for migration.

## 2. Migration order and current status

```text
1. review integrity  ✅ completed
2. review today      ✅ completed
3. review next       ✅ completed
4. review weak       ✅ completed
5. review prepare    ← next
6. review mark
```

`integrity` established the first genuinely read-only Review slice. `today` established the queue-state initialization boundary. `next` proved horizon selection could reuse that boundary, and `weak` now proves another query slice can reuse the same queue state, projection, ranking, strategy and optional issue-link capabilities without creating another loader.

## 3. Current mixed responsibilities outside migrated slices

`scripts/commands/review.js` still directly coordinates the pending commands' concerns:

```text
ReviewProgress loading and persistence for prepare / mark
missing-progress initialization for prepare / mark
Issue-link loading for prepare
review strategy loading for prepare
prepare filters
Markdown plan rendering and filesystem writing
Review result input validation
ReviewProgress state transition
session-event construction and append
CLI exit semantics
run manifest writing
```

`review integrity`, `review today`, `review next`, and `review weak` are no longer part of those implementation responsibilities in the CLI.

## 4. Domain SSOT extraction status

### 4.1 Review progress scheduling policy

Current scheduling/progress rules are in:

```text
src/domain/review/progress-policy.js
```

It owns:

```text
addDays()
defaultProgressItem()
ensureProgressItems()
isDue()
```

The legacy `scripts/lib/review_store.js` keeps compatibility wrappers for pending commands, but those wrappers delegate migrated scheduling rules to the Domain policy.

`applyReviewResult()` remains pending because it belongs to the final `review mark` mutation slice. Its current rules still cover:

```text
again / hard / good / easy transitions
level clamp 0..5
confidence changes
difficulty changes
mistake_count changes
next-review intervals
mastered / weak / learning derivation
```

Those rules must move to Review Domain unchanged before the legacy `mark` path is retired.

### 4.2 Review ranking policy

Scoring and ordering are now pure Review Domain policy:

```text
src/domain/review/ranking-policy.js
```

The declarative weight SSOT remains:

```text
config/review_strategy.json
```

Production migrated Review use cases obtain it through `ReviewStrategyProvider`. Domain interprets the values; it does not load config files.

### 4.3 Review weak-selection policy

Weak-card classification is now a pure Review Domain predicate:

```text
src/domain/review/weak-policy.js
```

It preserves the legacy rule exactly:

```text
progress.status === 'weak'
OR mistake_count > 0
OR (review_count > 0 AND confidence < 0.5)
```

The policy does not rank rows, load progress, read strategy configuration or know about CLI options.

## 5. Shared Review queue state boundary

`review today`, `review next`, and `review weak` now share:

```text
src/application/review/review-queue-state.js
```

Current flow:

```text
CanonicalCatalogRepository.list()
QuestionCatalogRepository.list()
ReviewProgressReader.load()
        ↓
ensureProgressItems() Domain policy
        ↓
if write_progress:
    ReviewProgressWriter.write()
        ↓
optional ReviewIssueLinkReader.load()
ReviewStrategyProvider.load()
        ↓
createReviewQueueRows()
```

This preserves a critical compatibility rule:

> Review queue commands are not pure reads by default when ReviewProgress is missing.

For migrated queue commands:

```text
missing progress
→ synthesized in memory
→ participates in returned queue state
→ persisted unless --noWrite
```

`--noWrite` suppresses persistence only; it does not suppress in-memory initialization.

The same state loader should next be reused by the query side of `prepare`.

## 6. `review integrity` — completed

Current flow:

```text
review integrity CLI
        ↓
app.review.integrity
        ↓
ReviewIntegrity Application
        ↓
CanonicalCatalogRepository
ReviewProgressReader
ReviewSessionReader
        ↓
Review integrity Domain policy
```

Filesystem adapters own only persistence facts:

- progress JSON loading;
- session enumeration;
- session JSON parsing;
- invalid session JSON becomes `parse_error = invalid_json` evidence.

Domain owns the meaning of duplicate/stale/missing/malformed references.

Frozen output:

```text
schema_version = review_integrity.v1
ok
canonical_count
progress_item_count
initialized_progress_count
missing_progress_count
missing_progress_sample
  # max 20
duplicate_progress_canonical_ids
stale_progress_canonical_ids
malformed_progress_items
stale_session_events
hard_failure_count
```

Hard failures remain:

```text
malformed progress items
+ duplicate progress canonical IDs
+ stale progress canonical IDs
+ stale/malformed session events
```

Missing progress is reported but does **not** count as a hard failure.

CLI compatibility remains:

```text
review integrity result.ok=false
→ process exit 1
```

This intentionally differs from `canonical check`, whose `ok=false` exits 0.

## 7. `review today` — completed

Current flow:

```text
review today CLI
        ↓
app.review.today
        ↓
shared ReviewQueueState
        ↓
isDue() Domain policy
        ↓
rankReviewRows() Domain policy
        ↓
review_today.v1
```

Frozen behavior:

```text
default limit = 20
date = current / explicit review date
total_due_count = due count before limit
returned_count = limited row count
optional --with-issues adds issue_url
missing progress is synthesized
missing progress is persisted unless --noWrite
```

CLI no longer owns progress initialization, due selection, ranking, issue-link enrichment or Review strategy interpretation.

## 8. `review next` — completed

Current flow:

```text
review next CLI
        ↓
app.review.next
        ↓
shared ReviewQueueState
        ↓
maxDate = addDays(date, days)
        ↓
next_review_at absent OR <= maxDate
        ↓
rankReviewRows() Domain policy
        ↓
limit
        ↓
review_next.v1
```

Frozen behavior:

```text
schema_version = review_next.v1
default days = 7
default limit = 20
rows include already-due cards
rows include upcoming cards inside the horizon
missing progress initialization behavior = same as today
optional --with-issues = same as today
```

The migration intentionally reuses the exact Review queue Ports and policies established by `today`; no `Next`-specific filesystem repository was introduced.

## 9. `review weak` — completed

Current flow:

```text
review weak CLI
        ↓
app.review.weak
        ↓
shared ReviewQueueState
        ↓
isWeakReviewProgress() Domain policy
        ↓
rankReviewRows() Domain policy
        ↓
limit
        ↓
review_weak.v1
```

Frozen behavior:

```text
schema_version = review_weak.v1
returned_count
rows
default limit = 20
optional --with-issues
missing progress initialization = same as today / next
```

The selector remains:

```text
progress.status === 'weak'
OR mistake_count > 0
OR (review_count > 0 AND confidence < 0.5)
```

`review weak` now reuses the exact queue-state and ranking boundaries established by `today` / `next`. The CLI only resolves Interface options and invokes `app.review.weak`; it no longer loads Review state, selects weak cards, reads strategy configuration or enriches issue links itself.

No `Weak`-specific filesystem repository or duplicate queue loader was introduced.

## 10. `review prepare` — next

`prepare` composes due/upcoming selection with filters and optional Markdown plan publication.

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
topic          case-insensitive substring across:
               canonical_title
               primary_entities
               primary_domain.l1
               primary_domain.l2
```

Side effects:

```text
missing progress may be initialized/persisted
Markdown review/plans/<safe target>.md is written unless --noWrite
```

Output:

```text
schema_version = review_prepare_result.v1
ok = true
dry_run
plan_path
item_count
rows
```

Target separation:

```text
Application
  → reuse queue state / due or upcoming selection
  → filter rows
  → decide whether plan is published

ReviewPlanWriter Port / Infrastructure
  → path-safe Markdown/file publication
```

The writer must not decide which cards belong in the plan.

## 11. `review mark` — pending / highest risk

`mark` is a formal mutation.

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

The legacy write order remains:

```text
saveProgress(...)
    ↓
appendSessionEvent(...)
```

If the second write fails after the first succeeds, ReviewProgress and ReviewSession can diverge.

This must become an explicit consistency boundary rather than two Infrastructure calls hidden behind Application.

Recommended target:

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

## 12. Recommended migration order

```text
1. review integrity  ✅
2. review today      ✅
3. review next       ✅
4. review weak       ✅
5. review prepare    ← next
6. review mark
```

The remaining sequence stays the same because:

- `prepare` can now reuse the proven queue-state, selection and ranking boundaries while introducing a separate Markdown publication capability;
- `mark` requires a formal mutation consistency boundary and therefore remains last.

## 13. Port / responsibility guidance

Current/recommended narrow capabilities:

```text
CanonicalCatalogRepository
QuestionCatalogRepository
ReviewProgressReader
ReviewProgressWriter
ReviewSessionReader
ReviewStrategyProvider
ReviewIssueLinkReader
ReviewPlanWriter          # pending prepare
ReviewMutationStore       # pending mark
```

The existing Canonical-merge `ReviewRepository.loadMergeState()` remains merge-specific and must not be broadened into a generic Review CRUD repository.

## 14. Completion criteria

After the Review namespace is fully migrated, `scripts/commands/review.js` should no longer directly import or use:

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
→ preserve command-specific exit semantics
```

The Review Domain must not depend on filesystem paths, `process.argv`, config-file loading or Markdown rendering.

## 15. Non-targets of this migration line

This line does not redesign:

- Review scheduling intervals or thresholds;
- `config/review_strategy.json` values;
- Canonical/Dedup behavior;
- Canonical merge Review migration behavior;
- existing Review data.

Business behavior is frozen first; structural ownership moves one vertical slice at a time.
