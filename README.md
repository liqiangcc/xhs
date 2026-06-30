# XHS Knowledge Assets

This repo turns Xiaohongshu interview-note data into a maintainable knowledge asset system:

`Question -> CanonicalQuestion -> Answer -> ReviewProgress`

The supported entrypoint is:

```bash
node scripts/xhs.js <command> [subcommand] [options]
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
node scripts/xhs.js review mark --canonical-id <cq_id> --result good --notes "<text>"
node scripts/xhs.js review weak --limit 20
```

Review data lives in:

- `review/progress.json`
- `review/sessions/{YYYY-MM-DD}.json`
- `review/plans/{target}.md`

## Verification

Use Node's built-in test runner; no package install is required for tests.

```bash
node --test
node scripts/xhs.js migrate build-questions --check
node scripts/xhs.js validate all
node scripts/xhs.js index build --check
node scripts/xhs.js canonical check
node scripts/xhs.js answer validate
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
