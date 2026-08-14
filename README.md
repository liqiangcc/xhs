# XHS Knowledge Assets

This repo turns Xiaohongshu interview-note data into a maintainable knowledge asset system:

`Question -> CanonicalQuestion -> Answer -> ReviewProgress`

The supported entrypoint is:

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

For current Canonical/Dedup commands and boundaries, use `docs/refactor/10_current_dedup_canonical_operations.md` as the operational SSOT. `docs/refactor/08_content_building_goals.md` defines content goals and completion criteria rather than command semantics.

## Current Status

As of 2026-07-01, the M1-M8 core loop is implemented and the repository is in the content-coverage and real-review phase: migration, validation, indexing, canonical question management, answer metadata validation/sync, review progress, issue-card rendering, and quality reporting are all available.

Current data snapshot:

- 9,620 question rows, 9,362 valid rows
- 34 canonical questions
- 134 assigned question rows
- 34 review progress records
- 34 ready answers; missing answers is now 0
- P0 count: 12; P1 count: 22
- 0 GitHub issue links synced so far

The current high-value batch is answer-complete. The active roadmap is content-first: calibrate the existing assets, widen canonical coverage, upgrade answers for experienced-hire oral delivery and follow-ups, then use real review results to drive the next batch. The intermediate milestones lead to full reviewability: every genuine interview question—including recoverable rows currently marked invalid—must bind to one CanonicalQuestion, have a ready answer and ReviewProgress, and be reachable from a query or review entrypoint. See `docs/refactor/08_content_building_goals.md`.

## Next Steps

1. Follow the C0-C10 goals in `docs/refactor/08_content_building_goals.md`.
2. Calibrate the existing 34 canonical assets and attach synonymous questions before creating new records.
3. Expand in closed batches of at most 10 assets; the first target is 60 canonical questions and 200+ assigned rows.
4. Keep every new P0/P1 answer strict-valid and optimize it for experienced-hire oral delivery plus answered follow-ups.
5. Before scaling to 100 canonical questions, complete a pilot covering at least 5 canonical questions and 10 real review marks.
6. Continue through the long tail until every genuine interview question is assigned, answer-ready, and reachable from review; 60/200 and 100/300 are milestones, not the final scope.

```bash
# Detect pending relation candidates
node scripts/xhs.js canonical suggest --hotspot --limit 50
node scripts/xhs.js canonical suggest --entity Redis --limit 50

# Explicitly review one candidate
node scripts/xhs.js dedup decide \
  --relation-candidate-key '<key>' \
  --relation same \
  --actor-type human \
  --actor-id '<reviewer-id>'

# Apply a reviewed same/alias relation
node scripts/xhs.js dedup apply \
  --relation-candidate-key '<key>' \
  --canonical-id <cq_id> \
  --canonical-title '<title>'

node scripts/xhs.js answer missing --priority P1
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

New relation discovery always goes through Detect -> explicit Decision -> Apply:

```bash
# Detect pending review candidates
node scripts/xhs.js canonical suggest --hotspot --limit 25
node scripts/xhs.js canonical suggest --entity Redis --limit 50

# Review one RelationCandidate
node scripts/xhs.js dedup decide \
  --relation-candidate-key '<key>' \
  --relation <same|alias|parent_child|followup|related|unrelated> \
  --actor-type human \
  --actor-id '<reviewer-id>' \
  --rationale '<reason>'

# Apply same/alias after explicit review
node scripts/xhs.js dedup apply \
  --relation-candidate-key '<key>' \
  --canonical-id <cq_id> \
  --canonical-title '<title>'

# Maintain already-existing Canonical records
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
- `data/manifests/dedup/relation_candidate_queues.json`
- `data/manifests/dedup/relation_decisions.jsonl`

`canonical suggest` writes pending review state to `data/manifests/dedup/relation_candidate_queues.json`. A RelationCandidate is not mutation authorization: it must be followed by an explicit `dedup decide`, and only then can `dedup apply` revalidate freshness and mutate Canonical state.

The `canonical accept` CLI and its executable runtime/mutation contract have been retired. Historical `canonical_candidates.v1` now remains only as staged cleanup residue (test-support/path names plus an empty snapshot); new Suggest flows, GitHub Actions, Agents, and normal manual work must use Suggest -> Decide -> Apply. See `docs/refactor/09_legacy_canonical_accept_boundary.md`.

`--noManifest` suppresses `data/manifests/runs/latest_*.json`; it does not suppress the Dedup relation review queue generated by Suggest.

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
<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_example","version":1,"status":"draft","updated_at":"2026-07-01"} -->
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

`canonical-suggest-hotspot` and `canonical-suggest-entity` publish `data/manifests/dedup/relation_candidate_queues.json` as the `dedup-relation-candidates` artifact. With `create_pr=true`, the PR contains that review queue; it does not create or update `canonical_candidates.json`. An explicit `dedup decide` is still required before any Apply.

See `docs/refactor/10_current_dedup_canonical_operations.md` for the current operational flow. `docs/refactor/06_github_actions_ai_management.md` is an Actions evolution record and may contain historical terminology in older sections.

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

The `canonical accept` CLI, runtime path, and MutationPlan operation are retired. Only non-executable test/path/data cleanup residue remains. See `docs/refactor/09_legacy_canonical_accept_boundary.md`.

`note_tagged/` remains source history. Migration scripts must not move, delete, or silently rewrite it.
