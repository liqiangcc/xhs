# 12 Canonical Read-only Command Audit

> Scope: audit and track the staged migration of `canonical list / stats / check` from the legacy CLI boundary. `canonical list` and `canonical stats` have completed their vertical migrations; only `canonical check` remains pending.

## 1. Goal

The Canonical read-side migration follows one dependency direction:

```text
CLI / Interface
    ↓
Application read use case
    ↓
Outbound read Port
    ↓
Filesystem adapter

Application / Domain own query semantics.
Infrastructure owns persistence.
Interface owns argv / transport / presentation only.
```

No new business rule should be added to the remaining legacy `check` command body while it waits for migration.

## 2. Migration order and current status

The migration order remains:

```text
1. canonical list   ✅ completed
2. canonical stats  ✅ completed
3. canonical check  ← next / final read-side slice
```

`list` proved the one-catalog read pattern. `stats` then proved that storage-independent aggregation across Canonical and Question catalogs can also live in Application without pushing query semantics into Filesystem adapters.

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

Current responsibility split:

| Responsibility | Current owner |
|---|---|
| root / argv option mapping | Interface |
| Canonical record loading | Infrastructure adapter |
| priority + answer-status filtering | Application |
| priority ordering | Application using Domain `priorityRank()` SSOT |
| frequency / id tie-break ordering | Application |
| limit semantics | Application |
| `canonical_list.v1` DTO projection | Application |

The CLI no longer imports or calls `priorityRank()` for `list`, and `runList()` no longer reads `canonical_questions.jsonl` directly.

Frozen compatibility behavior remains:

```text
schema_version = canonical_list.v1
default limit = 50
total_count = count after filters, before limit
returned_count = min(total_count, limit)
ordering = priorityRank ASC, frequency DESC, canonical_id ASC
filters = exact review_priority / answer_status equality
```

Output record fields remain:

```text
canonical_id
canonical_title
review_priority
answer_status
frequency
question_ids
companies
primary_domain
primary_entities
```

The migration intentionally preserves the existing synchronous `runList()` call timing for local JSONL reads; separation of concerns did not require changing the command's calling convention.

## 4. `canonical stats` — completed

Previous flow:

```text
CLI
  ↓
load Canonical records
load Question rows
  ↓
count / distinct / rank / limit / DTO in CLI
```

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

The two catalog Ports are intentionally separate:

- `CanonicalCatalogRepository.list()` returns storage-agnostic Canonical records;
- `QuestionCatalogRepository.list()` returns storage-agnostic Question rows;
- neither adapter knows `canonical_stats.v1`, ranking, counting, or CLI flags.

Current responsibility split:

| Responsibility | Current owner |
|---|---|
| root / argv / limit mapping | Interface |
| Canonical JSONL loading | Canonical catalog Infrastructure adapter |
| Question JSONL loading | Question catalog Infrastructure adapter |
| distinct Canonical question-id aggregation | Application |
| assigned Question row aggregation | Application |
| top-Canonical ranking | Application |
| limit semantics | Application |
| `canonical_stats.v1` DTO projection | Application |

Frozen compatibility behavior remains:

```text
schema_version = canonical_stats.v1
default top limit = 20
canonical_count = Canonical record count
canonical_question_id_count = distinct IDs declared by Canonical.question_ids
assigned_question_rows = Question rows whose canonical_id is truthy
top ordering = frequency DESC, canonical_id ASC
```

Top row fields remain:

```text
canonical_id
canonical_title
frequency
companies
primary_entities
```

Important separation point:

> Cross-catalog aggregation is storage-independent query semantics. It belongs to Application, not to JSONL/Filesystem adapters.

The migration also preserves the existing synchronous `runStats()` calling convention.

## 5. `canonical check` — next / last

Current flow is still legacy:

```text
load Canonical records
load Question rows
  ↓
evaluateCanonicalIntegrity(records, questions)
  ↓
optionally write canonical_quality_report.json
  ↓
return canonical_quality_report.v1
```

Important existing reusable boundary:

```text
CanonicalIntegrityChecker Port
        ↑
createFsCanonicalIntegrityChecker
        ↓
evaluateCanonicalIntegrity Domain SSOT
```

Production `createApplication()` already constructs this checker for Merge/Split post-commit validation, but it is not yet exposed as a standalone read use case.

Current responsibilities mixed in `runCheck()`:

| Responsibility | Current owner | Target owner |
|---|---|---|
| root / noWrite option | Interface | Interface DTO |
| JSONL loading | Interface via legacy stores | existing FS integrity checker |
| integrity rules | Domain | Domain — keep |
| optional quality report persistence | Interface | explicit outbound report writer / Application side-effect boundary |
| response | Interface | Application result |

Frozen compatibility behavior:

```text
report schema remains canonical_quality_report.v1
--noWrite suppresses canonical_quality_report.json
report.ok=false is still valid JSON output
canonical CLI process exit remains 0 when check returns ok=false
```

The last rule intentionally differs from `review integrity`, whose CLI returns a failure exit code when `ok=false`. Do not normalize those exit semantics accidentally during migration.

Risk/complexity remains **medium-high** despite the existing checker, because report persistence is an explicit optional side effect.

## 6. Why Stats uses a separate Question catalog Port

The existing Dedup Question retrieval Port is intentionally not reused:

```text
DedupQuestionRetrievalRepository.findByRefs(refs)
→ Question facts + scoped freshness revision
```

That Port belongs to Dedup retrieval/freshness semantics. Canonical Stats only needs a read catalog and must not inherit Dedup refs or CAS evidence.

Therefore Stats uses:

```text
QuestionCatalogRepository.list()
```

This keeps bounded-context concerns separated while still avoiding filesystem knowledge in Application.

## 7. Next vertical slice: `canonical check`

The next implementation slice should be limited to `canonical check`.

Required shape:

```text
canonical check CLI
        ↓
app.canonical.check
        ↓
CheckCanonicalIntegrity Application
        ↓
CanonicalIntegrityChecker
        +
optional CanonicalQualityReportWriter
        ↑
Filesystem adapters
```

Rules:

1. Reuse the existing `CanonicalIntegrityChecker`; do not duplicate integrity rules or JSONL loading.
2. Model quality-report persistence as an explicit outbound capability rather than writing from CLI.
3. Preserve `--noWrite` exactly.
4. Preserve `canonical_quality_report.v1` exactly.
5. Preserve the unusual `report.ok=false → canonical CLI exit 0` behavior.
6. Do not change `review integrity` semantics.
7. Do not modify Merge/Split post-commit integrity checking while exposing standalone `check`.

## 8. Read-only migration completion criteria

After `check` migrates, `scripts/commands/canonical.js` should no longer import:

```text
loadCanonicalQuestions
loadQuestions
evaluateCanonicalIntegrity
writeJson   # Canonical quality report persistence
```

`priorityRank` already left the CLI with `list`; Canonical/Question counting and ranking left with `stats`.

The Canonical CLI should then be uniformly thin:

```text
parse syntax
→ construct DTO
→ call Application
→ present result
→ preserve command-specific exit semantics
```

## 9. Non-targets

This migration line does not change:

- Merge/Split/Canonicalize runtime;
- Dedup Suggest/Decide/Apply;
- Canonical mutation transaction semantics;
- Review integrity command;
- `src/domain/canonical/accept-policy.js`;
- historical ADR/review-plan wording.

Historical documents may retain old command snapshots. Current behavior is governed by current code/tests, `10_current_dedup_canonical_operations.md`, and this read-side migration audit.
