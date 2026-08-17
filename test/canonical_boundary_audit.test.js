'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJson, writeJsonl } = require('../scripts/lib/io');
const { buildCandidates } = require('../scripts/content/audit_canonical_boundaries');

function withRoot(canonicals, fn) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-boundary-'));
    try {
        writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), canonicals);
        return fn(root);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
}

test('boundary audit proposes deterministic exact-title and related-topic review pairs', () => {
    withRoot([
        { canonical_id: 'cq_a', canonical_title: 'Redis AOF 重写过程', aliases: [], primary_entities: ['redis', 'aof'], primary_domain: { l1: '缓存', l2: 'Redis' } },
        { canonical_id: 'cq_b', canonical_title: 'Redis AOF 重写过程？', aliases: [], primary_entities: ['redis', 'aof'], primary_domain: { l1: '缓存', l2: 'Redis' } },
        { canonical_id: 'cq_c', canonical_title: 'Redis RDB 快照', aliases: [], primary_entities: ['redis', 'rdb'], primary_domain: { l1: '缓存', l2: 'Redis' } },
    ], (root) => {
        const rows = buildCandidates({ root });
        assert.equal(rows[0].canonical_ids.join(','), 'cq_a,cq_b');
        assert.equal(rows[0].proposed_action, 'merge_review');
        assert.equal(rows[0].reviewer_decision, 'pending');
        writeJson(path.join(root, 'data', 'manifests', 'canonical', 'boundary_review_decisions.json'), {
            schema_version: 'canonical_boundary_review_decisions.v1',
            items: [{ candidate_id: rows[0].candidate_id, decision: 'keep_separate', note: 'different coding invariant' }],
        });
        const reviewed = buildCandidates({ root });
        assert.equal(reviewed[0].reviewer_decision, 'keep_separate');
        assert.equal(reviewed[0].reviewer_note, 'different coding invariant');
    });
});

test('boundary audit recalls same-domain richer variants through strong entity containment', () => {
    withRoot([
        {
            canonical_id: 'cq_tcp_rich',
            canonical_title: 'TCP 三次握手和四次挥手的过程与原因',
            aliases: [],
            primary_entities: ['tcp', '三次握手', '四次挥手', 'syn', 'ack'],
            primary_domain: { l1: '网络', l2: 'TCP' },
        },
        {
            canonical_id: 'cq_tcp_process',
            canonical_title: '讲讲TCP协议的三次握手和四次挥手过程?',
            aliases: [],
            primary_entities: ['三次握手', '四次挥手'],
            primary_domain: { l1: '网络', l2: 'TCP' },
        },
    ], (root) => {
        const rows = buildCandidates({ root });
        assert.equal(rows.length, 1);
        assert.deepEqual(rows[0].canonical_ids, ['cq_tcp_process', 'cq_tcp_rich']);
        assert.equal(rows[0].evidence.contained_variant_signal, true);
        assert.equal(rows[0].evidence.shared_entity_count, 2);
        assert.equal(rows[0].evidence.entity_containment, 1);
        assert.ok(rows[0].evidence.title_token_jaccard >= 0.35);
        assert.ok(rows[0].evidence.title_token_jaccard < 0.55);
    });
});

test('entity containment does not recall low-title-similarity same-domain topics', () => {
    withRoot([
        {
            canonical_id: 'cq_tcp_packet',
            canonical_title: 'TCP 粘包和拆包怎么处理',
            aliases: [],
            primary_entities: ['tcp', '网络协议'],
            primary_domain: { l1: '网络', l2: 'TCP' },
        },
        {
            canonical_id: 'cq_tcp_handshake',
            canonical_title: 'TCP 三次握手流程',
            aliases: [],
            primary_entities: ['tcp', '网络协议'],
            primary_domain: { l1: '网络', l2: 'TCP' },
        },
    ], (root) => {
        const rows = buildCandidates({ root });
        assert.deepEqual(rows, []);
    });
});
