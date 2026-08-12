'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const { createSplitCanonicalUseCase } = require('../src/application/canonical/split-canonical');
const { createInMemoryCanonicalAdapters } = require('../src/infrastructure/in-memory/canonical-adapters');

function canonical(id, questionIds, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['旧公司'],
        frequency: questionIds.length,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function binding(questionId, canonicalId, index, company, originalQuestion = `question ${questionId}`) {
    return {
        question_id: questionId,
        canonical_id: canonicalId,
        source_note_id: `note_${index}`,
        source_question_index: index,
        original_question: originalQuestion,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
    };
}

function passingIntegrityReport(overrides = {}) {
    return {
        schema_version: 'canonical_quality_report.v1',
        ok: true,
        record_count: 2,
        assigned_question_rows: 4,
        duplicate_question_id_count: 0,
        missing_question_id_count: 0,
        binding_mismatch_count: 0,
        orphan_binding_count: 0,
        unlisted_binding_count: 0,
        suspected_duplicate_count: 0,
        duplicate_question_ids: [],
        missing_question_ids: [],
        binding_mismatches: [],
        orphan_bindings: [],
        unlisted_bindings: [],
        suspected_duplicates: [],
        ...overrides,
    };
}

function createUseCase(adapters, overrides = {}) {
    return createSplitCanonicalUseCase({
        canonicalRepository: adapters.canonicalRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        mutationStore: adapters.mutationStore,
        integrityChecker: {
            async check() {
                return passingIntegrityReport();
            },
        },
        taxonomy,
        ...overrides,
    });
}

function createSeed() {
    return {
        canonicals: [
            canonical('cq_source', ['q1', 'q2'], {
                canonical_title: 'Redis 综合问题',
                aliases: ['Redis 综合问题'],
                frequency: 4,
                review_priority: 'P1',
            }),
        ],
        bindings: [
            binding('q1', 'cq_source', 1, '美团', 'Redis 过期策略有哪些？'),
            binding('q2', 'cq_source', 2, '字节', 'Redis 为什么快？'),
            binding('q2', 'cq_source', 3, '阿里', 'Redis 单线程为什么快？'),
            binding('q2', 'cq_source', 4, '字节', 'Redis 性能为什么高？'),
        ],
    };
}

test('plans and commits a split while refreshing both resulting canonicals', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const split = createUseCase(adapters);

    const result = await split({
        source: 'cq_source',
        question_id: 'q2',
        new_canonical_id: 'cq_redis_fast',
        title: 'Redis 为什么快？',
    });

    assert.equal(result.ok, true);
    assert.equal(result.canonical_count, 2);
    assert.equal(result.plan.operation, 'split');
    assert.equal(Object.isFrozen(result.plan), true);
    assert.deepEqual(
        result.plan.expected_revisions.map((item) => item.resource),
        [
            'canonical:cq_source',
            'question-bindings-by-question:q1',
            'question-bindings-by-question:q2',
        ],
    );
    assert.deepEqual(result.plan.changes.canonical_removals, []);
    assert.equal(result.plan.changes.canonical_upserts.length, 2);
    assert.deepEqual(result.plan.changes.question_rebindings, [{
        question_id: 'q2',
        from_canonical_id: 'cq_source',
        to_canonical_id: 'cq_redis_fast',
    }]);
    assert.deepEqual(result.plan.changes.review_migrations, []);
    assert.deepEqual(result.plan.changes.answer_invalidations, []);
    assert.deepEqual(result.plan.changes.answer_archives, []);
    assert.equal(result.plan.changes.rebuild_indexes, true);
    assert.equal(result.plan.changes.history_entry, null);

    const sourcePlanRecord = result.plan.changes.canonical_upserts
        .find((item) => item.canonical_id === 'cq_source');
    assert.deepEqual(sourcePlanRecord.question_ids, ['q1']);
    assert.equal(sourcePlanRecord.frequency, 1);
    assert.deepEqual(sourcePlanRecord.companies, ['美团']);

    const newPlanRecord = result.plan.changes.canonical_upserts
        .find((item) => item.canonical_id === 'cq_redis_fast');
    assert.deepEqual(newPlanRecord.question_ids, ['q2']);
    assert.equal(newPlanRecord.frequency, 3);
    assert.equal(newPlanRecord.review_priority, 'P1');
    assert.deepEqual(newPlanRecord.primary_domain, { l1: '缓存', l2: 'Redis' });
    assert.deepEqual(newPlanRecord.primary_entities, ['Redis']);
    assert.deepEqual(
        newPlanRecord.companies,
        ['字节', '阿里'].sort((a, b) => a.localeCompare(b, 'zh')),
    );
    assert.deepEqual(
        newPlanRecord.aliases,
        ['Redis 为什么快？', 'Redis 性能为什么高？', 'Redis 单线程为什么快？']
            .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh')),
    );

    const state = adapters.snapshot();
    assert.deepEqual(
        state.canonicals.map((item) => item.canonical_id).sort(),
        ['cq_redis_fast', 'cq_source'],
    );
    assert.deepEqual(
        state.bindings
            .filter((item) => item.question_id === 'q2')
            .map((item) => item.canonical_id),
        ['cq_redis_fast', 'cq_redis_fast', 'cq_redis_fast'],
    );
    assert.equal(state.effects.index_rebuild_count, 1);
    assert.deepEqual(state.effects.history, []);
});

test('removes the source canonical when its last question is split out', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [canonical('cq_source', ['q1'])],
        bindings: [binding('q1', 'cq_source', 1, '美团')],
    });
    const split = createUseCase(adapters);

    const result = await split({
        source: 'cq_source',
        question_id: 'q1',
        new_canonical_id: 'cq_new',
        title: '新的 Canonical',
    });

    assert.deepEqual(result.plan.changes.canonical_removals, ['cq_source']);
    assert.deepEqual(
        result.plan.changes.canonical_upserts.map((item) => item.canonical_id),
        ['cq_new'],
    );
    assert.equal(result.canonical_count, 1);
    assert.deepEqual(adapters.snapshot().canonicals.map((item) => item.canonical_id), ['cq_new']);
});

test('rejects an existing new canonical before mutation preflight', async () => {
    const seed = createSeed();
    seed.canonicals.push(canonical('cq_existing', ['q9']));
    const adapters = createInMemoryCanonicalAdapters(seed);
    const before = adapters.snapshot();
    let preflightCalled = false;
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            preflightCalled = true;
            return adapters.mutationStore.preflight(plan);
        },
    };
    const split = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        split({
            source: 'cq_source',
            question_id: 'q2',
            new_canonical_id: 'cq_existing',
            title: 'duplicate',
        }),
        /Canonical already exists: cq_existing/,
    );
    assert.equal(preflightCalled, false);
    assert.deepEqual(adapters.snapshot(), before);
});

test('rejects a stale question snapshot without publishing split state', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const before = adapters.snapshot();
    const originalPreflight = adapters.mutationStore.preflight.bind(adapters.mutationStore);
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            adapters.mutationStore.bumpRevision('question-bindings-by-question:q2');
            return originalPreflight(plan);
        },
    };
    const split = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        split({
            source: 'cq_source',
            question_id: 'q2',
            new_canonical_id: 'cq_new',
            title: 'Redis 为什么快？',
        }),
        /Revision mismatch for question-bindings-by-question:q2/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('commit failure leaves the whole split state unchanged', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const before = adapters.snapshot();
    adapters.mutationStore.failNextCommit(new Error('injected split commit failure'));
    const split = createUseCase(adapters);

    await assert.rejects(
        split({
            source: 'cq_source',
            question_id: 'q2',
            new_canonical_id: 'cq_new',
            title: 'Redis 为什么快？',
        }),
        /injected split commit failure/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('preserves legacy post-check semantics when integrity is false after a committed split', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const split = createUseCase(adapters, {
        integrityChecker: {
            async check() {
                return passingIntegrityReport({
                    ok: false,
                    binding_mismatch_count: 1,
                    binding_mismatches: [{ question_id: 'q-external' }],
                });
            },
        },
    });

    const result = await split({
        source: 'cq_source',
        question_id: 'q2',
        new_canonical_id: 'cq_new',
        title: 'Redis 为什么快？',
    });

    assert.equal(result.ok, false);
    assert.equal(result.integrity.binding_mismatch_count, 1);
    assert.equal(adapters.snapshot().canonicals.some((item) => item.canonical_id === 'cq_new'), true);
});
