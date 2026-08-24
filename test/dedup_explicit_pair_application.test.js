'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const taxonomy = require('../config/taxonomy.json');
const { createSuggestCanonicalRelationsUseCase } = require('../src/application/dedup/suggest-canonical-relations');
const { createRecordRelationDecisionUseCase } = require('../src/application/dedup/record-relation-decision');
const { createInMemoryDedupSuggestionAdapters } = require('../src/infrastructure/in-memory/dedup-suggestion-adapters');

function question(id, note, canonicalId) {
    return {
        question_id: id,
        original_question: `Question ${id}`,
        source_note_id: note,
        source_question_index: 0,
        company: '未知',
        domain: { l1: '计算机基础', l2: '数据结构与算法' },
        tech_entities: [],
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

function fixture() {
    const q1 = question('q_a', 'note-a', 'cq_a');
    const q2 = question('q_b', 'note-b', 'cq_b');
    const adapters = createInMemoryDedupSuggestionAdapters({ questions: [q1, q2] });
    return { q1, q2, adapters };
}

function suggestUseCase(adapters) {
    return createSuggestCanonicalRelationsUseCase({
        taxonomy,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        questionSelectionRepository: adapters.questionSelectionRepository,
        relationCandidatePublisher: adapters.relationCandidatePublisher,
    });
}

function decisionUseCase(adapters) {
    return createRecordRelationDecisionUseCase({
        relationCandidateRepository: adapters.relationCandidateRepository,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        questionSelectionRepository: adapters.questionSelectionRepository,
        relationDecisionGateway: adapters.relationDecisionGateway,
    });
}

test('pair suggestion emits one pending candidate for already-assigned Questions', async () => {
    const { adapters } = fixture();
    const result = await suggestUseCase(adapters)({
        mode: 'pair',
        question_ids: ['q_b', 'q_a'],
    });

    assert.equal(result.mode, 'pair');
    assert.equal(result.seed, 'q_a,q_b');
    assert.equal(result.candidate_count, 1);
    assert.equal(result.source_revisions.length, 1);
    assert.deepEqual(result.relation_candidates[0].question_ids, ['q_a', 'q_b']);
    assert.equal(result.relation_candidates[0].relation_candidate_key, 'pair|q_a,q_b|q_a,q_b');
    assert.equal(result.relation_candidates[0].evidence[0].relation_inference, 'none');
    assert.equal(Object.hasOwn(result.relation_candidates[0], 'relation'), false);
});

test('pair decision revalidates selected Question source and fails closed when stale', async () => {
    const { q1, q2, adapters } = fixture();
    const result = await suggestUseCase(adapters)({ mode: 'pair', question_ids: ['q_a', 'q_b'] });
    const key = result.relation_candidates[0].relation_candidate_key;

    adapters.testSupport.replaceQuestions([q1, { ...q2, original_question: 'Changed source fact' }]);

    await assert.rejects(
        decisionUseCase(adapters)({
            relation_candidate_key: key,
            relation: 'related',
            actor: { type: 'ai', id: 'review-agent' },
        }),
        /Stale relation candidate source dedup-question-catalog/,
    );
    assert.deepEqual(adapters.snapshot().decisions, []);
});
