'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const { createAcceptCanonicalUseCase } = require('../src/application/canonical/accept-canonical');
const { createInMemoryCanonicalAdapters } = require('../src/infrastructure/in-memory/canonical-adapters');

function candidate(overrides = {}) {
    return {
        candidate_id: 'cand_accept',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？', 'Redis 单线程为什么快？'],
        question_ids: ['q1', 'q2'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团', '字节'],
        frequency: 2,
        review_priority: 'P2',
        ...overrides,
    };
}

function canonical(canonicalId, questionIds, overrides = {}) {
    return {
        canonical_id: canonicalId,
        canonical_title: '已有 Redis Canonical',
        aliases: ['已有 Redis Canonical'],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: questionIds.length,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(questionId, index, canonicalId = null, company = '美团', originalQuestion = null) {
    return {
        question_id: questionId,
        original_question: originalQuestion || `question ${questionId}`,
        source_note_id: `note_${index}`,
        source_question_index: index,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

function useCase(adapters, mutationStore = adapters.mutationStore) {
    return createAcceptCanonicalUseCase({
        candidateRepository: adapters.canonicalCandidateRepository,
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
        canonicalQuestionOwnershipRepository: adapters.canonicalQuestionOwnershipRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        mutationStore,
        taxonomy,
    });
}

test('accept creates a canonical and assigns every unbound candidate question row atomically', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        candidates: [candidate()],
        bindings: [
            question('q1', 1, null, '美团', 'Redis 为什么快？'),
            question('q2', 2, null, '字节', 'Redis 单线程为什么快？'),
            question('q2', 3, null, '阿里', 'Redis 单线程为何高效？'),
        ],
    });

    const result = await useCase(adapters)({
        candidate_id: 'cand_accept',
        canonical_id: 'cq_redis_fast',
    });

    assert.equal(result.ok, true);
    assert.equal(result.canonical_id, 'cq_redis_fast');
    assert.equal(result.accepted_candidate_id, 'cand_accept');
    assert.deepEqual(result.question_ids, ['q1', 'q2']);
    assert.equal(result.updated_question_rows, 3);
    assert.equal(result.canonical_count, 1);
    assert.equal(result.plan.operation, 'accept');
    assert.deepEqual(
        result.plan.expected_revisions.map((item) => item.resource),
        [
            'canonical-candidate:cand_accept',
            'canonical:cq_redis_fast',
            'question-bindings-by-question:q1',
            'question-bindings-by-question:q2',
            'canonical-ownership-by-question:q1',
            'canonical-ownership-by-question:q2',
        ],
    );
    assert.deepEqual(result.plan.changes.question_rebindings, [
        { question_id: 'q1', from_canonical_id: null, to_canonical_id: 'cq_redis_fast' },
        { question_id: 'q2', from_canonical_id: null, to_canonical_id: 'cq_redis_fast' },
    ]);

    const state = adapters.snapshot();
    const record = state.canonicals.find((item) => item.canonical_id === 'cq_redis_fast');
    assert.ok(record);
    assert.deepEqual(record.question_ids, ['q1', 'q2']);
    assert.equal(record.frequency, 3);
    assert.deepEqual(
        record.companies,
        ['美团', '字节', '阿里'].sort((a, b) => a.localeCompare(b, 'zh')),
    );
    assert.deepEqual(record.primary_domain, { l1: '缓存', l2: 'Redis' });
    assert.deepEqual(record.primary_entities, ['Redis']);
    assert.equal(state.bindings.every((binding) => binding.canonical_id === 'cq_redis_fast'), true);
    assert.equal(state.effects.index_rebuild_count, 1);
});

test('accept extends an existing canonical while preserving its identity fields and assigning only unbound rows', async () => {
    const target = canonical('cq_target', ['q1'], {
        canonical_title: '编辑后的 Redis 标题',
        primary_domain_override: { l1: '缓存', l2: 'Redis' },
        answer_status: 'ready',
    });
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [target],
        candidates: [candidate({ question_ids: ['q2'], frequency: 1 })],
        bindings: [
            question('q1', 1, 'cq_target', '美团'),
            question('q2', 2, null, '字节'),
        ],
    });

    const result = await useCase(adapters)({
        candidate_id: 'cand_accept',
        canonical_id: 'cq_target',
        title: '候选覆盖标题',
    });

    assert.equal(result.updated_question_rows, 1);
    assert.deepEqual(result.plan.changes.question_rebindings, [
        { question_id: 'q2', from_canonical_id: null, to_canonical_id: 'cq_target' },
    ]);
    const record = adapters.snapshot().canonicals.find((item) => item.canonical_id === 'cq_target');
    assert.equal(record.canonical_title, '编辑后的 Redis 标题');
    assert.equal(record.answer_status, 'ready');
    assert.deepEqual(record.question_ids, ['q1', 'q2']);
    assert.equal(record.frequency, 2);
    assert.deepEqual(record.primary_domain, target.primary_domain_override);
});

test('accept remains idempotent when candidate questions already belong to the target canonical', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [canonical('cq_target', ['q1'])],
        candidates: [candidate({ question_ids: ['q1'], frequency: 1 })],
        bindings: [question('q1', 1, 'cq_target')],
    });

    const result = await useCase(adapters)({
        candidate_id: 'cand_accept',
        canonical_id: 'cq_target',
    });

    assert.deepEqual(result.plan.changes.question_rebindings, []);
    assert.equal(result.updated_question_rows, 1);
    assert.equal(result.canonical_count, 1);
    assert.equal(adapters.snapshot().bindings[0].canonical_id, 'cq_target');
});

test('accept rejects a conflicting Question binding before mutation preflight', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        candidates: [candidate({ question_ids: ['q1'] })],
        bindings: [question('q1', 1, 'cq_other')],
    });
    let preflightCalled = false;
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            preflightCalled = true;
            return adapters.mutationStore.preflight(plan);
        },
    };

    await assert.rejects(
        useCase(adapters, mutationStore)({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_target',
        }),
        /Question q1 already belongs to cq_other/,
    );
    assert.equal(preflightCalled, false);
    assert.equal(adapters.snapshot().canonicals.length, 0);
});

test('accept rejects a conflicting Canonical record declaration even when the Question row is unbound', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [canonical('cq_other', ['q1'])],
        candidates: [candidate({ question_ids: ['q1'] })],
        bindings: [question('q1', 1, null)],
    });
    let preflightCalled = false;
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            preflightCalled = true;
            return adapters.mutationStore.preflight(plan);
        },
    };

    await assert.rejects(
        useCase(adapters, mutationStore)({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_target',
        }),
        /Question q1 already belongs to cq_other/,
    );
    assert.equal(preflightCalled, false);
    assert.equal(adapters.snapshot().bindings[0].canonical_id, null);
});

test('accept rejects a candidate that changes after planning', async () => {
    const originalCandidate = candidate({ question_ids: ['q1'] });
    const adapters = createInMemoryCanonicalAdapters({
        candidates: [originalCandidate],
        bindings: [question('q1', 1, null)],
    });
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            adapters.testSupport.upsertCandidate({
                ...originalCandidate,
                aliases: ['concurrent candidate edit'],
            });
            return adapters.mutationStore.preflight(plan);
        },
    };

    await assert.rejects(
        useCase(adapters, mutationStore)({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_target',
        }),
        /Revision mismatch for canonical-candidate:cand_accept/,
    );
    const state = adapters.snapshot();
    assert.equal(state.canonicals.length, 0);
    assert.equal(state.bindings[0].canonical_id, null);
    assert.deepEqual(state.candidates[0].aliases, ['concurrent candidate edit']);
});

test('accept rejects a concurrent create of its target canonical id', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        candidates: [candidate({ question_ids: ['q1'] })],
        bindings: [question('q1', 1, null)],
    });
    const concurrent = canonical('cq_target', ['q9'], { canonical_title: 'concurrent create' });
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            adapters.testSupport.upsertCanonical(concurrent);
            return adapters.mutationStore.preflight(plan);
        },
    };

    await assert.rejects(
        useCase(adapters, mutationStore)({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_target',
        }),
        /Revision mismatch for canonical:cq_target/,
    );
    const state = adapters.snapshot();
    assert.equal(state.canonicals.length, 1);
    assert.deepEqual(state.canonicals[0].question_ids, ['q9']);
    assert.equal(state.bindings[0].canonical_id, null);
});

test('accept rejects a concurrent Canonical ownership claim for a candidate question', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        candidates: [candidate({ question_ids: ['q1'] })],
        bindings: [question('q1', 1, null)],
    });
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            adapters.testSupport.upsertCanonical(canonical('cq_other', ['q1']));
            return adapters.mutationStore.preflight(plan);
        },
    };

    await assert.rejects(
        useCase(adapters, mutationStore)({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_target',
        }),
        /Revision mismatch for canonical-ownership-by-question:q1/,
    );
    const state = adapters.snapshot();
    assert.equal(state.canonicals[0].canonical_id, 'cq_other');
    assert.equal(state.bindings[0].canonical_id, null);
});

test('accept commit failure leaves canonical and Question state unchanged', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        candidates: [candidate({ question_ids: ['q1'] })],
        bindings: [question('q1', 1, null)],
    });
    const before = adapters.snapshot();
    adapters.mutationStore.failNextCommit(new Error('injected accept commit failure'));

    await assert.rejects(
        useCase(adapters)({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_target',
        }),
        /injected accept commit failure/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});
