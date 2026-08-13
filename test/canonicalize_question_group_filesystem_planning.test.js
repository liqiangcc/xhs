'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { readJsonl, writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { createApplication } = require('../src/bootstrap/create-application');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');

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

function existingCanonical(overrides = {}) {
    return {
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 性能原理',
        aliases: ['Redis 为什么快？'],
        question_ids: ['q_existing'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: 1,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function makeRoot(prefix) {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeQuestionFixture(root) {
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
    const questions = [q1, q2];
    const paths = createCanonicalFsPaths(root);
    writeJsonl(paths.questions, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), paths.indexDir);
    return { paths, questions };
}

async function prepareReadyIntent(app) {
    const suggestions = await app.dedup.suggest({ mode: 'entity', seed: 'redis', limit: 10 });
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    await app.dedup.recordDecision({
        relation_candidate_key: relationCandidateKey,
        relation: 'same',
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: 'same Redis performance concept',
        decided_at: '2026-08-13T14:40:00+08:00',
    });
    return app.dedup.prepareApply({
        relation_candidate_key: relationCandidateKey,
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 为什么快？',
    });
}

test('production root resolves an absent Canonical target to create without mutation', async () => {
    const root = makeRoot('xhs-canonicalize-plan-absent-fs-');
    try {
        const { paths } = writeQuestionFixture(root);
        const app = createApplication({ root });
        const prepared = await prepareReadyIntent(app);
        const result = await app.canonical.planQuestionGroup({ intent: prepared.intent });

        assert.equal(result.ok, true);
        assert.equal(result.resolution, 'absent');
        assert.equal(result.canonical_id, 'cq_redis_performance');
        assert.equal(result.plan.plan_kind, 'create_canonical');
        assert.equal(result.plan.canonical_target.title_resolution, 'use_requested');
        assert.equal(result.plan.canonical_target.effective_title, 'Redis 为什么快？');
        assert.equal(result.plan.target_identity.resource, 'canonical:cq_redis_performance');
        assert.match(result.plan.target_identity.revision, /^[0-9a-f]{64}$/);
        assert.equal(result.plan.mutation_authorized, false);
        assert.equal(Object.hasOwn(result.plan, 'operation'), false);
        assert.equal(Object.hasOwn(result.plan, 'changes'), false);
        assert.equal(Object.hasOwn(result, 'commit'), false);
        assert.equal(fs.existsSync(paths.canonicalQuestions), false);
        assert.equal(fs.existsSync(paths.candidateManifest), false);
        assert.equal(fs.existsSync(paths.lock), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('production root resolves an existing Canonical target to extend and preserves authoritative state', async () => {
    const root = makeRoot('xhs-canonicalize-plan-existing-fs-');
    try {
        const { paths } = writeQuestionFixture(root);
        const existing = existingCanonical();
        writeJsonl(paths.canonicalQuestions, [existing]);
        const app = createApplication({ root });
        const prepared = await prepareReadyIntent(app);
        const before = readJsonl(paths.canonicalQuestions, []);
        const result = await app.canonical.planQuestionGroup({ intent: prepared.intent });
        const after = readJsonl(paths.canonicalQuestions, []);

        assert.equal(result.ok, true);
        assert.equal(result.resolution, 'existing');
        assert.equal(result.plan.plan_kind, 'extend_existing_canonical');
        assert.equal(result.plan.canonical_target.requested_title, 'Redis 为什么快？');
        assert.equal(result.plan.canonical_target.effective_title, 'Redis 性能原理');
        assert.equal(result.plan.canonical_target.title_resolution, 'preserve_existing');
        assert.equal(result.plan.mutation_authorized, false);
        assert.deepEqual(before, [existing]);
        assert.deepEqual(after, before);
        assert.equal(Object.hasOwn(result.plan, 'mutation_plan'), false);
        assert.equal(Object.hasOwn(result.plan, 'commit'), false);
        assert.equal(fs.existsSync(paths.candidateManifest), false);
        assert.equal(fs.existsSync(paths.lock), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
