'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJson, writeJsonl } = require('../scripts/lib/io');
const { buildQueue } = require('../scripts/content/build_curated_audit_queue');

test('curated audit queue deterministically groups no more than ten rows per batch', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-curated-queue-'));
    const rows = Array.from({ length: 11 }, (_, index) => ({ canonical_id: `cq_${String(index).padStart(2, '0')}`, answer_status: 'ready', quality_tier: 'curated', audit_ok: false, hard_failures: ['missing_evidence'], evidence_path: null, review_decision: null }));
    writeJson(path.join(root, 'data', 'manifests', 'quality', 'curated_answer_audit.json'), { curated_population_count: 11, rows });
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), rows.map((row) => ({ canonical_id: row.canonical_id, canonical_title: row.canonical_id, question_ids: [], primary_domain: {} })));
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), []);
    const result = buildQueue({ root });
    assert.equal(result.report.queued_count, 11);
    assert.equal(result.report.batch_count, 2);
    assert.equal(result.rows.filter((row) => row.batch === 'curated-audit-001').length, 10);
    assert.equal(result.rows.filter((row) => row.batch === 'curated-audit-002').length, 1);
    fs.rmSync(root, { recursive: true, force: true });
});
