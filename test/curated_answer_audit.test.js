'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJson, writeJsonl } = require('../scripts/lib/io');
const { buildReport } = require('../scripts/content/audit_curated_answers');

test('curated audit report includes curated and previously demoted curated assets', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-curated-audit-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), require('../config/answer_quality.json'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{ canonical_id: 'cq_one', canonical_title: 'Redis AOF', question_ids: [], primary_domain: { l1: '缓存', l2: 'Redis' } }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), []);
    const answers = path.join(root, 'review', 'answers');
    ensureDir(answers);
    fs.writeFileSync(path.join(answers, 'cq_one.md'), '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_one","version":2,"status":"needs_update","quality_tier":"curated_audit_failed","updated_at":"2026-07-11"} -->\n# Redis AOF\n', 'utf8');
    const report = buildReport({ root });
    assert.equal(report.curated_population_count, 1);
    assert.equal(report.rows[0].quality_tier, 'curated_audit_failed');
    assert.equal(report.passing_count, 0);
    fs.rmSync(root, { recursive: true, force: true });
});
