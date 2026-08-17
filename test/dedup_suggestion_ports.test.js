'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    assertDedupIndexRetrievalRepository,
} = require('../src/ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupHotspotRetrievalRepository,
} = require('../src/ports/repositories/dedup-hotspot-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../src/ports/repositories/dedup-question-retrieval-repository');
const {
    assertRelationCandidateRepository,
} = require('../src/ports/repositories/relation-candidate-repository');
const {
    assertRelationDecisionRepository,
} = require('../src/ports/repositories/relation-decision-repository');
const { assertRelationCandidatePublisher } = require('../src/ports/relation-candidate-publisher');
const { assertRelationDecisionStore } = require('../src/ports/relation-decision-store');
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

test('dedup suggestion and decision Ports stay narrow and reject missing capabilities', () => {
    assert.equal(assertDedupIndexRetrievalRepository({ findEntityRefs() {} }).findEntityRefs instanceof Function, true);
    assert.equal(assertDedupHotspotRetrievalRepository({ listHotspots() {} }).listHotspots instanceof Function, true);
    assert.equal(assertDedupQuestionRetrievalRepository({ findByRefs() {} }).findByRefs instanceof Function, true);
    assert.equal(assertRelationCandidateRepository({ get() {} }).get instanceof Function, true);
    assert.equal(assertRelationDecisionRepository({ get() {} }).get instanceof Function, true);
    assert.equal(assertRelationCandidatePublisher({ replaceQueue() {} }).replaceQueue instanceof Function, true);
    assert.equal(assertRelationDecisionStore({ record() {} }).record instanceof Function, true);

    assert.throws(
        () => assertDedupIndexRetrievalRepository({}),
        /findEntityRefs\(\) is required/,
    );
    assert.throws(
        () => assertDedupHotspotRetrievalRepository({}),
        /listHotspots\(\) is required/,
    );
    assert.throws(
        () => assertDedupQuestionRetrievalRepository({}),
        /findByRefs\(\) is required/,
    );
    assert.throws(
        () => assertRelationCandidateRepository({}),
        /get\(\) is required/,
    );
    assert.throws(
        () => assertRelationDecisionRepository({}),
        /get\(\) is required/,
    );
    assert.throws(
        () => assertRelationCandidatePublisher({}),
        /replaceQueue\(\) is required/,
    );
    assert.throws(
        () => assertRelationDecisionStore({}),
        /record\(\) is required/,
    );
});

test('in-memory retrieval adapters expose opaque revisions that change with their source state', async () => {
    const q1 = {
        question_id: 'q1',
        source_note_id: 'note-a',
        source_question_index: 0,
        original_question: 'Redis 为什么快？',
    };
    const hotspot = {
        canonical_id: null,
        question_id: 'q1',
        frequency: 2,
        refs: [questionRef(q1)],
    };
    const adapters = createInMemoryDedupSuggestionAdapters({
        questions: [q1],
        entity_refs: { Redis: [questionRef(q1)] },
        hotspots: [hotspot],
    });

    const firstIndex = await adapters.indexRepository.findEntityRefs('Redis');
    const firstHotspots = await adapters.hotspotRepository.listHotspots();
    const firstQuestions = await adapters.questionRepository.findByRefs(firstIndex.refs);

    adapters.testSupport.replaceEntityRefs('Redis', []);
    adapters.testSupport.replaceHotspots([{ ...hotspot, frequency: 3 }]);
    adapters.testSupport.replaceQuestions([{ ...q1, original_question: 'Redis 为什么这么快？' }]);

    const secondIndex = await adapters.indexRepository.findEntityRefs('Redis');
    const secondHotspots = await adapters.hotspotRepository.listHotspots();
    const secondQuestions = await adapters.questionRepository.findByRefs([questionRef(q1)]);

    assert.equal(firstIndex.resource, secondIndex.resource);
    assert.notEqual(firstIndex.revision, secondIndex.revision);
    assert.equal(firstHotspots.resource, 'dedup-hotspot-index');
    assert.equal(firstHotspots.resource, secondHotspots.resource);
    assert.notEqual(firstHotspots.revision, secondHotspots.revision);
    assert.equal(firstQuestions.resource, secondQuestions.resource);
    assert.notEqual(firstQuestions.revision, secondQuestions.revision);
});

test('relation candidate publisher replaces one review queue without becoming a Canonical mutation store', async () => {
    const adapters = createInMemoryDedupSuggestionAdapters();
    const first = await adapters.relationCandidatePublisher.replaceQueue({
        schema_version: 'dedup_relation_candidate_queue.v1',
        mode: 'entity',
        seed: 'Redis',
        source_revisions: [{ resource: 'source', revision: 'rev-source' }],
        candidate_count: 1,
        relation_candidates: [{ relation_candidate_key: 'entity|Redis|q1,q2', review_state: 'pending' }],
    });
    const candidate = await adapters.relationCandidateRepository.get('entity|Redis|q1,q2');
    const second = await adapters.relationCandidatePublisher.replaceQueue({
        schema_version: 'dedup_relation_candidate_queue.v1',
        mode: 'entity',
        seed: 'Redis',
        source_revisions: [],
        candidate_count: 0,
        relation_candidates: [],
    });

    assert.equal(first.resource, 'dedup-relation-queue:entity:Redis');
    assert.equal(candidate.resource, first.resource);
    assert.equal(candidate.revision, first.revision);
    assert.deepEqual(candidate.source_revisions, [{ resource: 'source', revision: 'rev-source' }]);
    assert.equal(second.resource, first.resource);
    assert.notEqual(second.revision, first.revision);
    assert.equal(second.candidate_count, 0);
    assert.equal(Object.hasOwn(adapters.relationCandidatePublisher, 'preflight'), false);
    assert.equal(Object.hasOwn(adapters.relationCandidatePublisher, 'commit'), false);
    assert.equal(Object.hasOwn(adapters.relationCandidatePublisher, 'merge'), false);
    assert.deepEqual(adapters.snapshot().queues[second.resource].relation_candidates, []);
});

test('relation decision store and repository are audit boundaries, not Apply boundaries', async () => {
    const adapters = createInMemoryDedupSuggestionAdapters();
    const queue = await adapters.relationCandidatePublisher.replaceQueue({
        schema_version: 'dedup_relation_candidate_queue.v1',
        mode: 'entity',
        seed: 'Redis',
        source_revisions: [],
        candidate_count: 0,
        relation_candidates: [],
    });
    const decision = {
        schema_version: 'dedup_relation_decision.v1',
        relation_candidate_key: 'entity|Redis|q1,q2',
        relation: 'same',
        decision_state: 'explicit',
    };
    const stored = await adapters.relationDecisionStore.record(decision, {
        expected_revisions: [{ resource: queue.resource, revision: queue.revision }],
    });
    const snapshot = await adapters.relationDecisionRepository.get(decision.relation_candidate_key);

    assert.equal(stored.recorded, true);
    assert.equal(stored.resource, 'dedup-relation-decisions');
    assert.equal(snapshot.resource, 'dedup-relation-decision:entity|Redis|q1,q2');
    assert.match(snapshot.revision, /^rev-/);
    assert.deepEqual(snapshot.decision, decision);
    assert.equal(adapters.snapshot().decisions.length, 1);
    assert.equal(Object.hasOwn(adapters.relationDecisionStore, 'preflight'), false);
    assert.equal(Object.hasOwn(adapters.relationDecisionStore, 'commit'), false);
    assert.equal(Object.hasOwn(adapters.relationDecisionStore, 'merge'), false);
    assert.equal(Object.hasOwn(adapters.relationDecisionStore, 'accept'), false);
    assert.equal(Object.hasOwn(adapters.relationDecisionStore, 'apply'), false);
    assert.equal(Object.hasOwn(adapters.relationDecisionRepository, 'record'), false);
    assert.equal(Object.hasOwn(adapters.relationDecisionRepository, 'apply'), false);
});
