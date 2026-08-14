'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createRelationCandidate } = require('../src/domain/dedup/relation-candidate');
const { createRelationDecision } = require('../src/domain/dedup/relation-decision');
const { createRelationApplyIntent } = require('../src/domain/dedup/relation-apply-intent');
const {
    createCanonicalizationPlan,
    createResolveQuestionGroupCanonicalizationUseCase,
} = require('../src/application/canonical/resolve-question-group-canonicalization');
const {
    createInMemoryCanonicalAdapters,
} = require('../src/infrastructure/in-memory/canonical-adapters');

function relationDecision(relation = 'same') {
    const candidate = createRelationCandidate({
        scope: 'entity',
        seed: 'Redis',
        cluster: {
            domain_key: '缓存/Redis',
            anchor_question_id: 'q_a',
            question_ids: ['q_b', 'q_a'],
            member_count: 2,
            distinct_source_count: 2,
            members: [
                { question_id: 'q_a', source_note_id: 'note-a', source_question_index: 0 },
                { question_id: 'q_b', source_note_id: 'note-b', source_question_index: 0 },
            ],
            evidence: [{
                signal: 'jaccard',
                left_question_id: 'q_a',
                right_question_id: 'q_b',
                score: 0.6,
                threshold: 0.38,
                matched: true,
            }],
        },
    });
    return createRelationDecision({
        candidate,
        relation,
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: 'reviewed explicitly',
        decided_at: '2026-08-13T14:10:00+08:00',
        source_revisions: [
            { resource: 'dedup-entity-index:Redis', revision: 'index-rev-1' },
            { resource: 'dedup-questions-by-refs:abc', revision: 'question-rev-1' },
        ],
    });
}

function readyIntent(relation = 'same', overrides = {}) {
    return createRelationApplyIntent(relationDecision(relation), {
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
            ...overrides,
        },
    });
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

test('absent Canonical target resolves to a side-effect-free create plan', async () => {
    const adapters = createInMemoryCanonicalAdapters();
    const useCase = createResolveQuestionGroupCanonicalizationUseCase({
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
    });

    const result = await useCase({ intent: readyIntent('same') });

    assert.equal(result.ok, true);
    assert.equal(result.resolution, 'absent');
    assert.equal(result.canonical_id, 'cq_redis_performance');
    assert.equal(result.plan.schema_version, 'canonicalization_plan.v1');
    assert.equal(result.plan.plan_state, 'resolved');
    assert.equal(result.plan.plan_kind, 'create_canonical');
    assert.equal(result.plan.relation, 'same');
    assert.deepEqual(result.plan.question_ids, ['q_a', 'q_b']);
    assert.deepEqual(result.plan.canonical_target, {
        canonical_id: 'cq_redis_performance',
        resolution: 'absent',
        requested_title: 'Redis 为什么快？',
        effective_title: 'Redis 为什么快？',
        title_resolution: 'use_requested',
    });
    assert.equal(result.plan.target_identity.resource, 'canonical:cq_redis_performance');
    assert.equal(result.plan.target_identity.revision, 'rev-0');
    assert.equal(result.plan.mutation_authorized, false);
    assert.equal(Object.isFrozen(result.plan), true);
    assert.equal(Object.isFrozen(result.plan.canonical_target), true);

    for (const forbidden of [
        'candidate_id',
        'operation',
        'mutation_plan',
        'changes',
        'preflight',
        'commit',
        'accept',
        'merge',
    ]) {
        assert.equal(Object.hasOwn(result.plan, forbidden), false);
    }
    assert.deepEqual(adapters.snapshot().canonicals, []);
});

test('existing Canonical target resolves to extend and preserves the authoritative existing title', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [existingCanonical()],
    });
    const useCase = createResolveQuestionGroupCanonicalizationUseCase({
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
    });

    const result = await useCase({ intent: readyIntent('alias') });

    assert.equal(result.resolution, 'existing');
    assert.equal(result.plan.plan_kind, 'extend_existing_canonical');
    assert.equal(result.plan.relation, 'alias');
    assert.deepEqual(result.plan.canonical_target, {
        canonical_id: 'cq_redis_performance',
        resolution: 'existing',
        requested_title: 'Redis 为什么快？',
        effective_title: 'Redis 性能原理',
        title_resolution: 'preserve_existing',
    });
    assert.equal(result.plan.mutation_authorized, false);
    assert.deepEqual(adapters.snapshot().canonicals, [existingCanonical()]);
});

test('canonicalization plan is deterministic for a resolved identity snapshot', () => {
    const intent = readyIntent('same');
    const identity = {
        record: existingCanonical(),
        resource: 'canonical:cq_redis_performance',
        revision: 'canonical-rev-1',
    };

    const first = createCanonicalizationPlan({ intent, target_identity: identity });
    const second = createCanonicalizationPlan({ intent, target_identity: identity });

    assert.deepEqual(first, second);
    assert.equal(first.target_identity.revision, 'canonical-rev-1');
    assert.deepEqual(first.decision_provenance, intent.decision_provenance);
});

test('resolve rejects non-ready or non-canonicalization relation intents', async () => {
    const adapters = createInMemoryCanonicalAdapters();
    const useCase = createResolveQuestionGroupCanonicalizationUseCase({
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
    });

    const requiresInput = createRelationApplyIntent(relationDecision('same'));
    await assert.rejects(
        useCase({ intent: requiresInput }),
        /requires a ready intent/,
    );

    const relationOnly = createRelationApplyIntent(relationDecision('related'));
    await assert.rejects(
        useCase({ intent: relationOnly }),
        /Unsupported relation apply intent kind/,
    );
});

test('Application owns target resolution and rejects caller-controlled Canonical state', async () => {
    const adapters = createInMemoryCanonicalAdapters();
    const useCase = createResolveQuestionGroupCanonicalizationUseCase({
        canonicalIdentityRepository: adapters.canonicalIdentityRepository,
    });

    await assert.rejects(
        useCase({
            intent: readyIntent('same'),
            target_identity: {
                record: existingCanonical(),
                resource: 'fake',
                revision: 'fake',
            },
        }),
        /target state is controlled by Application/,
    );
    await assert.rejects(
        useCase({
            intent: readyIntent('same'),
            canonical_record: existingCanonical(),
        }),
        /target state is controlled by Application/,
    );
});

test('resolve rejects an inconsistent Canonical identity snapshot', () => {
    assert.throws(
        () => createCanonicalizationPlan({
            intent: readyIntent('same'),
            target_identity: {
                record: existingCanonical({ canonical_id: 'cq_other' }),
                resource: 'canonical:cq_redis_performance',
                revision: 'canonical-rev-1',
            },
        }),
        /Canonical target identity mismatch/,
    );
});
