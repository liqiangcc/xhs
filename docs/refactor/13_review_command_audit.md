# 13 Review Command SoC / SRP Audit

> Scope: audit the current `review prepare / today / next / weak / mark / integrity` command responsibilities before Production migration. This document does not change runtime behavior.

## 1. Goal

The Review namespace is still implemented primarily in `scripts/commands/review.js` plus legacy helpers in `scripts/lib/review_store.js` and `scripts/lib/review_scheduler.js`.

The target dependency direction is:

```text
CLI / Interface
    ↓
Application use case
    ↓
Domain policies + outbound Ports
                    ↑
             Infrastructure
```

The migration must preserve current behavior first. In particular, commands that look read-only today are not necessarily side-effect free.

No new Review business rule should be added to `scripts/commands/review.js`, `scripts/lib/review_store.js`, or `scripts/lib/review_scheduler.js` while these commands wait for migration.

## 2. Current mixed responsibilities

`scripts/commands/review.js` currently owns or directly coordinates all of the following:

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
review integrity scanning
filesystem session enumeration / JSON parsing
result DTOs
CLI exit semantics
run manifest writing
```

This is not one stable reason to change. It combines Interface, Application, Domain and Infrastructure responsibilities.

## 3. Legacy helper split points

### 3.1 `scripts/lib/review_store.js`

This file mixes persistence with business rules.

Infrastructure responsibilities currently inside it:

```text
loadProgress()
saveProgress()
appendSessionEvent()
filesystem paths / JSON read-write
```

Storage-independent Review rules currently inside the same file:

```text
defaultProgressItem()
ensureProgressItems()
isDue()
applyReviewResult()
addDays()
```

`applyReviewResult()` contains current Review scheduling semantics, including:

```text
again / hard / good / easy transitions
level clamp 0..5
confidence changes
difficulty changes
mistake_count changes
next-review intervals
mastered / weak / learning status derivation
```

These semantics must move to the Domain unchanged before the legacy helper is retired. Do not duplicate them in Application or CLI.

### 3.2 `scripts/lib/review_scheduler.js`

This file also mixes I/O and pure policy.

```text
loadReviewStrategy()   → config I/O
scoreReviewRow()       → scoring policy
rankReviewRows()       → ordering policy
```

`config/review_strategy.json` remains the declarative weight SSOT. Infrastructure should load/provide the strategy; pure Domain code should interpret it. A model/config change must not require CLI changes.

## 4. Shared review-state behavior that must be explicit

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

This produces an important compatibility rule:

> `review today`, `review next`, `review weak`, and `review prepare` are not pure reads by default.

If a Canonical lacks ReviewProgress, these commands synthesize a default progress item and persist it unless `--noWrite` is present.

Even with `--noWrite`, missing progress is still synthesized **in memory** and participates in the returned rows; only persistence is suppressed.

Migration must model this side effect explicitly in Application. It must not silently turn the commands into pure reads or, conversely, hide initialization inside a read repository.

## 5. Shared row projection and ranking

Current `questionMetadata()` + `canonicalRows()` join facts from:

```text
CanonicalQuestion
Question
ReviewProgress
optional IssueLink
```

They produce Review queue rows containing:

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

This join/projection is storage-independent query semantics. It belongs in Application or a pure Review query policy, not in Filesystem adapters.

Current due/upcoming/weak ranking eventually uses `rankReviewRows()` and the strategy weights from `config/review_strategy.json`.

## 6. `review integrity` audit

Current flow:

```text
load Canonical records
load ReviewProgress
enumerate review/sessions/*.json
parse session JSON
    ↓
collect malformed / duplicate / stale references
    ↓
review_integrity.v1
```

Current report semantics:

```text
hard failures =
    malformed progress items
  + duplicate progress canonical IDs
  + stale progress canonical IDs
  + stale/malformed session events

missing progress is reported
but does NOT count as a hard failure
```

Current output fields include:

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

Compatibility rule:

```text
review integrity result.ok=false
→ review CLI exits 1
```

This differs from `canonical check`, whose `ok=false` intentionally exits 0.

`review integrity` does not initialize or persist progress and does not mutate formal Review state. It is therefore the recommended **first Review vertical migration**.

Recommended shape:

```text
review integrity CLI
        ↓
app.review.integrity
        ↓
ReviewIntegrity Application / pure evaluator
        ↓
Canonical catalog read capability
ReviewProgress read capability
ReviewSession read capability
        ↑
Filesystem adapters
```

Filesystem adapters may report invalid JSON/parsing facts, but the meaning of duplicate/stale/missing Review references should remain storage-independent policy.

Do not reuse the existing `ReviewRepository.loadMergeState()` as a generic Review query repository. That Port is intentionally Canonical-merge-specific and carries merge concurrency evidence.

## 7. `review today` audit

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

`today` is the recommended first queue command after `integrity` because it establishes the shared Review state/query pattern with the smallest selector surface.

## 8. `review next` audit

Current flow reuses the same Review state and enriched rows, then selects rows whose `next_review_at` is absent or no later than `date + days`.

Frozen behavior:

```text
default days = 7
default limit = 20
schema_version = review_next.v1
missing progress initialization behavior = same as today
rows include current due rows as well as upcoming rows inside the horizon
ranking = shared review strategy
```

`next` should reuse the state/query boundaries proven by `today`; it should not create another filesystem loader.

## 9. `review weak` audit

Current weak selector is:

```text
progress.status === 'weak'
OR mistake_count > 0
OR (review_count > 0 AND confidence < 0.5)
```

Then rows are ranked with the same Review strategy and limited to 20 by default.

Frozen behavior:

```text
schema_version = review_weak.v1
returned_count
rows
optional --with-issues
missing progress initialization behavior = same as today/next
```

The weak predicate is business/query policy and must not live in CLI or Infrastructure after migration.

## 10. `review prepare` audit

`prepare` composes due/upcoming selection with additional filters and an optional Markdown plan write.

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
  → select/filter rows
  → decide whether a plan is published

ReviewPlanWriter Port / Infrastructure
  → safe path + Markdown/file publication
```

The writer must not decide which cards belong in the plan.

Migrate `prepare` only after `today/next/weak` have established the shared Review query model.

## 11. `review mark` audit

`mark` is the highest-risk Review command because it is a formal mutation.

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

Frozen mutation behavior includes:

```text
result alias: --result or --status
allowed oral-version: one_minute
feedback-closed-at requires YYYY-MM-DD
feedback-closed-at requires at least one quality-defect
--noWrite returns proposed progress/session event but writes neither progress nor session
```

### Current consistency risk

The current write order is:

```text
saveProgress(...)
    ↓
appendSessionEvent(...)
```

These are separate filesystem writes. If the second write fails after the first succeeds, ReviewProgress and ReviewSession can diverge.

This is a mutation consistency boundary and must be addressed during migration. Do not merely wrap the two legacy functions in an Application use case.

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

`mark` should therefore migrate last among the current Review commands.

## 12. Recommended migration order

```text
1. review integrity
2. review today
3. review next
4. review weak
5. review prepare
6. review mark
```

Rationale:

- `integrity` is genuinely read-only and has no initialization side effect;
- `today` establishes the shared Review state + implicit initialization boundary;
- `next` and `weak` reuse that query model with different selectors;
- `prepare` adds plan publication after query semantics are stable;
- `mark` is a cross-file formal mutation and needs an explicit consistency boundary.

Before or as part of the first queue migration, extract the current pure scheduling/progress semantics from the legacy helpers into Domain without changing behavior. Do not redesign intervals, thresholds or strategy weights in the same slice.

## 13. Port / responsibility guidance

Potential narrow capabilities should follow caller needs rather than generic CRUD:

```text
CanonicalCatalogRepository          # may reuse the current generic read-side Port
QuestionCatalogRepository           # may reuse current raw Question catalog reads
ReviewProgressReader / Store        # Review progress facts; write capability kept explicit
ReviewSessionReader                  # session facts for integrity/query evidence
ReviewStrategyProvider              # provides review_strategy.v1
ReviewIssueLinkReader               # optional issue URLs
ReviewPlanWriter                    # publishes an already-selected plan
ReviewMutationStore                 # atomic/recoverable formal Review mutation
```

Do not broaden the existing Canonical-merge `ReviewRepository` just to avoid creating Review-specific read/mutation Ports.

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

A later business-rule change should have one obvious place to edit and test.

## 15. Completion criteria

After the Review namespace is fully migrated, `scripts/commands/review.js` should no longer directly import or use:

```text
node:fs
legacy Canonical / Question stores
issue_store
review_store persistence helpers
review_scheduler config loader
ensureDir
```

The final Interface responsibility should be:

```text
parse syntax/options
→ construct Application DTO
→ call app.review.<useCase>
→ emit result
→ preserve command-specific exit code
```

The Review Domain must not depend on filesystem paths, `process.argv`, config-file loading or Markdown rendering.

## 16. Non-targets of this audit slice

This audit does not change:

- any Review command runtime behavior;
- Review scheduling intervals or thresholds;
- `config/review_strategy.json` values;
- Canonical/Dedup runtime;
- Canonical merge Review migration behavior;
- current Review files or session data.
