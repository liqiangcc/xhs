'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const {
    createSuggestCanonicalRelationsUseCase,
} = require('../src/application/dedup/suggest-canonical-relations');
const {
    createRecordRelationDecisionUseCase,
} = require('../src/application/dedup/record-relation-decision');
const {
    createPrepareRelationApplyUseCase,
} = require('../src/application/dedup/prepare-relation-apply');
const {
    createInMemoryDedupSuggestionAdapters,
} = require('../src/infrastructure/in-memory/dedup-suggestion-adapters');

function question(overrides = {}) {
    return {
        question_id: 'q_default',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['Redis'],
        is_valid_for_library: true,
        canonical_id: null,
        ...overrides,
    };
}

function ref(row) {
    return {
        question_id: row.question_id,
        source_note_id: row.source_note_id,
        source_question_index: row.source_question_index,
    };
}

function fixture() {
    const q1 = question({
        question_id: 'q_redis_a',
        source_note_id: 'note-a',
        original_question: 'Redis 为什么快？',
    });
    const q2 = question({
        question_id: 'q_redis_b',
        source_note_id: 'note-b',
        original_question: 'Redis 为什么这么快？',
    });
    const adapters = createInMemoryDedupSuggestionAdapters({
        questions: [q1, q2],
        entity_refs: { Redis: [ref(q1), ref(q2)] },
    });
    return { q1, q2, adapters };
}

async function seedDecision(adapters, relation = 'same') {
    const suggest = createSuggestCanonicalRelationsUseCase({
        taxonomy,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        relationCandidatePublisher: adapters.relationCandidatePublisher,
    });
    const suggestions = await suggest({ mode: 'entity', seed: 'redis', limit: 10 });
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    const recordDecision = createRecordRelationDecisionUseCase({
        relationCandidateRepository: adapters.relationCandidateRepository,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        relationDecisionStore: adapters.relationDecisionStore,
    });
    await recordDecision({
        relation_candidate_key: relationCandidateKey,
        relation,
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: 'reviewed explicitly',
        decided_at: '2026-08-13T13:20:00+08:00',
    });
    return relationCandidateKey;
}

function prepareUseCase(adapters) {
    return createPrepareRelationApplyUseCase({
        relationDecisionRepository: adapters.relationDecisionRepository,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
    });
}

test('prepare relation apply reloads a persisted decision and produces only a ready ApplyIntent', async () => {
    const { adapters } = fixture();
    const relationCandidateKey = await seedDecision(adapters, 'same');

    const result = await prepareUseCase(adapters)({
        relation_candidate_key: relationCandidateKey,
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 为什么快？',
    });

    assert.equal(result.ok, true);
    assert.equal(result.relation, 'same');
    assert.equal(result.intent.intent_kind, 'canonicalize_question_group');
    assert.equal(result.intent.intent_state, 'ready');
    assert.deepEqual(result.intent.canonical_target, {
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 为什么快？',
    });
    assert.equal(result.decision_snapshot.resource, `dedup-relation-decision:${relationCandidateKey}`);
    assert.match(result.decision_snapshot.revision, /^rev-/);
    assert.equal(result.current_source_revisions.length, 2);
    assert.equal(Object.hasOwn(result, 'plan'), false);
    assert.equal(Object.hasOwn(result, 'commit'), false);
    assert.equal(Object.hasOwn(result.intent, 'operation'), false);
    assert.equal(Object.hasOwn(result.intent, 'mutation_plan'), false);
});

test('prepare relation apply can report missing target input without inventing a Canonical target', async () => {
    const { adapters } = fixture();
    const relationCandidateKey = await seedDecision(adapters, 'alias');

    const result = await prepareUseCase(adapters)({
        relation_candidate_key: relationCandidateKey,
    });

    assert.equal(result.relation, 'alias');
    assert.equal(result.intent.intent_state, 'requires_input');
    assert.deepEqual(result.intent.required_inputs, ['canonical_id', 'canonical_title']);
    assert.equal(Object.hasOwn(result.intent, 'canonical_target'), false);
});

test('prepare relation apply rejects a persisted decision whose Question source became stale', async () => {
    const { q1, q2, adapters } = fixture();
    const relationCandidateKey = await seedDecision(adapters, 'same');
    adapters.testSupport.replaceQuestions([
        q1,
        { ...q2, original_question: 'Redis 为什么会这么快？' },
    ]);

    await assert.rejects(
        prepareUseCase(adapters)({
            relation_candidate_key: relationCandidateKey,
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        }),
        /Stale relation candidate source dedup-question-catalog/,
    );
});

test('prepare relation apply preserves relation-only and no-op decisions instead of converting them to Canonical commands', async () => {
    for (const relation of ['parent_child', 'followup', 'related', 'unrelated']) {
        const { adapters } = fixture();
        const relationCandidateKey = await seedDecision(adapters, relation);
        const result = await prepareUseCase(adapters)({
            relation_candidate_key: relationCandidateKey,
        });

        assert.equal(result.relation, relation);
        assert.equal(result.intent.apply_required, false);
        assert.equal(result.intent.intent_state, 'complete');
        assert.equal(Object.hasOwn(result.intent, 'canonical_target'), false);

        await assert.rejects(
            prepareUseCase(adapters)({
                relation_candidate_key: relationCandidateKey,
                canonical_id: 'cq_forbidden',
                canonical_title: 'Forbidden target',
            }),
            new RegExp(`Relation ${relation} cannot target Canonical apply`),
        );
    }
});

test('prepare relation apply reads the latest persisted decision for one review candidate', async () => {
    const { adapters } = fixture();
    const relationCandidateKey = await seedDecision(adapters, 'same');
    const recordDecision = createRecordRelationDecisionUseCase({
        relationCandidateRepository: adapters.relationCandidateRepository,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        relationDecisionStore: adapters.relationDecisionStore,
    });
    await recordDecision({
        relation_candidate_key: relationCandidateKey,
        relation: 'alias',
        actor: { type: 'human', id: 'reviewer-2' },
        rationale: 're-reviewed as alias',
    });

    const result = await prepareUseCase(adapters)({
        relation_candidate_key: relationCandidateKey,
    });
    assert.equal(result.relation, 'alias');
    assert.equal(result.intent.relation, 'alias');
});

test('prepare relation apply rejects missing decisions, partial targets, and caller-controlled evidence', async () => {
    const { adapters } = fixture();
    const prepare = prepareUseCase(adapters);

    await assert.rejects(
        prepare({ relation_candidate_key: 'entity|Redis|missing' }),
        /Relation decision not found/,
    );

    const relationCandidateKey = await seedDecision(adapters, 'same');
    await assert.rejects(
        prepare({ relation_candidate_key: relationCandidateKey, canonical_id: 'cq_only' }),
        /canonical_id and canonical_title must be provided together/,
    );
    await assert.rejects(
        prepare({
            relation_candidate_key: relationCandidateKey,
            decision: { relation: 'same' },
        }),
        /evidence is controlled by Application/,
    );
    await assert.rejects(
        prepare({
            relation_candidate_key: relationCandidateKey,
            source_revisions: [{ resource: 'fake', revision: 'fake' }],
        }),
        /evidence is controlled by Application/,
    );
});
