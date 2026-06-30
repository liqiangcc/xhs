# XHS Knowledge Assets

This repo turns Xiaohongshu interview-note data into a maintainable knowledge asset system:

`Question -> CanonicalQuestion -> Answer -> ReviewProgress`

The supported entrypoint is:

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

## Current Status

As of 2026-06-30, the M1-M8 core loop is implemented and pushed to `origin/master`: migration, validation, indexing, canonical question management, answer metadata validation/sync, review progress, issue-card rendering, and quality reporting.

Current data snapshot:

- 9,620 question rows, 9,362 valid rows
- 18 canonical questions
- 83 assigned question rows
- 18 review progress records
- 12 ready P0 answers; P0 missing answers is now 0
- 6 remaining missing answers are P1 canonical questions
- 0 GitHub issue links synced so far

The project is now in the content-coverage and real-review phase. The P0 answer pass is done; the next useful work is widening canonical coverage, syncing selected ready answers into GitHub Issues for mobile review, and recording real review results.

## Next Steps

1. Continue expanding canonical coverage with hotspot/entity suggestions; the near-term target is 200+ assigned question rows.
2. After accepting new canonical records, use `answer missing` / `answer init-batch` to prepare the next answer batch.
3. After each answer batch, run `answer validate`, `answer validate --strict`, `answer sync`, and `report quality`.
4. Use `issue sync` dry-run first, then `--apply` only for reviewed ready cards that should appear on GitHub.
5. Start the real review loop with `review today`, `review next`, and `review mark`.

```bash
node scripts/xhs.js canonical suggest --hotspot --limit 50
node scripts/xhs.js canonical suggest --entity Redis --limit 50
node scripts/xhs.js answer missing --priority P1
node scripts/xhs.js answer init-batch --priority P1 --limit 20
node scripts/xhs.js answer validate
node scripts/xhs.js answer validate --strict
node scripts/xhs.js answer sync
node scripts/xhs.js report quality
node scripts/xhs.js issue sync --priority P0 --answer-status ready --repo liqiangcc/xhs
node scripts/xhs.js review today --with-issues
node scripts/xhs.js review next --with-issues
node scripts/xhs.js review mark --canonical-id <cq_id> --result good
```

## Core Workflow

```bash
# Rebuild Question main data from note_tagged without changing source files
node scripts/xhs.js migrate build-questions
node scripts/xhs.js migrate build-questions --check

# Validate schemas, taxonomy, and question hashes
node scripts/xhs.js validate all

# Build or check query indexes
node scripts/xhs.js index build
node scripts/xhs.js index build --check

# Query the main Question store and indexes
node scripts/xhs.js query entity Redis --valid --slim
node scripts/xhs.js query company 美团 --valid --slim
node scripts/xhs.js query domain --l1 缓存 --valid --slim
node scripts/xhs.js query hotspot --canonical --slim
```

## Canonical Questions

Canonical questions group equivalent raw interview prompts into reusable knowledge assets.

```bash
node scripts/xhs.js canonical suggest --hotspot --limit 25
node scripts/xhs.js canonical suggest --entity Redis --limit 50
node scripts/xhs.js canonical accept --candidate-id <id> --canonical-id <cq_id>
node scripts/xhs.js canonical list --priority P0 --answer-status missing
node scripts/xhs.js canonical merge --target <cq_id> --source <cq_id> --reason <text>
node scripts/xhs.js canonical split --canonical-id <cq_id> --question-id <qid> --new-canonical-id <cq_id> --title <title>
node scripts/xhs.js canonical check
node scripts/xhs.js canonical stats
```

Important files:

- `data/questions/questions.jsonl`
- `data/questions/canonical_questions.jsonl`
- `data/indexes/*.json`
- `data/manifests/canonical/*.json`

`canonical suggest` always writes its business output to `data/manifests/canonical/canonical_candidates.json`. `--noManifest` only suppresses `data/manifests/runs/latest_*.json`; it does not suppress canonical candidate output.

## Answers

Answers are Markdown files bound to `canonical_id`.

```bash
node scripts/xhs.js answer init --canonical-id <cq_id>
node scripts/xhs.js answer init-batch --priority P1 --limit 20
node scripts/xhs.js answer missing --priority P1
node scripts/xhs.js answer status --missing
node scripts/xhs.js answer validate
node scripts/xhs.js answer validate --strict
node scripts/xhs.js answer sync
```

Answer files live at `review/answers/{canonical_id}.md`. The first line is required metadata:

```markdown
<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_example","version":1,"status":"draft","updated_at":"2026-06-30"} -->
```

`answer validate --strict` adds content-quality checks for ready answers: no TODO placeholders, required sections present, and non-empty ready sections.

## Review

Review progress is also bound to `canonical_id`.

```bash
node scripts/xhs.js review prepare --target redis --limit 20 --priority P0 --topic Redis
node scripts/xhs.js review prepare --target metro --limit 20 --days 7 --company 字节
node scripts/xhs.js review today --limit 20
node scripts/xhs.js review today --limit 20 --with-issues
node scripts/xhs.js review mark --canonical-id <cq_id> --result good --notes "<text>"
node scripts/xhs.js review mark --canonical-id <cq_id> --status good --notes "<text>"
node scripts/xhs.js review next --limit 20 --days 7 --with-issues
node scripts/xhs.js review weak --limit 20 --with-issues
```

Review data lives in:

- `review/progress.json`
- `review/sessions/{YYYY-MM-DD}.json`
- `review/plans/{target}.md`

`review prepare --noWrite` is a dry run: it returns rows without writing `review/plans/*.md`, `review/progress.json`, or run manifests.

## GitHub Issue Cards

GitHub issues are optional mobile-friendly review cards. The source of truth remains local: canonical questions, answer Markdown, and review progress are still keyed by `canonical_id`.

```bash
node scripts/xhs.js issue render --canonical-id <cq_id>
node scripts/xhs.js issue sync --canonical-id <cq_id> --repo liqiangcc/xhs
node scripts/xhs.js issue sync --priority P0 --answer-status ready --repo liqiangcc/xhs --apply
node scripts/xhs.js issue check
```

`issue sync` is a dry run by default. Add `--apply` to create or update GitHub issues through `gh`. Local issue links live in `review/issue_links.json`.

Review issue cards use managed labels for filtering:

```bash
gh issue list --label "priority:P0"
gh issue list --label "domain:缓存"
gh issue list --label "review:weak"
gh issue list --label "answer:ready"
```

`issue sync --apply` keeps `priority:*`, `answer:*`, `domain:*`, and `review:*` labels in sync while preserving unrelated manual labels.

## GitHub Actions

The repository has three management workflows:

```text
.github/workflows/ci.yml
.github/workflows/xhs-manage.yml
.github/workflows/xhs-weekly-report.yml
```

Common checks:

```bash
gh run list --workflow CI --limit 5
gh run list --workflow "XHS Manage" --limit 5
gh run list --workflow "XHS Weekly Report" --limit 5
gh run view <run-id> --log-failed
```

Manual AI-friendly task trigger examples:

```bash
gh workflow run xhs-manage.yml -f task=validate
gh workflow run xhs-manage.yml -f task=answer-validate-strict
gh workflow run xhs-manage.yml -f task=quality-report
gh workflow run xhs-manage.yml -f task=canonical-suggest-hotspot -f limit=50
```

## Verification

Use Node's built-in test runner; no package install is required for tests.

```bash
node --test
node scripts/xhs.js migrate build-questions --check
node scripts/xhs.js validate all
node scripts/xhs.js index build --check
node scripts/xhs.js canonical check
node scripts/xhs.js answer validate
node scripts/xhs.js answer validate --strict
node scripts/xhs.js report quality --noWrite
node scripts/xhs.js issue check
```

With npm:

```bash
npm test
npm run validate
npm run index:check
npm run answer:validate:strict
npm run report:quality
npm run ci:check
```

## Legacy

The legacy collection and one-off query scripts remain for historical comparison and migration support. Do not use them as the primary entrypoint for new workflows.

- `scripts/query_tagged.js`
- `scripts/xhs_pipeline.js`
- `scripts/generate_hashes.js`
- `scripts/validate_tagged.js`
- shell collection scripts such as `fetch.sh`, `fetch_detail.sh`, and `desc_2_questions.sh`

`note_tagged/` remains source history. Migration scripts must not move, delete, or silently rewrite it.
