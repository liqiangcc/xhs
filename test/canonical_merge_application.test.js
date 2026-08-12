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

function progress(canonicalId, overrides = {}) {
    return {
        canonical_id: canonicalId,
        status: 'learning',
        level: 2,
        review_count: 3,
        last_reviewed_at: '2026-08-01',
        next_review_at: '2026-08-10',
        confidence: 0.7,
        difficulty: 3,
        mistake_count: 0,
        updated_at: '2026-08-01',
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
        review_progress: [
            progress('cq_target', {
                level: 3,
                review_count: 2,
                last_reviewed_at: '2026-08-02',
                next_review_at: '2026-08-20',
                confidence: 0.8,
                difficulty: 2,
            }),
            progress('cq_source', {
                level: 1,
                review_count: 4,
                last_reviewed_at: '2026-08-05',
                next_review_at: '2026-08-08',
                confidence: 0.4,
                difficulty: 5,
                mistake_count: 1,
                updated_at: '2026-08-05',
            }),
        ],
        review_session_events: [
            { canonical_id: 'cq_target', result: 'good', event_id: 'e1' },
            { canonical_id: 'cq_source', result: 'hard', event_id: 'e2' },
        ],
    };
}

function createUseCase(adapters, overrides = {}) {
    return createMergeCanonicalUseCase({
        canonicalRepository: adapters.canonicalRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        reviewRepository: adapters.reviewRepository,
        mutationStore: adapters.mutationStore,
        clock: () => '2026-08-12T05:52:00.000Z',
        ...overrides,
    });
}

test('orchestrates merge with planned review progress and session migration in one mutation', async () => {
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
    assert.equal(result.plan.expected_revisions.length, 5);
    assert.match(result.plan.expected_revisions[4].resource, /^review-merge:/);
    assert.equal(result.plan.changes.rebuild_indexes, true);
    assert.deepEqual(result.plan.changes.canonical_removals, ['cq_source']);
    assert.equal(result.plan.changes.canonical_upserts[0].canonical_id, 'cq_target');
    assert.equal(result.plan.changes.canonical_upserts[0].answer_status, 'needs_update');
    assert.deepEqual(result.plan.changes.question_rebindings, [
        { question_id: 'q2', from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
        { question_id: 'q3', from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
    ]);

    const reviewMigration = result.plan.changes.review_migrations[0];
    assert.equal(reviewMigration.from_canonical_id, 'cq_source');
    assert.equal(reviewMigration.to_canonical_id, 'cq_target');
    assert.deepEqual(reviewMigration.progress.remove_canonical_ids, ['cq_target', 'cq_source']);
    assert.equal(reviewMigration.progress.upsert.canonical_id, 'cq_target');
    assert.equal(reviewMigration.progress.upsert.level, 1);
    assert.equal(reviewMigration.progress.upsert.review_count, 6);
    assert.equal(reviewMigration.progress.upsert.status, 'weak');
    assert.equal(reviewMigration.progress.upsert.confidence, 0.4);
    assert.equal(reviewMigration.progress.upsert.difficulty, 5);
    assert.equal(reviewMigration.progress.upsert.next_review_at, '2026-08-08');
    assert.deepEqual(reviewMigration.session_events, {
        rebind_from_canonical_id: 'cq_source',
        rebind_to_canonical_id: 'cq_target',
        annotate_migrated_from: true,
    });

    const state = adapters.snapshot();
    assert.deepEqual(state.canonicals.map((record) => record.canonical_id), ['cq_target']);
    assert.deepEqual(state.canonicals[0].question_ids, ['q1', 'q2', 'q3']);
    assert.deepEqual(
        state.bindings.map((binding) => [binding.question_id, binding.canonical_id]),
        [
            ['q1', 'cq_target'],
            ['q2', 'cq_target'],
            ['q3', 'cq_target'],
        ],
    );
    assert.equal(state.review_progress.length, 1);
    assert.equal(state.review_progress[0].canonical_id, 'cq_target');
    assert.equal(state.review_progress[0].level, 1);
    assert.equal(state.review_progress[0].review_count, 6);
    assert.equal(state.review_progress[0].mistake_count, 1);
    assert.deepEqual(
        state.review_session_events.map((event) => [
            event.event_id,
            event.canonical_id,
            event.migrated_from_canonical_id || null,
        ]),
        [
            ['e1', 'cq_target', null],
            ['e2', 'cq_target', 'cq_source'],
        ],
    );
    assert.deepEqual(state.effects.review_migrations, [reviewMigration]);
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

test('rejects stale canonical revisions during preflight without publishing mutation state', async () => {
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

test('rejects stale review revisions before canonical or review state is published', async () => {
    const adapters = createInMemoryCanonicalAdapters(createSeed());
    const originalPreflight = adapters.mutationStore.preflight.bind(adapters.mutationStore);
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            const reviewRevision = plan.expected_revisions.find((item) => item.resource.startsWith('review-merge:'));
            adapters.mutationStore.bumpRevision(reviewRevision.resource);
            return originalPreflight(plan);
        },
    };
    const before = adapters.snapshot();
    const merge = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_source', reason: 'same' }),
        /Revision mismatch for review-merge:/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('duplicate review progress is rejected while planning before mutation preflight', async () => {
    const seed = createSeed();
    seed.review_progress.push(progress('cq_source', { level: 0 }));
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
    const merge = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_source', reason: 'same' }),
        /Cannot merge review progress with duplicate rows/,
    );
    assert.equal(preflightCalled, false);
    assert.deepEqual(adapters.snapshot(), before);
});

test('injected commit failure leaves canonical, bindings, review progress, and sessions unchanged', async () => {
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
