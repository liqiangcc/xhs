# 12 Canonical Read-only Command Audit

> Scope: audit the remaining legacy `canonical list / check / stats` read-only command responsibilities before production migration. This document does not migrate runtime behavior.

## 1. Goal

The remaining Canonical read-only commands still live in `scripts/commands/canonical.js`. The purpose of this audit is to identify stable separation points before another vertical migration slice.

Target architecture remains:

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

No new business rule should be added to the legacy read-only command bodies while they wait for migration.

## 2. Current shared legacy boundary

`canonical.js` still directly imports and uses:

```text
scripts/lib/canonical_store.js::loadCanonicalQuestions
scripts/lib/question_store.js::loadQuestions
src/domain/canonical/priority-policy.js::priorityRank
src/domain/canonical/integrity-policy.js::evaluateCanonicalIntegrity
scripts/lib/io.js::writeJson
```

This means the Interface currently knows:

- filesystem-oriented stores and paths;
- Canonical filtering and ordering semantics;
- cross-Question/Canonical aggregation rules;
- global integrity evaluation;
- report persistence.

`merge`, `split`, and `suggest` no longer have this problem because they delegate to `createApplication()`.

## 3. `canonical list` audit

Current flow:

```text
CLI options
  ↓
load canonical_questions.jsonl
  ↓
filter review_priority
  ↓
filter answer_status
  ↓
sort priorityRank ASC
     frequency DESC
     canonical_id ASC
  ↓
limit
  ↓
project canonical_list.v1 DTO
```

Current responsibilities mixed in `runList()`:

| Responsibility | Current owner | Target owner |
|---|---|---|
| root / argv / option parsing | Interface | Interface |
| JSONL loading | Interface via legacy store | Infrastructure adapter |
| priority + answer-status filtering | Interface | Application read use case |
| priority ordering | Interface calls Domain policy | Application using Domain SSOT |
| frequency / id tie-break ordering | Interface | Application query semantics |
| limit | Interface | Application query semantics |
| `canonical_list.v1` projection | Interface | Application result DTO or thin presenter |

Frozen compatibility behavior:

```text
schema_version = canonical_list.v1
default limit = 50
total_count = count after filters, before limit
returned_count = min(total_count, limit)
ordering = priorityRank ASC, frequency DESC, canonical_id ASC
filters = exact review_priority / answer_status equality
```

Output record fields must remain:

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

Risk/complexity: **low**.

Recommended target slice:

```text
CanonicalCatalogRepository.list()
        ↓
ListCanonicals Application
        ↓
canonical list CLI delegate
```

Do not make the CLI call `priorityRank()` after migration.

## 4. `canonical stats` audit

Current flow:

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
| DTO projection | Interface | Application result DTO / presenter |

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

Risk/complexity: **medium** because it joins two logical read sources.

Do not push aggregation into the filesystem adapter merely because the current implementation uses JSONL. The aggregation is storage-independent query semantics.

## 5. `canonical check` audit

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
| optional quality report persistence | Interface | explicit outbound report writer / application side-effect boundary |
| response | Interface | Application result / presenter |

Frozen compatibility behavior:

```text
report schema remains canonical_quality_report.v1
--noWrite suppresses canonical_quality_report.json
report.ok=false is still valid JSON output
canonical CLI process exit remains 0 when check returns ok=false
```

The last rule intentionally differs from `review integrity`, whose CLI returns a failure exit code when `ok=false`. Do not normalize those exit semantics accidentally during migration.

Risk/complexity: **medium-high** despite the existing checker, because report persistence is an explicit optional side effect.

## 6. Migration order

Recommended order:

```text
1. canonical list
2. canonical stats
3. canonical check
```

Rationale:

### 1. `list` first

- one data source;
- no write behavior;
- no cross-context aggregation;
- existing Domain priority SSOT can be reused;
- smallest failure surface for proving the read-side vertical migration pattern.

### 2. `stats` second

- still pure read-only;
- exercises composition of Canonical + Question read state;
- establishes where storage-independent aggregation belongs.

### 3. `check` last

- can reuse the existing `CanonicalIntegrityChecker`;
- but must explicitly model optional report persistence;
- has unusual compatibility exit semantics that need preservation.

## 7. Next vertical slice: `canonical list`

The next implementation slice should be limited to `canonical list`.

Proposed dependency shape:

```text
scripts/commands/canonical.js::runList
        ↓
app.canonical.list
        ↓
ListCanonicals
        ↓
CanonicalCatalogRepository
        ↑
Filesystem Canonical catalog adapter
```

Rules:

1. CLI parses `priority`, `answer-status`, and `limit`, delegates, and prints only.
2. Application owns filtering, ordering, limiting, and output DTO semantics.
3. Domain `priorityRank()` remains the priority ordering SSOT.
4. Infrastructure only returns Canonical records; it does not know CLI flags or `canonical_list.v1`.
5. Preserve exact current JSON behavior before removing legacy code.
6. Do not migrate `stats` or `check` in the same slice.

## 8. Read-only migration completion criteria

After all three commands migrate, `scripts/commands/canonical.js` should no longer import:

```text
loadCanonicalQuestions
loadQuestions
priorityRank
evaluateCanonicalIntegrity
writeJson   # for Canonical read report persistence
```

The Canonical CLI should then be uniformly thin:

```text
parse syntax
→ construct DTO
→ call Application
→ present result
→ preserve command-specific exit semantics
```

## 9. Non-targets

This audit does not change:

- Merge/Split/Canonicalize runtime;
- Dedup Suggest/Decide/Apply;
- Canonical mutation transaction semantics;
- Review integrity command;
- `src/domain/canonical/accept-policy.js`;
- historical ADR/review-plan wording.

Historical documents may retain old command snapshots. Current behavior is governed by current code/tests, `10_current_dedup_canonical_operations.md`, and this migration audit for the remaining read-only commands.
