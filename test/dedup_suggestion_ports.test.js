'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    assertDedupIndexRetrievalRepository,
} = require('../src/ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../src/ports/repositories/dedup-question-retrieval-repository');
const { assertRelationCandidateStore } = require('../src/ports/relation-candidate-store');
const {
    createInMemoryDedupSuggestionAdapters,
} = require('../src/infrastructure/in-memory/dedup-suggestion-adapters');

function questionRef(question) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
    };
}

test('dedup suggestion Ports stay narrow and reject missing capabilities', () => {
    assert.equal(assertDedupIndexRetrievalRepository({ findEntityRefs() {} }).findEntityRefs instanceof Function, true);
    assert.equal(assertDedupQuestionRetrievalRepository({ findByRefs() {} }).findByRefs instanceof Function, true);
    assert.equal(assertRelationCandidateStore({ replaceQueue() {} }).replaceQueue instanceof Function, true);

    assert.throws(
        () => assertDedupIndexRetrievalRepository({}),
        /findEntityRefs\(\) is required/,
    );
    assert.throws(
        () => assertDedupQuestionRetrievalRepository({}),
        /findByRefs\(\) is required/,
    );
    assert.throws(
        () => assertRelationCandidateStore({}),
        /replaceQueue\(\) is required/,
    );
});

test('in-memory retrieval adapters expose opaque revisions that change with their source state', async () => {
    const q1 = {
        question_id: 'q1',
        source_note_id: 'note-a',
        source_question_index: 0,
        original_question: 'Redis 为什么快？',
    };
    const adapters = createInMemoryDedupSuggestionAdapters({
        questions: [q1],
        entity_refs: { Redis: [questionRef(q1)] },
    });

    const firstIndex = await adapters.indexRepository.findEntityRefs('Redis');
    const firstQuestions = await adapters.questionRepository.findByRefs(firstIndex.refs);

    adapters.testSupport.replaceEntityRefs('Redis', []);
    adapters.testSupport.replaceQuestions([{ ...q1, original_question: 'Redis 为什么这么快？' }]);

    const secondIndex = await adapters.indexRepository.findEntityRefs('Redis');
    const secondQuestions = await adapters.questionRepository.findByRefs([questionRef(q1)]);

    assert.equal(firstIndex.resource, secondIndex.resource);
    assert.notEqual(firstIndex.revision, secondIndex.revision);
    assert.equal(firstQuestions.resource, secondQuestions.resource);
    assert.notEqual(firstQuestions.revision, secondQuestions.revision);
});

test('relation candidate store replaces one review queue without becoming a Canonical mutation store', async () => {
    const adapters = createInMemoryDedupSuggestionAdapters();
    const first = await adapters.relationCandidateStore.replaceQueue({
        schema_version: 'dedup_relation_candidate_queue.v1',
        mode: 'entity',
        seed: 'Redis',
        candidate_count: 1,
        relation_candidates: [{ relation_candidate_key: 'entity|Redis|q1,q2', review_state: 'pending' }],
    });
    const second = await adapters.relationCandidateStore.replaceQueue({
        schema_version: 'dedup_relation_candidate_queue.v1',
        mode: 'entity',
        seed: 'Redis',
        candidate_count: 0,
        relation_candidates: [],
    });

    assert.equal(first.resource, 'dedup-relation-queue:entity:Redis');
    assert.equal(second.resource, first.resource);
    assert.notEqual(second.revision, first.revision);
    assert.equal(second.candidate_count, 0);
    assert.equal(Object.hasOwn(adapters.relationCandidateStore, 'preflight'), false);
    assert.equal(Object.hasOwn(adapters.relationCandidateStore, 'commit'), false);
    assert.equal(Object.hasOwn(adapters.relationCandidateStore, 'merge'), false);
    assert.deepEqual(adapters.snapshot().queues[second.resource].relation_candidates, []);
});
