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

async function suggest(adapters) {
    const useCase = createSuggestCanonicalRelationsUseCase({
        taxonomy,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        relationCandidatePublisher: adapters.relationCandidatePublisher,
    });
    return useCase({ mode: 'entity', seed: 'redis', limit: 10 });
}

function decisionUseCase(adapters, overrides = {}) {
    return createRecordRelationDecisionUseCase({
        relationCandidateRepository: adapters.relationCandidateRepository,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        relationDecisionStore: overrides.relationDecisionStore || adapters.relationDecisionStore,
    });
}

test('record relation decision loads the current review candidate and stores only an explicit decision', async () => {
    const { adapters } = fixture();
    const suggestions = await suggest(adapters);
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    const useCase = decisionUseCase(adapters);

    const result = await useCase({
        relation_candidate_key: relationCandidateKey,
        relation: 'same',
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: '两道题表达同一知识点',
        decided_at: '2026-08-13T10:00:00+08:00',
    });

    assert.equal(result.ok, true);
    assert.equal(result.relation_candidate_key, relationCandidateKey);
    assert.equal(result.relation, 'same');
    assert.equal(result.decision.decision_state, 'explicit');
    assert.equal(result.store.resource, 'dedup-relation-decisions');
    assert.match(result.store.revision, /^rev-/);
    assert.equal(Object.hasOwn(result, 'plan'), false);
    assert.equal(Object.hasOwn(result, 'commit'), false);
    assert.equal(Object.hasOwn(result.decision, 'canonical_id'), false);
    assert.equal(Object.hasOwn(result.decision, 'mutation_plan'), false);

    const state = adapters.snapshot();
    assert.equal(state.decisions.length, 1);
    assert.equal(state.decisions[0].relation_candidate_key, relationCandidateKey);
    assert.equal(state.decisions[0].relation, 'same');
});

test('record relation decision rejects a candidate whose Question source changed after suggestion', async () => {
    const { q1, q2, adapters } = fixture();
    const suggestions = await suggest(adapters);
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;

    adapters.testSupport.replaceQuestions([
        q1,
        { ...q2, original_question: 'Redis 为什么会这么快？' },
    ]);

    await assert.rejects(
        decisionUseCase(adapters)({
            relation_candidate_key: relationCandidateKey,
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
        }),
        /Stale relation candidate source dedup-question-catalog/,
    );
    assert.deepEqual(adapters.snapshot().decisions, []);
});

test('decision store rejects a source race that happens after Application freshness validation', async () => {
    const { adapters } = fixture();
    const suggestions = await suggest(adapters);
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    const racingStore = {
        async record(decision, options) {
            adapters.testSupport.replaceEntityRefs('Redis', []);
            return adapters.relationDecisionStore.record(decision, options);
        },
    };

    await assert.rejects(
        decisionUseCase(adapters, { relationDecisionStore: racingStore })({
            relation_candidate_key: relationCandidateKey,
            relation: 'same',
            actor: { type: 'ai', id: 'review-agent' },
        }),
        /Revision mismatch for dedup-entity-index:Redis/,
    );
    assert.deepEqual(adapters.snapshot().decisions, []);
});

test('decision store rejects a review queue race after the candidate was loaded', async () => {
    const { adapters } = fixture();
    const suggestions = await suggest(adapters);
    const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
    const queueResource = suggestions.queue.resource;
    const racingStore = {
        async record(decision, options) {
            const currentQueue = adapters.snapshot().queues[queueResource];
            await adapters.relationCandidatePublisher.replaceQueue(currentQueue);
            return adapters.relationDecisionStore.record(decision, options);
        },
    };

    await assert.rejects(
        decisionUseCase(adapters, { relationDecisionStore: racingStore })({
            relation_candidate_key: relationCandidateKey,
            relation: 'related',
            actor: { type: 'human', id: 'reviewer-2' },
        }),
        /Revision mismatch for dedup-relation-queue:entity:Redis/,
    );
    assert.deepEqual(adapters.snapshot().decisions, []);
});

test('record relation decision rejects missing candidates and caller-controlled evidence snapshots', async () => {
    const { adapters } = fixture();
    const useCase = decisionUseCase(adapters);

    await assert.rejects(
        useCase({
            relation_candidate_key: 'entity|Redis|missing',
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
        }),
        /Relation candidate not found/,
    );

    await assert.rejects(
        useCase({
            relation_candidate_key: 'entity|Redis|q1,q2',
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: [{ resource: 'fake', revision: 'fake' }],
        }),
        /revisions are controlled by Application/,
    );
});
