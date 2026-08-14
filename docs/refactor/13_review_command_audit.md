# 13 Review Command SoC / SRP Audit

> Scope: freeze the completed vertical migration of `review integrity / today / next / weak / prepare / mark`. All six Review commands are now Application-backed; the CLI no longer owns Review business or persistence logic.

## 1. Target dependency direction

```text
CLI / Interface
    ↓
Application UseCase / Coordinator
    ↓
Domain Policy + outbound Port
                    ↑
             Infrastructure Adapter
```

The migration preserves legacy command behavior while moving ownership to explicit separation points.

## 2. Migration order and final status

```text
1. review integrity  ✅ completed
2. review today      ✅ completed
3. review next       ✅ completed
4. review weak       ✅ completed
5. review prepare    ✅ completed
6. review mark       ✅ completed
```

## 3. Review Application surface

Production `app.review` exposes:

```text
integrity
today
next
weak
prepare
mark
```

The CLI is now limited to:

```text
parse syntax/options
resolve Interface aliases
construct Application DTO
call app.review.<useCase>
emit result
preserve command exit semantics
write the generic run manifest
```

It no longer imports legacy Canonical/Review stores.

## 4. Domain SSOT

### 4.1 Progress scheduling

```text
src/domain/review/progress-policy.js
```

Owns:

```text
addDays()
defaultProgressItem()
ensureProgressItems()
isDue()
```

### 4.2 Ranking

```text
src/domain/review/ranking-policy.js
```

Owns score interpretation and deterministic queue ordering.

### 4.3 Weak classification

```text
src/domain/review/weak-policy.js
```

Frozen rule:

```text
progress.status === 'weak'
OR mistake_count > 0
OR (review_count > 0 AND confidence < 0.5)
```

### 4.4 Review result transition

```text
src/domain/review/review-result-policy.js
```

Owns the former legacy `applyReviewResult()` business rules unchanged:

```text
again / hard / good / easy
level clamp 0..5
confidence updates
difficulty updates
mistake_count updates
next-review intervals
mastered / weak / learning derivation
```

`scripts/lib/review_store.js` keeps only a compatibility wrapper that delegates to this Domain SSOT.

### 4.5 Mark metadata/event policy

```text
src/domain/review/review-mark-policy.js
```

Owns:

```text
oral-version = one_minute validation
quality-defect de-duplication
hard-failure de-duplication
feedback-closed-at YYYY-MM-DD validation
feedback-closed-at requires at least one quality-defect
ReviewSession event construction
```

## 5. Shared Review queue state

Queue queries share:

```text
src/application/review/review-queue-state-coordinator.js
```

Final flow:

```text
CanonicalCatalogRepository.list()
QuestionCatalogRepository.list()
ReviewProgressRepository.snapshot(date)
        ↓
ensureProgressItems() Domain policy
        ↓
if write_progress:
    ReviewProgressRepository.save(progress, expected_revision)
        ↓
optional ReviewIssueLinkReader.load()
ReviewStrategyReader.read()
        ↓
createReviewQueueRows()
```

`ReviewProgressRepository` uses compare-and-set persistence. A queue command holding a stale progress snapshot cannot overwrite a concurrent `review mark`.

`--noWrite` still synthesizes missing progress in memory but does not persist it.

## 6. `review integrity` — completed

```text
review integrity CLI
        ↓
app.review.integrity
        ↓
ReviewIntegrityUseCase
        ↓
CanonicalCatalogRepository
ReviewProgressReader
ReviewSessionReader
        ↓
Review integrity Domain policy
```

Output remains:

```text
schema_version = review_integrity.v1
```

Missing progress is reported but is not a hard failure. Malformed, duplicate, stale progress/session references remain hard failures. `ok=false` still maps to CLI exit 1.

## 7. `review today` — completed

```text
review today
→ ReviewQueueStateCoordinator
→ isDue()
→ rankReviewRows()
→ limit
→ review_today.v1
```

Frozen behavior:

```text
default limit = 20
missing progress synthesized
missing progress persisted unless --noWrite
optional --with-issues
```

## 8. `review next` — completed

```text
review next
→ ReviewQueueStateCoordinator
→ addDays(date, days)
→ next_review_at absent OR <= maxDate
→ rankReviewRows()
→ limit
→ review_next.v1
```

Frozen behavior:

```text
default days = 7
default limit = 20
already-due rows remain included
```

## 9. `review weak` — completed

```text
review weak
→ ReviewQueueStateCoordinator
→ isWeakReviewProgress()
→ rankReviewRows()
→ limit
→ review_weak.v1
```

No Weak-specific repository or loader exists.

## 10. `review prepare` — completed

```text
review prepare
→ ReviewQueueStateCoordinator
→ due/upcoming selection
→ rank
→ Application filters
→ limit
→ optional ReviewPlanPublisher.publish()
→ review_prepare_result.v1
```

Filters remain behavior-compatible:

```text
priority exact
status exact
domain exact
company substring
level substring
topic case-insensitive substring across title/entities/domain
```

`ReviewPlanPublisher` owns only publication. `FileReviewPlanPublisherAdapter` owns safe filename, Markdown format, and filesystem persistence.

## 11. `review mark` — completed

Final flow:

```text
review mark CLI
        ↓
app.review.mark
        ↓
ReviewMarkUseCase
        ↓
CanonicalCatalogRepository
ReviewMutationGateway.snapshot(date)
        ↓
ensureProgressItems()
applyReviewResult() Domain policy
normalizeReviewMarkInput() Domain policy
createReviewSessionEvent() Domain policy
        ↓
if --noWrite:
    return proposed mutation only
else:
    ReviewMutationGateway.commit(review_mutation.v1)
        ↓
review_mark_result.v1
```

Frozen Interface aliases remain:

```text
canonical id = --canonical-id or positional id
result       = --result or --status
```

Frozen output remains:

```text
schema_version = review_mark_result.v1
ok = true
dry_run
canonical_id
result
progress
session_event
session_path
```

## 12. Mark consistency boundary

The legacy risk was:

```text
saveProgress(...)
    ↓
appendSessionEvent(...)
```

A second-write failure could leave progress updated without the matching session event.

The migrated boundary is:

```text
ReviewMutationGateway
```

Its production implementation is:

```text
FileReviewMutationGatewayAdapter
```

The Gateway revision covers both:

```text
review/progress.json
review/sessions/<date>.json
```

Commit semantics:

```text
snapshot returns opaque revision
→ Application builds semantic review_mutation.v1
→ commit acquires Review mutation lock
→ recover stale pending journal if needed
→ compare revision again
→ stage progress + session
→ persist prepared journal
→ publish both files
→ mark journal committed
→ cleanup
```

Normal publish failure rolls already-published files back. A simulated/process crash may leave the prepared journal; the next Review persistence operation recovers it before proceeding.

This is an explicitly recoverable multi-file transaction rather than two hidden filesystem writes.

## 13. Queue/mark concurrency

`ReviewProgressRepository` and `ReviewMutationGateway` share the Review transaction directory/lock/recovery mechanism.

Queue persistence uses a progress-only revision:

```text
snapshot progress revision
→ synthesize missing items
→ save(progress, expected_revision)
```

Mark persistence uses a progress+session revision:

```text
snapshot mutation revision
→ build transition/event
→ commit(expected_revision)
```

Therefore:

```text
stale queue save cannot overwrite a completed mark
stale mark cannot overwrite a newer queue progress save
concurrent mark/session edits fail closed on revision mismatch
```

## 14. Final narrow capabilities

```text
CanonicalCatalogRepository
QuestionCatalogRepository
ReviewProgressReader          # integrity/read-only inspection
ReviewProgressRepository      # queue progress CAS persistence
ReviewSessionReader           # integrity/read-only inspection
ReviewStrategyReader
ReviewIssueLinkReader
ReviewPlanPublisher
ReviewMutationGateway         # mark consistency boundary
```

The Canonical-merge-specific `ReviewRepository.loadMergeState()` remains separate and must not become generic Review CRUD.

## 15. Completion criteria — satisfied

`scripts/commands/review.js` no longer imports or uses:

```text
node:fs
legacy Canonical store
legacy Question store
issue_store
review_store
review_scheduler
saveProgress
appendSessionEvent
applyReviewResult
Markdown plan rendering
```

The Review Domain does not depend on filesystem paths, config-file loading, CLI syntax, or Markdown rendering.

## 16. Non-targets

This migration does not redesign:

```text
review interval values
confidence/difficulty deltas
status thresholds
review_strategy.json weights
Review plan Markdown format
existing Review data schemas
Canonical/Dedup business behavior
```

Business behavior was frozen first; ownership and consistency boundaries changed without silently changing Review rules.
