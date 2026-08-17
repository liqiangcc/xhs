# 12 Canonical Read-only Command Audit

> Scope: audit and track the staged migration of `canonical list / stats / check` from the legacy CLI boundary. All three read-side vertical migrations are now completed.

## 1. Final dependency direction

The Canonical read side now follows one dependency direction:

```text
CLI / Interface
    ↓
Application read use case
    ↓
Outbound Port
    ↓
Filesystem adapter

Application / Domain own query semantics.
Infrastructure owns persistence and report publication.
Interface owns argv / transport / presentation only.
```

## 2. Migration order and status

The planned order is complete:

```text
1. canonical list   ✅ completed
2. canonical stats  ✅ completed
3. canonical check  ✅ completed
```

`list` proved the one-catalog read pattern. `stats` proved cross-catalog aggregation without leaking JSONL semantics. `check` completed the line by moving both integrity loading and optional report persistence behind explicit outbound capabilities.

## 3. `canonical list` — completed

Current flow:

```text
scripts/commands/canonical.js::runList
        ↓
app.canonical.list
        ↓
ListCanonicals
        ↓
CanonicalCatalogRepository.list()
        ↑
Filesystem Canonical catalog adapter
```

Application owns exact priority / answer-status filtering, `priorityRank()` ordering, frequency/id tie breaks, limit semantics, and `canonical_list.v1` projection.

Frozen behavior remains:

```text
schema_version = canonical_list.v1
default limit = 50
total_count = count after filters, before limit
returned_count = min(total_count, limit)
ordering = priorityRank ASC, frequency DESC, canonical_id ASC
filters = exact review_priority / answer_status equality
```

The migration preserves synchronous `runList()` timing for current local filesystem reads.

## 4. `canonical stats` — completed

Current flow:

```text
scripts/commands/canonical.js::runStats
        ↓
app.canonical.stats
        ↓
CanonicalStats Application
        ↓
CanonicalCatalogRepository.list()
QuestionCatalogRepository.list()
        ↑
Filesystem catalog adapters
```

The two Ports remain intentionally separate. The existing Dedup Question retrieval Port is not reused because `findByRefs + freshness revision` belongs to Dedup retrieval/CAS semantics, not Canonical statistics.

Application owns:

```text
canonical_count
canonical_question_id_count
assigned_question_rows
top ranking / limiting
canonical_stats.v1 DTO
```

Frozen behavior remains:

```text
schema_version = canonical_stats.v1
default top limit = 20
canonical_count = Canonical record count
canonical_question_id_count = distinct IDs declared by Canonical.question_ids
assigned_question_rows = Question rows whose canonical_id is truthy
top ordering = frequency DESC, canonical_id ASC
```

Cross-catalog aggregation remains storage-independent Application query semantics, not Filesystem behavior.

## 5. `canonical check` — completed

Previous legacy flow:

```text
CLI loads Canonical + Question JSONL
  ↓
CLI calls evaluateCanonicalIntegrity
  ↓
CLI optionally writes canonical_quality_report.json
```

Current flow:

```text
scripts/commands/canonical.js::runCheck
        ↓
app.canonical.check({ write_report })
        ↓
CheckCanonicalIntegrity Application
        ↓
CanonicalIntegrityChecker
        +
CanonicalQualityReportPublisher
        ↑
Filesystem adapters
```

Responsibilities are now separated:

| Responsibility | Current owner |
|---|---|
| root / `noWrite` mapping | Interface |
| Canonical + Question state loading | `CanonicalIntegrityChecker` Infrastructure adapter |
| integrity rules | Domain `evaluateCanonicalIntegrity` SSOT |
| whether a report is published | Application |
| where/how report is published | `CanonicalQualityReportPublisher` Infrastructure adapter |
| returned `canonical_quality_report.v1` | Application contract |
| process exit convention | Interface |

The Production filesystem checker remains synchronous because its actual work is synchronous JSONL loading/evaluation. Merge/Split already use `await integrityChecker.check()`, so a synchronous return remains fully compatible. `CheckCanonicalIntegrity` also supports promise-like checker/writer implementations, so this timing choice does not become an Application dependency.

Frozen compatibility behavior remains:

```text
report schema remains canonical_quality_report.v1
--noWrite suppresses canonical_quality_report.json
report.ok=false is still valid JSON output
canonical CLI process exit remains 0 when check returns ok=false
```

The last rule intentionally differs from `review integrity`, whose CLI returns a failure exit code when `ok=false`; that behavior was not normalized during migration.

## 6. Final CLI boundary

After all three read migrations, `scripts/commands/canonical.js` no longer imports or directly uses:

```text
loadCanonicalQuestions
loadQuestions
priorityRank
evaluateCanonicalIntegrity
writeJson
shouldWriteReports
```

The Canonical Interface now follows the intended boundary for both read and migrated mutation commands:

```text
parse syntax/options
→ construct Application DTO
→ call Application
→ present/emit result
→ preserve command-specific exit semantics
```

No Canonical read command owns JSONL loading, Domain evaluation, aggregation, sorting policy, or report persistence anymore.

## 7. Port responsibility summary

```text
CanonicalCatalogRepository
  → raw Canonical catalog records

QuestionCatalogRepository
  → raw Question catalog rows for read aggregation

CanonicalIntegrityChecker
  → global canonical_quality_report.v1 evaluation

CanonicalQualityReportPublisher
  → publish an already-produced quality report
```

Ports stay narrow. The report publisher does not decide whether writing is allowed; the checker does not write; catalog repositories do not perform DTO/query semantics.

## 8. Completion criteria

The read-side migration is complete when all of the following stay green:

```text
canonical list CLI → app.canonical.list
canonical stats CLI → app.canonical.stats
canonical check CLI → app.canonical.check

CLI has no Canonical/Question store imports
CLI has no Canonical integrity Domain import
CLI has no Canonical quality-report publisher call

--noWrite keeps canonical check report-free
check ok=false still exits zero
list/stats JSON contracts remain unchanged
full CI / semantic / evidence / generated-diff gates pass
```

## 9. Non-targets

This migration line did not change:

- Merge/Split/Canonicalize mutation semantics;
- Dedup Suggest/Decide/Apply;
- Canonical mutation transaction/recovery behavior;
- `review integrity` exit semantics;
- `src/domain/canonical/accept-policy.js`;
- historical ADR/review-plan wording.

Historical documents may retain old command snapshots. Current behavior is governed by current code/tests, `10_current_dedup_canonical_operations.md`, and this completed read-side migration record.
