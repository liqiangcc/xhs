'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createMergeCanonicalUseCase } = require('../src/application/canonical/merge-canonical');
const { createInMemoryCanonicalAdapters } = require('../src/infrastructure/in-memory/canonical-adapters');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: [],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: [],
        frequency: 0,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function createSeed() {
    return {
        canonicals: [
            canonical('cq_target', {
                canonical_title: 'Redis 为什么快？',
                aliases: ['Redis 为什么快？'],
                question_ids: ['q1'],
                companies: ['美团'],
                frequency: 1,
                review_priority: 'P1',
            }),
            canonical('cq_source', {
                canonical_title: 'Redis 单线程为什么快？',
                aliases: ['Redis 单线程为什么快？'],
                question_ids: ['q2', 'q3'],
                companies: ['字节'],
                frequency: 2,
                review_priority: 'P0',
            }),
        ],
        bindings: [
            { question_id: 'q1', canonical_id: 'cq_target', row_id: 'r1' },
            { question_id: 'q2', canonical_id: 'cq_source', row_id: 'r2' },
            { question_id: 'q3', canonical_id: 'cq_source', row_id: 'r3' },
        ],
    };
}

function createUseCase(adapters, overrides = {}) {
    return createMergeCanonicalUseCase({
        canonicalRepository: adapters.canonicalRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        mutationStore: adapters.mutationStore,
        clock: () => '2026-08-12T05:52:00.000Z',
        ...overrides,
    });
}

test('orchestrates merge through Domain policy, MutationPlan, preflight, commit, and post-check', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const merge = createUseCase(adapters);

    const result = await merge({
        target: 'cq_target',
        source: 'cq_source',
        reason: 'same interview knowledge point',
    });

    assert.equal(result.ok, true);
    assert.deepEqual(result.moved_question_ids, ['q2', 'q3']);
    assert.equal(Object.isFrozen(result.plan), true);
    assert.equal(result.plan.operation, 'merge');
    assert.equal(result.plan.expected_revisions.length, 4);
    assert.equal(result.plan.changes.rebuild_indexes, true);
    assert.deepEqual(result.plan.changes.canonical_removals, ['cq_source']);
    assert.equal(result.plan.changes.canonical_upserts[0].canonical_id, 'cq_target');
    assert.equal(result.plan.changes.canonical_upserts[0].answer_status, 'needs_update');
    assert.deepEqual(result.plan.changes.question_rebindings, [
        { question_id: 'q2', from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
        { question_id: 'q3', from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
    ]);

    const state = adapters.snapshot();
    assert.deepEqual(state.canonicals.map((record) => record.canonical_id), ['cq_target']);
    assert.deepEqual(
        state.canonicals[0].question_ids,
        ['q1', 'q2', 'q3'],
    );
    assert.deepEqual(
        state.bindings.map((binding) => [binding.question_id, binding.canonical_id]),
        [
            ['q1', 'cq_target'],
            ['q2', 'cq_target'],
            ['q3', 'cq_target'],
        ],
    );
    assert.deepEqual(state.effects.review_migrations, [
        { from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
    ]);
    assert.deepEqual(state.effects.answer_invalidations, [
        {
            canonical_id: 'cq_target',
            reason: 'canonical_merge',
            source_canonical_id: 'cq_source',
        },
    ]);
    assert.deepEqual(state.effects.answer_archives, [
        {
            canonical_id: 'cq_source',
            target_canonical_id: 'cq_target',
            reason: 'canonical_merge',
        },
    ]);
    assert.equal(state.effects.index_rebuild_count, 1);
    assert.deepEqual(state.effects.history, [{
        schema_version: 'canonical_merge.v1',
        merged_at: '2026-08-12T05:52:00.000Z',
        target: 'cq_target',
        source: 'cq_source',
        reason: 'same interview knowledge point',
        moved_question_ids: ['q2', 'q3'],
    }]);
});

test('rejects stale revisions during preflight without publishing mutation state', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const originalPreflight = adapters.mutationStore.preflight.bind(adapters.mutationStore);
    let injected = false;
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            if (!injected) {
                injected = true;
                adapters.mutationStore.bumpRevision(plan.expected_revisions[0].resource);
            }
            return originalPreflight(plan);
        },
    };
    const before = adapters.snapshot();
    const merge = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_source', reason: 'same' }),
        /Revision mismatch/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('injected commit failure leaves the complete formal state unchanged', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const before = adapters.snapshot();
    adapters.mutationStore.failNextCommit(new Error('injected commit failure'));
    const merge = createUseCase(adapters);

    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_source', reason: 'same' }),
        /injected commit failure/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('post-commit validation rejects a mutation store that reports success without applying the plan', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const mutationStore = {
        preflight: adapters.mutationStore.preflight.bind(adapters.mutationStore),
        async commit() {
            return { committed: true };
        },
    };
    const merge = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_source', reason: 'same' }),
        /Post-commit validation failed: source canonical cq_source still exists/,
    );
});

test('validates required merge input before loading or mutating state', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const before = adapters.snapshot();
    const merge = createUseCase(adapters);

    await assert.rejects(merge({ target: 'cq_target', source: 'cq_source' }), /target, source, and reason are required/);
    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_target', reason: 'same' }),
        /target and source must be different/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});
