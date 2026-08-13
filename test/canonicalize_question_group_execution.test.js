'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    createCanonicalizeQuestionGroupUseCase,
} = require('../src/application/canonical/canonicalize-question-group');
const {
    createInMemoryCanonicalAdapters,
} = require('../src/infrastructure/in-memory/canonical-adapters');

const TAXONOMY = Object.freeze({
    domain_l1: ['缓存', '数据库', '其他'],
    domain_l2_by_l1: {
        缓存: ['Redis', '其他'],
        数据库: ['MySQL', '其他'],
        其他: ['其他'],
    },
    entity_synonyms: {
        redis: 'Redis',
        'redis缓存': 'Redis',
    },
});

function plan(overrides = {}) {
    return {
        schema_version: 'canonicalization_plan.v1',
        plan_state: 'resolved',
        plan_kind: 'create_canonical',
        relation_candidate_key: 'entity|Redis|q_a,q_b',
        relation: 'same',
        question_ids: ['q_a', 'q_b'],
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'absent',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 为什么快？',
            title_resolution: 'use_requested',
        },
        target_identity: {
            resource: 'canonical:cq_redis_performance',
            revision: 'rev-0',
        },
        decision_provenance: {
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: [{ resource: 'source', revision: 'source-rev' }],
        },
        mutation_authorized: false,
        ...overrides,
    };
}

function question(overrides = {}) {
    return {
        question_id: 'q_a',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
        canonical_id: null,
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

function createUseCase(adapters, overrides = {}) {
    return createCanonicalizeQuestionGroupUseCase({
        canonicalIdentityRepository: overrides.canonicalIdentityRepository
            || adapters.canonicalIdentityRepository,
        questionBindingRepository: overrides.questionBindingRepository
            || adapters.questionBindingRepository,
        canonicalQuestionOwnershipRepository: overrides.canonicalQuestionOwnershipRepository
            || adapters.canonicalQuestionOwnershipRepository,
        mutationStore: overrides.mutationStore || adapters.mutationStore,
        taxonomy: TAXONOMY,
    });
}

test('execute create rebuilds fresh mutation evidence, commits atomically, and validates final ownership', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [
            question(),
            question({
                question_id: 'q_b',
                source_note_id: 'note-b',
                original_question: 'Redis 为什么这么快？',
                company: '字节',
                tech_entities: ['Redis缓存'],
            }),
        ],
    });
    const execute = createUseCase(adapters);

    const result = await execute({ plan: plan() });
    const state = adapters.snapshot();

    assert.equal(result.ok, true);
    assert.equal(result.canonical_id, 'cq_redis_performance');
    assert.equal(result.mutation_plan.operation, 'canonicalize');
    assert.equal(result.commit.committed, true);
    assert.equal(result.commit.operation, 'canonicalize');
    assert.equal(result.updated_question_rows, 2);
    assert.equal(state.canonicals.length, 1);
    assert.deepEqual(state.canonicals[0].question_ids, ['q_a', 'q_b']);
    assert.equal(state.canonicals[0].canonical_title, 'Redis 为什么快？');
    assert.ok(state.bindings.every((binding) => binding.canonical_id === 'cq_redis_performance'));
});

test('execute extend preserves authoritative Canonical state while assigning only unbound planned Questions', async () => {
    const existing = existingCanonical();
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [existing],
        bindings: [
            question({
                question_id: 'q_existing',
                source_note_id: 'note-existing',
                original_question: 'Redis 底层性能原理是什么？',
                company: '阿里',
                canonical_id: 'cq_redis_performance',
            }),
            question(),
            question({
                question_id: 'q_b',
                source_note_id: 'note-b',
                original_question: 'Redis 为什么这么快？',
                company: '字节',
                canonical_id: 'cq_redis_performance',
            }),
        ],
    });
    const execute = createUseCase(adapters);
    const extendPlan = plan({
        plan_kind: 'extend_existing_canonical',
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'existing',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 性能原理',
            title_resolution: 'preserve_existing',
        },
    });

    const result = await execute({ plan: extendPlan });
    const state = adapters.snapshot();
    const target = state.canonicals[0];

    assert.equal(result.commit.question_rebinding_count, 1);
    assert.equal(target.canonical_title, 'Redis 性能原理');
    assert.equal(target.answer_status, 'curated');
    assert.equal(target.review_priority, 'P0');
    assert.deepEqual(target.question_ids, ['q_a', 'q_b', 'q_existing']);
    assert.ok(state.bindings.every((binding) => binding.canonical_id === 'cq_redis_performance'));
});

test('stale revision introduced after Application planning is rejected by MutationStore preflight', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const before = adapters.snapshot();
    const mutationStore = {
        async preflight(mutationPlan) {
            adapters.mutationStore.bumpRevision('question-bindings-by-question:q_a');
            return adapters.mutationStore.preflight(mutationPlan);
        },
        async commit(mutationPlan, token) {
            return adapters.mutationStore.commit(mutationPlan, token);
        },
    };
    const execute = createUseCase(adapters, { mutationStore });

    await assert.rejects(
        execute({ plan: plan() }),
        /Revision mismatch for question-bindings-by-question:q_a/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('commit failure leaves Canonical and Question formal state unchanged', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const before = adapters.snapshot();
    adapters.mutationStore.failNextCommit(new Error('injected canonicalize commit failure'));
    const execute = createUseCase(adapters);

    await assert.rejects(
        execute({ plan: plan() }),
        /injected canonicalize commit failure/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});

test('post-commit validation detects a Canonical projection mismatch', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    let inspectCount = 0;
    const canonicalIdentityRepository = {
        async inspect(canonicalId) {
            inspectCount += 1;
            const snapshot = await adapters.canonicalIdentityRepository.inspect(canonicalId);
            if (inspectCount === 2 && snapshot.record) {
                return {
                    ...snapshot,
                    record: {
                        ...snapshot.record,
                        canonical_title: 'corrupted after commit',
                    },
                };
            }
            return snapshot;
        },
    };
    const execute = createUseCase(adapters, { canonicalIdentityRepository });

    await assert.rejects(
        execute({ plan: plan() }),
        /Post-commit validation failed: Canonical cq_redis_performance does not match projection/,
    );
    assert.equal(adapters.snapshot().canonicals.length, 1);
});

test('execute rejects caller-controlled mutation evidence', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const execute = createUseCase(adapters);

    for (const forged of [
        { mutation_plan: {} },
        { expected_revisions: [] },
        { projected_record: {} },
        { preflight: {} },
        { commit: {} },
    ]) {
        await assert.rejects(
            execute({ plan: plan(), ...forged }),
            /Canonical execution state is controlled by Application/,
        );
    }
});
