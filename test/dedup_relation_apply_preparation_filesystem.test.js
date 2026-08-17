'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { createApplication } = require('../src/bootstrap/create-application');
const { createDedupFsPaths } = require('../src/infrastructure/filesystem/dedup-paths');

function question(overrides = {}) {
    return {
        question_id: 'q_default',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2026',
        date: '未知',
        domain: { l1: '缓存', l2: 'Redis' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: ['Redis'],
        business_context: [],
        is_valid_for_library: true,
        canonical_id: null,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
        ...overrides,
    };
}

function makeRoot(prefix) {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeFixture(root) {
    const q1 = question({
        question_id: 'q_redis_a',
        source_note_id: 'note-a',
        original_question: 'Redis 为什么快？',
    });
    const q2 = question({
        question_id: 'q_redis_b',
        source_note_id: 'note-b',
        company: '字节',
        original_question: 'Redis 为什么这么快？',
    });
    const paths = createDedupFsPaths(root);
    writeJsonl(paths.questions, [q1, q2]);
    writeIndexes(buildIndexes([q1, q2], { canonicalQuestions: [] }), path.dirname(paths.entityIndex));
    return { paths, q1, q2 };
}

async function seedDecision(app) {
    const suggestions = await app.dedup.suggest({ mode: 'entity', seed: 'redis', limit: 10 });
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    await app.dedup.recordDecision({
        relation_candidate_key: relationCandidateKey,
        relation: 'same',
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: 'same Redis performance concept',
        decided_at: '2026-08-13T13:30:00+08:00',
    });
    return relationCandidateKey;
}

test('production composition root reloads the persisted Decision and prepares a side-effect-free ready intent', async () => {
    const root = makeRoot('xhs-dedup-prepare-fs-');
    try {
        const { paths } = writeFixture(root);
        const app = createApplication({ root });
        const relationCandidateKey = await seedDecision(app);
        const result = await app.dedup.prepareApply({
            relation_candidate_key: relationCandidateKey,
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        });

        assert.equal(result.ok, true);
        assert.equal(result.relation, 'same');
        assert.equal(result.intent.intent_state, 'ready');
        assert.equal(result.intent.intent_kind, 'canonicalize_question_group');
        assert.equal(result.decision_snapshot.resource, `dedup-relation-decision:${relationCandidateKey}`);
        assert.match(result.decision_snapshot.revision, /^[0-9a-f]{64}$/);
        assert.equal(Object.hasOwn(result, 'plan'), false);
        assert.equal(Object.hasOwn(result, 'commit'), false);
        assert.equal(Object.hasOwn(result.intent, 'operation'), false);

        const canonicalCandidateManifest = path.join(
            root,
            'data',
            'manifests',
            'canonical',
            'canonical_candidates.json',
        );
        assert.equal(fs.existsSync(canonicalCandidateManifest), false);
        assert.equal(fs.existsSync(paths.relationDecisions), true);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('production prepare ignores unrelated Question changes but rejects relevant source drift', async () => {
    const root = makeRoot('xhs-dedup-prepare-stale-fs-');
    try {
        const { paths, q1, q2 } = writeFixture(root);
        const app = createApplication({ root });
        const relationCandidateKey = await seedDecision(app);

        const unrelated = question({
            question_id: 'q_mysql',
            source_note_id: 'note-c',
            original_question: 'MySQL MVCC 是什么？',
            domain: { l1: '数据库', l2: 'MySQL' },
            tech_entities: ['MySQL'],
        });
        writeJsonl(paths.questions, [q1, q2, unrelated]);
        const stillFresh = await app.dedup.prepareApply({
            relation_candidate_key: relationCandidateKey,
        });
        assert.equal(stillFresh.intent.intent_state, 'requires_input');

        writeJsonl(paths.questions, [
            q1,
            { ...q2, original_question: 'Redis 为什么会这么快？' },
            unrelated,
        ]);
        await assert.rejects(
            app.dedup.prepareApply({
                relation_candidate_key: relationCandidateKey,
                canonical_id: 'cq_redis_performance',
                canonical_title: 'Redis 为什么快？',
            }),
            /Stale relation candidate source dedup-questions-by-refs:/,
        );
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
