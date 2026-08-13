'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    createPrepareCanonicalizeQuestionGroupUseCase,
} = require('../src/application/canonical/prepare-canonicalize-question-group');
const {
    createCanonicalizeQuestionGroupMutationPlan,
} = require('../src/application/canonical/plan-canonicalize-question-group-mutation');
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

function prepareUseCase(adapters) {
    return createPrepareCanonicalizeQuestionGroupUseCase({
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        canonicalQuestionOwnershipRepository: adapters.canonicalQuestionOwnershipRepository,
        taxonomy: TAXONOMY,
    });
}

test('create preparation maps to canonicalize MutationPlan with null-to-target rebindings only', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [
            question(),
            question({
                question_id: 'q_b',
                source_note_id: 'note-b',
                original_question: 'Redis 为什么这么快？',
                company: '字节',
            }),
        ],
    });
    const preparation = await prepareUseCase(adapters)({ plan: plan() });

    assert.deepEqual(preparation.planned_question_binding_states, [
        { question_id: 'q_a', from_canonical_ids: [null] },
        { question_id: 'q_b', from_canonical_ids: [null] },
    ]);

    const mutationPlan = createCanonicalizeQuestionGroupMutationPlan(preparation);

    assert.equal(mutationPlan.schema_version, 'canonical_mutation_plan.v1');
    assert.equal(mutationPlan.operation, 'canonicalize');
    assert.deepEqual(mutationPlan.expected_revisions, preparation.expected_revisions);
    assert.deepEqual(mutationPlan.changes.canonical_upserts, [preparation.projected_record]);
    assert.deepEqual(mutationPlan.changes.canonical_removals, []);
    assert.deepEqual(mutationPlan.changes.question_rebindings, [
        {
            question_id: 'q_a',
            from_canonical_id: null,
            to_canonical_id: 'cq_redis_performance',
        },
        {
            question_id: 'q_b',
            from_canonical_id: null,
            to_canonical_id: 'cq_redis_performance',
        },
    ]);
    assert.deepEqual(mutationPlan.changes.review_migrations, []);
    assert.deepEqual(mutationPlan.changes.answer_invalidations, []);
    assert.deepEqual(mutationPlan.changes.answer_archives, []);
    assert.equal(mutationPlan.changes.rebuild_indexes, true);
    assert.equal(mutationPlan.changes.history_entry, null);
    assert.equal(Object.isFrozen(mutationPlan), true);
    assert.equal(Object.hasOwn(mutationPlan, 'preflight'), false);
    assert.equal(Object.hasOwn(mutationPlan, 'commit'), false);
    assert.deepEqual(adapters.snapshot().canonicals, []);
});

test('extend planning treats target-to-target bindings as no-op and only rebinds remaining null rows', async () => {
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
    const preparation = await prepareUseCase(adapters)({ plan: extendPlan });

    assert.deepEqual(preparation.planned_question_binding_states, [
        { question_id: 'q_a', from_canonical_ids: [null] },
        { question_id: 'q_b', from_canonical_ids: ['cq_redis_performance'] },
    ]);

    const mutationPlan = createCanonicalizeQuestionGroupMutationPlan(preparation);

    assert.deepEqual(mutationPlan.changes.question_rebindings, [
        {
            question_id: 'q_a',
            from_canonical_id: null,
            to_canonical_id: 'cq_redis_performance',
        },
    ]);
    assert.equal(mutationPlan.changes.canonical_upserts[0].canonical_title, 'Redis 性能原理');
    assert.deepEqual(
        mutationPlan.changes.canonical_upserts[0].question_ids,
        ['q_a', 'q_b', 'q_existing'],
    );
    assert.deepEqual(adapters.snapshot().canonicals, [existing]);
});

test('planner preserves one null-to-target rebinding for mixed null and target source rows', async () => {
    const existing = existingCanonical();
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [existing],
        bindings: [
            question({
                question_id: 'q_existing',
                source_note_id: 'note-existing',
                canonical_id: 'cq_redis_performance',
            }),
            question({ question_id: 'q_a', source_note_id: 'note-a', canonical_id: null }),
            question({
                question_id: 'q_a',
                source_note_id: 'note-a-2',
                source_question_index: 1,
                canonical_id: 'cq_redis_performance',
            }),
            question({ question_id: 'q_b', source_note_id: 'note-b', canonical_id: null }),
        ],
    });
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
    const preparation = await prepareUseCase(adapters)({ plan: extendPlan });
    const mutationPlan = createCanonicalizeQuestionGroupMutationPlan(preparation);

    assert.deepEqual(preparation.planned_question_binding_states[0], {
        question_id: 'q_a',
        from_canonical_ids: [null, 'cq_redis_performance'],
    });
    assert.deepEqual(mutationPlan.changes.question_rebindings.map((item) => item.question_id), [
        'q_a',
        'q_b',
    ]);
});

test('pure planner rejects foreign binding state even when a caller forges a successful preparation', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const preparation = await prepareUseCase(adapters)({ plan: plan() });
    const forged = structuredClone(preparation);
    forged.planned_question_binding_states[1].from_canonical_ids = ['cq_other'];

    assert.throws(
        () => createCanonicalizeQuestionGroupMutationPlan(forged),
        /Question q_b already belongs to cq_other/,
    );
});

test('pure planner rejects target binding for an absent create target', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const preparation = await prepareUseCase(adapters)({ plan: plan() });
    const forged = structuredClone(preparation);
    forged.planned_question_binding_states[0].from_canonical_ids = ['cq_redis_performance'];

    assert.throws(
        () => createCanonicalizeQuestionGroupMutationPlan(forged),
        /binds to absent Canonical cq_redis_performance/,
    );
});

test('pure planner rejects incomplete binding states, stale target evidence, or projected membership drift', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const preparation = await prepareUseCase(adapters)({ plan: plan() });

    const incomplete = structuredClone(preparation);
    incomplete.planned_question_binding_states.pop();
    assert.throws(
        () => createCanonicalizeQuestionGroupMutationPlan(incomplete),
        /must cover exactly the planned question_ids/,
    );

    const staleTarget = structuredClone(preparation);
    staleTarget.expected_revisions[0].revision = 'newer-revision';
    assert.throws(
        () => createCanonicalizeQuestionGroupMutationPlan(staleTarget),
        /do not preserve target identity/,
    );

    const projectedDrift = structuredClone(preparation);
    projectedDrift.projected_record.question_ids = ['q_a'];
    assert.throws(
        () => createCanonicalizeQuestionGroupMutationPlan(projectedDrift),
        /question_ids do not match prepared membership/,
    );
});

test('pure planner is deterministic and does not mutate preparation', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const preparation = await prepareUseCase(adapters)({ plan: plan() });
    const before = structuredClone(preparation);

    const first = createCanonicalizeQuestionGroupMutationPlan(preparation);
    const second = createCanonicalizeQuestionGroupMutationPlan(preparation);

    assert.deepEqual(first, second);
    assert.deepEqual(preparation, before);
});
