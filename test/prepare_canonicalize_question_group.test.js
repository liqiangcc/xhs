'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    createPrepareCanonicalizeQuestionGroupUseCase,
} = require('../src/application/canonical/prepare-canonicalize-question-group');
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

function canonicalizationPlan(overrides = {}) {
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

function createUseCase(adapters) {
    return createPrepareCanonicalizeQuestionGroupUseCase({
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        canonicalQuestionOwnershipRepository: adapters.canonicalQuestionOwnershipRepository,
        taxonomy: TAXONOMY,
    });
}

test('prepare create loads current rows and ownership and returns projection plus opaque expected revisions', async () => {
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
    const prepare = createUseCase(adapters);

    const result = await prepare({ plan: canonicalizationPlan() });

    assert.equal(result.ok, true);
    assert.equal(result.canonical_id, 'cq_redis_performance');
    assert.deepEqual(result.question_ids, ['q_a', 'q_b']);
    assert.equal(result.projected_record.canonical_title, 'Redis 为什么快？');
    assert.deepEqual(result.projected_record.question_ids, ['q_a', 'q_b']);
    assert.deepEqual(result.projected_record.primary_entities, ['Redis']);
    assert.equal(result.projected_record.frequency, 2);
    assert.deepEqual(result.expected_revisions, [
        { resource: 'canonical:cq_redis_performance', revision: 'rev-0' },
        { resource: 'question-bindings-by-question:q_a', revision: 'rev-0' },
        { resource: 'question-bindings-by-question:q_b', revision: 'rev-0' },
        { resource: 'canonical-ownership-by-question:q_a', revision: 'rev-0' },
        { resource: 'canonical-ownership-by-question:q_b', revision: 'rev-0' },
    ]);

    for (const forbidden of ['mutation_plan', 'operation', 'changes', 'preflight', 'commit']) {
        assert.equal(Object.hasOwn(result, forbidden), false);
    }
    assert.deepEqual(adapters.snapshot().canonicals, []);
});

test('prepare extend loads existing and planned membership before projection', async () => {
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
            }),
        ],
    });
    const prepare = createUseCase(adapters);
    const plan = canonicalizationPlan({
        plan_kind: 'extend_existing_canonical',
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'existing',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 性能原理',
            title_resolution: 'preserve_existing',
        },
    });

    const result = await prepare({ plan });

    assert.deepEqual(result.question_ids, ['q_a', 'q_b', 'q_existing']);
    assert.equal(result.projected_record.canonical_title, 'Redis 性能原理');
    assert.equal(result.projected_record.answer_status, 'curated');
    assert.equal(result.projected_record.review_priority, 'P0');
    assert.equal(result.projected_record.frequency, 3);
    assert.deepEqual(result.projected_record.companies, ['阿里', '美团', '字节'].sort((a, b) => a.localeCompare(b, 'zh')));
    assert.deepEqual(adapters.snapshot().canonicals, [existing]);
});

test('prepare rejects planned Questions already owned or bound by another Canonical', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [{
            ...existingCanonical({
                canonical_id: 'cq_other',
                canonical_title: 'Other',
                question_ids: ['q_b'],
            }),
        }],
        bindings: [
            question(),
            question({
                question_id: 'q_b',
                source_note_id: 'note-b',
                canonical_id: 'cq_other',
            }),
        ],
    });
    const prepare = createUseCase(adapters);

    await assert.rejects(
        prepare({ plan: canonicalizationPlan() }),
        /Question q_b already belongs to cq_other/,
    );
});

test('prepare rejects inconsistent existing Canonical membership instead of projecting partial state', async () => {
    const existing = existingCanonical();
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [existing],
        bindings: [
            question({
                question_id: 'q_existing',
                source_note_id: 'note-existing',
                canonical_id: null,
            }),
            question(),
            question({ question_id: 'q_b', source_note_id: 'note-b' }),
        ],
    });
    const prepare = createUseCase(adapters);
    const plan = canonicalizationPlan({
        plan_kind: 'extend_existing_canonical',
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'existing',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 性能原理',
            title_resolution: 'preserve_existing',
        },
    });

    await assert.rejects(
        prepare({ plan }),
        /inconsistent binding for question q_existing/,
    );
});

test('prepare rejects a stale Canonical target identity before reading a projection as current', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    adapters.testSupport.upsertCanonical(existingCanonical({ question_ids: [] }));
    const prepare = createUseCase(adapters);

    await assert.rejects(
        prepare({ plan: canonicalizationPlan() }),
        /Canonical target identity revision changed since planning/,
    );
});

test('prepare rejects caller-controlled snapshots, rows, ownership, and revision evidence', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        bindings: [question(), question({ question_id: 'q_b', source_note_id: 'note-b' })],
    });
    const prepare = createUseCase(adapters);

    for (const forged of [
        { canonical_snapshot: {} },
        { question_rows: [] },
        { ownership_snapshots: [] },
        { expected_revisions: [] },
        { projected_record: {} },
    ]) {
        await assert.rejects(
            prepare({ plan: canonicalizationPlan(), ...forged }),
            /preparation state is controlled by Application/,
        );
    }
});
