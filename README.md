# XHS Knowledge Assets

This repo turns Xiaohongshu interview-note data into a maintainable knowledge asset system:

`Question -> CanonicalQuestion -> Answer -> ReviewProgress`

The supported entrypoint is:

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

## Current Status

As of 2026-06-30, the M1-M8 core loop is implemented and pushed to `origin/master`: migration, validation, indexing, canonical question management, answer metadata validation/sync, and review progress.

Current data snapshot:

- 18 canonical questions
- 83 assigned question rows
- 18 review progress records
- 12 P0 plan items still missing answers in `review/plans/p0.md`

The project is now in the content-building phase. The next useful work is writing answers, validating and syncing them, then widening canonical coverage.

## Next Steps

1. Fill the P0 answers listed in `review/plans/p0.md`.
2. After each answer batch, run `answer validate` and `answer sync`.
3. Continue expanding canonical coverage with `canonical suggest --hotspot --limit 50`; the first target is 200+ assigned question rows.
4. Start the real review loop with `review today` and `review mark`.

```bash
node scripts/xhs.js answer init --canonical-id <cq_id>
node scripts/xhs.js answer validate
node scripts/xhs.js answer sync
node scripts/xhs.js canonical suggest --hotspot --limit 50
node scripts/xhs.js review today
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

## Answers

Answers are Markdown files bound to `canonical_id`.

```bash
node scripts/xhs.js answer init --canonical-id <cq_id>
node scripts/xhs.js answer status --missing
node scripts/xhs.js answer validate
node scripts/xhs.js answer sync
```

Answer files live at `review/answers/{canonical_id}.md`. The first line is required metadata:

```markdown
<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_example","version":1,"status":"draft","updated_at":"2026-06-30"} -->
```

## Review

Review progress is also bound to `canonical_id`.

```bash
node scripts/xhs.js review prepare --target redis --limit 20 --priority P0
node scripts/xhs.js review today --limit 20
node scripts/xhs.js review today --limit 20 --with-issues
node scripts/xhs.js review mark --canonical-id <cq_id> --result good --notes "<text>"
node scripts/xhs.js review weak --limit 20 --with-issues
```

Review data lives in:

- `review/progress.json`
- `review/sessions/{YYYY-MM-DD}.json`
- `review/plans/{target}.md`

## GitHub Issue Cards

GitHub issues are optional mobile-friendly review cards. The source of truth remains local: canonical questions, answer Markdown, and review progress are still keyed by `canonical_id`.

```bash
node scripts/xhs.js issue render --canonical-id <cq_id>
node scripts/xhs.js issue sync --canonical-id <cq_id> --repo liqiangcc/xhs
node scripts/xhs.js issue sync --priority P0 --answer-status ready --repo liqiangcc/xhs --apply
node scripts/xhs.js issue check
```

`issue sync` is a dry run by default. Add `--apply` to create or update GitHub issues through `gh`. Local issue links live in `review/issue_links.json`.

## Verification

Use Node's built-in test runner; no package install is required for tests.

```bash
node --test
node scripts/xhs.js migrate build-questions --check
node scripts/xhs.js validate all
node scripts/xhs.js index build --check
node scripts/xhs.js canonical check
node scripts/xhs.js answer validate
node scripts/xhs.js issue check
```

With npm:

```bash
npm test
npm run validate
npm run index:check
```

## Legacy

The legacy collection and one-off query scripts remain for historical comparison and migration support. Do not use them as the primary entrypoint for new workflows.

- `scripts/query_tagged.js`
- `scripts/xhs_pipeline.js`
- `scripts/generate_hashes.js`
- `scripts/validate_tagged.js`
- shell collection scripts such as `fetch.sh`, `fetch_detail.sh`, and `desc_2_questions.sh`

`note_tagged/` remains source history. Migration scripts must not move, delete, or silently rewrite it.
