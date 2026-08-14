'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { readJson, readJsonl, writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, getIndexPaths, writeIndexes } = require('../scripts/lib/index_store');
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
        aliases: ['Redis 性能为什么高？'],
        question_ids: ['q_existing'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['阿里'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: 'curated',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function makeRoot(prefix) {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeFixture(root, { withExistingCanonical = false } = {}) {
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
    const existingQuestion = question({
        question_id: 'q_existing',
        source_note_id: 'note-existing',
        company: '阿里',
        original_question: 'Redis 底层性能原理是什么？',
        canonical_id: 'cq_redis_performance',
    });
    const questions = withExistingCanonical ? [existingQuestion, q1, q2] : [q1, q2];
    const paths = createCanonicalFsPaths(root);
    writeJsonl(paths.questions, questions);
    const canonicalQuestions = withExistingCanonical ? [existingCanonical()] : [];
    if (withExistingCanonical) writeJsonl(paths.canonicalQuestions, canonicalQuestions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions }), paths.indexDir);
    return { paths, questions, canonicalQuestions };
}

async function resolveCanonicalizationPlan(app) {
    const suggestions = await app.dedup.suggest({ mode: 'entity', seed: 'redis', limit: 10 });
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    await app.dedup.recordDecision({
        relation_candidate_key: relationCandidateKey,
        relation: 'same',
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: 'same Redis performance concept',
        decided_at: '2026-08-13T17:35:00+08:00',
    });
    const prepared = await app.dedup.prepareApply({
        relation_candidate_key: relationCandidateKey,
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 为什么快？',
    });
    return app.canonical.resolveQuestionGroupCanonicalization({ intent: prepared.intent });
}

function assertTransactionClean(paths) {
    assert.equal(fs.existsSync(paths.lock), false);
    assert.equal(fs.existsSync(paths.journal), false);
}

test('production root executes absent-target canonicalization atomically through filesystem MutationGateway', async () => {
    const root = makeRoot('xhs-canonicalize-execute-absent-fs-');
    try {
        const { paths } = writeFixture(root);
        const app = createApplication({ root });
        const canonicalization = await resolveCanonicalizationPlan(app);
        const indexPaths = getIndexPaths(paths.indexDir);
        fs.writeFileSync(indexPaths.company, JSON.stringify({ stale_sentinel: true }), 'utf8');

        const result = await app.canonical.executeQuestionGroupCanonicalization({
            plan: canonicalization.plan,
        });
        const canonicals = readJsonl(paths.canonicalQuestions, []);
        const questions = readJsonl(paths.questions, []);
        const companyIndex = readJson(indexPaths.company, {});

        assert.equal(result.ok, true);
        assert.equal(result.mutation_plan.operation, 'canonicalize');
        assert.equal(result.commit.committed, true);
        assert.equal(result.commit.operation, 'canonicalize');
        assert.equal(canonicals.length, 1);
        assert.equal(canonicals[0].canonical_id, 'cq_redis_performance');
        assert.deepEqual(canonicals[0].question_ids, ['q_redis_a', 'q_redis_b']);
        assert.ok(questions.every((row) => row.canonical_id === 'cq_redis_performance'));
        assert.equal(result.updated_question_rows, 2);
        assert.equal(Object.hasOwn(companyIndex, 'stale_sentinel'), false);
        assert.equal(fs.existsSync(paths.candidateManifest), false);
        assertTransactionClean(paths);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('production root executes existing-target canonicalization and preserves authoritative Canonical fields', async () => {
    const root = makeRoot('xhs-canonicalize-execute-existing-fs-');
    try {
        const { paths } = writeFixture(root, { withExistingCanonical: true });
        const app = createApplication({ root });
        const canonicalization = await resolveCanonicalizationPlan(app);

        const result = await app.canonical.executeQuestionGroupCanonicalization({
            plan: canonicalization.plan,
        });
        const canonicals = readJsonl(paths.canonicalQuestions, []);
        const questions = readJsonl(paths.questions, []);
        const target = canonicals.find((item) => item.canonical_id === 'cq_redis_performance');

        assert.equal(canonicalization.plan.plan_kind, 'extend_existing_canonical');
        assert.equal(result.commit.question_rebinding_count, 2);
        assert.equal(target.canonical_title, 'Redis 性能原理');
        assert.equal(target.answer_status, 'curated');
        assert.equal(target.review_priority, 'P0');
        assert.deepEqual(target.question_ids, ['q_existing', 'q_redis_a', 'q_redis_b'].sort());
        assert.ok(questions.every((row) => row.canonical_id === 'cq_redis_performance'));
        assert.equal(result.updated_question_rows, 3);
        assert.equal(fs.existsSync(paths.candidateManifest), false);
        assertTransactionClean(paths);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('production execution rejects caller-controlled MutationPlan evidence', async () => {
    const root = makeRoot('xhs-canonicalize-execute-forged-fs-');
    try {
        const { paths } = writeFixture(root);
        const app = createApplication({ root });
        const canonicalization = await resolveCanonicalizationPlan(app);

        await assert.rejects(
            app.canonical.executeQuestionGroupCanonicalization({
                plan: canonicalization.plan,
                mutation_plan: {
                    schema_version: 'canonical_mutation_plan.v1',
                    operation: 'canonicalize',
                },
            }),
            /Canonical execution state is controlled by Application/,
        );
        assert.equal(fs.existsSync(paths.canonicalQuestions), false);
        assertTransactionClean(paths);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
