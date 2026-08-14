# 12 Canonical Read-only Command Audit

> Scope: audit and track the staged migration of `canonical list / stats / check` from the legacy CLI boundary. `canonical list` has completed its vertical migration; `stats / check` remain pending.

## 1. Goal

The remaining Canonical read-side work follows one dependency direction:

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

No new business rule should be added to the legacy `stats / check` command bodies while they wait for migration.

## 2. Migration order and current status

The migration order remains:

```text
1. canonical list   ✅ completed
2. canonical stats  ← next
3. canonical check
```

`canonical list` 已完成第一条 read-side vertical slice. It now proves the intended pattern before the two broader queries migrate.

## 3. `canonical list` — completed

Previous flow:

```text
CLI options
  ↓
load canonical_questions.jsonl
  ↓
filter / sort / limit / DTO projection in CLI
```

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

## 4. `canonical stats` — next

Current flow remains legacy:

```text
load Canonical records
load Question rows
  ↓
count Canonicals
count unique Canonical.question_ids
count Question rows with canonical_id
rank Canonicals by frequency DESC / canonical_id ASC
  ↓
limit top rows
  ↓
project canonical_stats.v1
```

Current responsibilities mixed in `runStats()`:

| Responsibility | Current owner | Target owner |
|---|---|---|
| root / argv / limit parsing | Interface | Interface |
| Canonical JSONL loading | Interface via legacy store | Infrastructure |
| Question JSONL loading | Interface via legacy store | Infrastructure |
| unique question-id aggregation | Interface | Application query semantics |
| assigned row aggregation | Interface | Application query semantics |
| top-Canonical ranking | Interface | Application query semantics |
| DTO projection | Interface | Application result DTO |

Frozen compatibility behavior:

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

Risk/complexity: **medium**, because it composes two logical read sources.

Do not push these aggregations into a filesystem adapter merely because the current implementation uses JSONL. They are storage-independent query semantics.

Recommended next dependency shape:

```text
canonical stats CLI
        ↓
app.canonical.stats
        ↓
CanonicalStats Application
        ↓
Canonical catalog Port + Question read Port
        ↑
Filesystem adapters
```

Prefer reusing the newly established Canonical catalog read boundary rather than creating another Canonical loader with overlapping responsibility.

## 5. `canonical check` — last

Current flow:

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

Production `createApplication()` already constructs this checker for Merge/Split post-commit validation, but it is not exposed as a standalone read use case.

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

Risk/complexity: **medium-high** despite the existing checker, because report persistence is an explicit optional side effect.

## 6. Why `list` was first

`list` was selected first because it had:

- one data source;
- no write behavior;
- no cross-context aggregation;
- an existing Domain priority SSOT;
- the smallest failure surface for proving the read-side pattern.

That pattern is now established without expanding the mutation architecture or changing `stats/check` behavior.

## 7. Next vertical slice: `canonical stats`

The next implementation slice should be limited to `canonical stats`.

Rules:

1. CLI parses `limit`, delegates, and prints only.
2. Application owns aggregation, ranking, limiting, and `canonical_stats.v1` DTO semantics.
3. Infrastructure returns raw read state and does not know `canonical_stats.v1`.
4. Reuse `CanonicalCatalogRepository` for Canonical rows where practical.
5. Introduce only the narrow Question read capability needed by stats.
6. Preserve exact current counts, ranking, top row fields, and default limit.
7. Do not migrate `canonical check` in the same slice.

## 8. Read-only migration completion criteria

After `stats` and `check` also migrate, `scripts/commands/canonical.js` should no longer import:

```text
loadCanonicalQuestions
loadQuestions
evaluateCanonicalIntegrity
writeJson   # for Canonical read report persistence
```

`priorityRank` has already left the CLI as part of the completed `list` slice.

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
