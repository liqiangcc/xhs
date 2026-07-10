'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJsonl } = require('../scripts/lib/io');
const { buildCandidates } = require('../scripts/content/audit_canonical_boundaries');

test('boundary audit proposes deterministic exact-title and related-topic review pairs', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-boundary-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [
        { canonical_id: 'cq_a', canonical_title: 'Redis AOF 重写过程', aliases: [], primary_entities: ['redis', 'aof'], primary_domain: { l1: '缓存', l2: 'Redis' } },
        { canonical_id: 'cq_b', canonical_title: 'Redis AOF 重写过程？', aliases: [], primary_entities: ['redis', 'aof'], primary_domain: { l1: '缓存', l2: 'Redis' } },
        { canonical_id: 'cq_c', canonical_title: 'Redis RDB 快照', aliases: [], primary_entities: ['redis', 'rdb'], primary_domain: { l1: '缓存', l2: 'Redis' } },
    ]);
    const rows = buildCandidates({ root });
    assert.equal(rows[0].canonical_ids.join(','), 'cq_a,cq_b');
    assert.equal(rows[0].proposed_action, 'merge_review');
    assert.equal(rows[0].reviewer_decision, 'pending');
    fs.rmSync(root, { recursive: true, force: true });
});
