#!/usr/bin/env node
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { readJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

function sha256(filePath) {
    return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function paths(root) {
    return {
        audit: path.join(root, 'data', 'manifests', 'quality', 'pilot_answer_audit.json'),
        candidates: path.join(root, 'review', 'candidates', 'answers'),
        output: path.join(root, 'review', 'plans', 'pilot_human_review.md'),
    };
}

function renderPlan(options = {}) {
    const root = options.root || ROOT;
    const values = paths(root);
    const audit = readJson(values.audit);
    const rows = (audit.rows || [])
        .filter((row) => row.promotion_status === 'awaiting_human_review')
        .map((row) => {
            const candidatePath = path.join(values.candidates, `${row.canonical_id}.md`);
            if (!fs.existsSync(candidatePath)) {
                throw new Error(`Missing pilot candidate: ${path.relative(root, candidatePath)}`);
            }
            return { ...row, candidate_sha256: sha256(candidatePath) };
        })
        .sort((a, b) => a.answer_type.localeCompare(b.answer_type) || a.canonical_id.localeCompare(b.canonical_id));

    return [
        '# 首批 60 题试点：待人工签核清单',
        '',
        `当前有 ${rows.length} 题已完成 candidate、evidence、独立审查和候选审计；尚未写入正式答案。根据 \`answer_quality.v1\`，在首批 60 题全部完成人工签核前，不能用自动化或 Agent 代替人工批准。`,
        '',
        '## 人工审查边界',
        '',
        '每题只读取 Canonical/来源问法、候选答案、evidence 和质量合同；确认事实、题型、覆盖、口述质量和边界后，独立作出 `approved` 或 `rejected` 决定。拒绝时不得晋级，保留 `needs_update` 并记录具体缺陷。',
        '',
        '人工签核记录必须包含：',
        '',
        '```json',
        '{',
        '  "canonical_id": "<本表 ID>",',
        '  "candidate_sha256": "<本表 SHA-256>",',
        '  "reviewer_id": "<人工审查者标识>",',
        '  "reviewer_type": "human",',
        '  "reviewed_at": "YYYY-MM-DD",',
        '  "decision": "approved",',
        '  "attestation": "I reviewed the canonical, candidate, evidence, and quality contract.",',
        '  "batch_id": "pilot-quality-v2"',
        '}',
        '```',
        '',
        '保存为 `review/human-review/<canonical_id>.json` 后执行：',
        '',
        '```bash',
        'node scripts/xhs.js answer human-review --canonical-id <canonical_id> --evidence review/evidence/<canonical_id>.json --review review/human-review/<canonical_id>.json',
        'node scripts/xhs.js answer promote --canonical-id <canonical_id> --candidate review/candidates/answers/<canonical_id>.md --evidence review/evidence/<canonical_id>.json',
        '```',
        '',
        `## 待签核（${rows.length}）`,
        '',
        '| Canonical | 当前题型 | Candidate SHA-256 |',
        '|---|---|---|',
        ...rows.map((row) => `| \`${row.canonical_id}\` | ${row.answer_type} | \`${row.candidate_sha256}\` |`),
        '',
        '候选与证据路径均按表中 Canonical ID 代入：`review/candidates/answers/<id>.md`、`review/evidence/<id>.json`。',
        '',
    ].join('\n');
}

function main(argv = process.argv) {
    const rootIndex = argv.indexOf('--root');
    const root = rootIndex >= 0 ? path.resolve(argv[rootIndex + 1]) : ROOT;
    const check = argv.includes('--check');
    const output = paths(root).output;
    const expected = renderPlan({ root });
    const actual = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : '';
    const ok = !check || actual === expected;
    if (!check) fs.writeFileSync(output, expected, 'utf8');
    console.log(JSON.stringify({ schema_version: 'pilot_human_review_plan_report.v1', ok, check, output: path.relative(root, output) }, null, 2));
    return ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();
module.exports = { renderPlan, main };
