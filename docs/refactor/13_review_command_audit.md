# 13 Review Command SoC / SRP Audit

> Scope: audit and track the staged migration of `review integrity / today / next / weak / prepare / mark`. `review integrity`, `review today`, `review next`, `review weak`, and `review prepare` have completed their vertical migrations; only `review mark` remains legacy.

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

No new Review business rule should be added to `scripts/commands/review.js`, `scripts/lib/review_store.js`, or `scripts/lib/review_scheduler.js` while `review mark` waits for migration.

## 2. Migration order and current status

```text
1. review integrity  ✅ completed
2. review today      ✅ completed
3. review next       ✅ completed
4. review weak       ✅ completed
5. review prepare    ✅ completed
6. review mark       ← next
```

`integrity` established the first genuinely read-only Review slice. `today` established the queue-state initialization boundary. `next` and `weak` proved multiple query policies can reuse that boundary. `prepare` now reuses the same queue state while separating query selection from Markdown publication.

## 3. Current mixed responsibilities outside migrated slices

`scripts/commands/review.js` now directly coordinates only the remaining `mark` concerns:

```text
Canonical existence check
ReviewProgress loading and persistence
missing-progress initialization
Review result input validation
ReviewProgress state transition
session-event construction and append
CLI exit semantics
run manifest writing
```

The CLI no longer owns Review queue loading, Question enrichment, issue-link loading, review strategy loading, prepare filtering, or Markdown plan rendering.

`review integrity`, `review today`, `review next`, `review weak`, and `review prepare` are all Application-backed vertical slices.

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

The legacy `scripts/lib/review_store.js` keeps compatibility wrappers for `mark`, but migrated queue use cases call Domain policy through Application rather than through the CLI.

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

Scoring and ordering are pure Review Domain policy:

```text
src/domain/review/ranking-policy.js
```

The declarative weight SSOT remains:

```text
config/review_strategy.json
```

Production migrated Review use cases obtain it through `ReviewStrategyProvider`. Domain interprets the values; it does not load config files.

### 4.3 Review weak-selection policy

Weak-card classification is a pure Review Domain predicate:

```text
src/domain/review/weak-policy.js
```

It preserves the legacy rule exactly:

```text
progress.status === 'weak'
OR mistake_count > 0
OR (review_count > 0 AND confidence < 0.5)
```

The policy does not rank rows, load progress, read strategy configuration, or know about CLI options.

## 5. Shared Review queue state boundary

`review today`, `review next`, `review weak`, and `review prepare` share:

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

No command-specific queue repository has been introduced.

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

CLI no longer owns progress initialization, due selection, ranking, issue-link enrichment, or Review strategy interpretation.

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

The migration reuses the exact Review queue Ports and policies established by `today`; no `Next`-specific filesystem repository exists.

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

The CLI only resolves Interface options and invokes `app.review.weak`.

## 10. `review prepare` — completed

`prepare` now separates query selection from plan publication.

Current flow:

```text
review prepare CLI
        ↓
app.review.prepare
        ↓
shared ReviewQueueState
        ↓
if days:
    next_review_at absent OR <= addDays(date, days)
else:
    isDue(progress, date)
        ↓
rankReviewRows()
        ↓
Application filters
        ↓
limit
        ↓
optional ReviewPlanWriter.write()
        ↓
review_prepare_result.v1
```

Selection remains behavior-compatible:

```text
if --days:
    upcoming rows
else:
    due rows
```

Additional filters remain:

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

The ordering boundary is preserved:

```text
select due/upcoming
→ rank
→ apply prepare filters
→ limit
```

Frozen output remains:

```text
schema_version = review_prepare_result.v1
ok = true
dry_run
target
plan_path
item_count
rows
```

### 10.1 ReviewPlanWriter boundary

The outbound Port is:

```text
src/ports/services/review-plan-writer.js
```

The production filesystem adapter is:

```text
src/infrastructure/filesystem/review-plan-writer.js
```

Responsibility split:

```text
Application
  → reuse queue state
  → select due/upcoming rows
  → apply filters
  → rank / limit
  → decide whether a plan is published

ReviewPlanWriter Port
  → one narrow write capability

Filesystem ReviewPlanWriter
  → sanitize target into a safe filename
  → render the historical Markdown table
  → write review/plans/<safe target>.md
  → return the relative plan path
```

The writer does **not** decide which cards belong in the plan.

### 10.2 `--noWrite` compatibility

`review prepare --noWrite` maps to:

```text
write_progress = false
write_plan = false
```

Therefore:

```text
missing progress is still synthesized in memory
progress.json is not written
the Markdown plan is not written
plan_path = null
dry_run = true
rows are still returned
```

With normal writes enabled, missing progress is persisted before the plan is published, preserving the historical queue-state behavior.

### 10.3 CLI cleanup achieved by prepare migration

The CLI no longer contains:

```text
loadReviewState()
questionMetadata()
canonicalRows()
dueRows()
upcomingRows()
safeName()
writePlan()
```

It also no longer imports Review prepare dependencies such as:

```text
node:fs
Question store
issue_store
review_scheduler
```

Those concerns now belong to Application, Ports, or Infrastructure.

## 11. `review mark` — next / highest risk

`mark` is the final legacy Review command and a formal mutation.

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

`mark` remains last because it is the only Review command whose correctness depends on an atomic/recoverable multi-file mutation boundary.

## 12. Recommended migration order

```text
1. review integrity  ✅
2. review today      ✅
3. review next       ✅
4. review weak       ✅
5. review prepare    ✅
6. review mark       ← next
```

The remaining work is intentionally mutation-focused:

- move Review result transition semantics to Domain SSOT without changing intervals or thresholds;
- model proposed progress/session changes as semantic mutation intent;
- add a `ReviewMutationStore` with preflight and recoverable commit semantics;
- keep Interface input aliases and output schema compatible.

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
ReviewPlanWriter          # completed
ReviewMutationStore       # pending mark
```

The existing Canonical-merge `ReviewRepository.loadMergeState()` remains merge-specific and must not be broadened into a generic Review CRUD repository.

## 14. Completion criteria

After `review mark` is migrated, `scripts/commands/review.js` should no longer directly import or use:

```text
legacy Canonical store
review_store persistence helpers
```

The following Review prepare/query dependencies have already been removed from the CLI:

```text
node:fs
legacy Question store
issue_store
review_scheduler config loader
Markdown rendering / filesystem plan writes
```

Final Interface responsibility:

```text
parse syntax/options
→ construct Application DTO
→ call app.review.<useCase>
→ emit result
→ preserve command-specific exit semantics
```

The Review Domain must not depend on filesystem paths, `process.argv`, config-file loading, or Markdown rendering.

## 15. Non-targets of this migration line

This line does not redesign:

- Review scheduling intervals or thresholds;
- `config/review_strategy.json` values;
- Canonical/Dedup behavior;
- Canonical merge Review migration behavior;
- existing Review data;
- Review plan Markdown format.

Business behavior is frozen first; structural ownership moves one vertical slice at a time.
