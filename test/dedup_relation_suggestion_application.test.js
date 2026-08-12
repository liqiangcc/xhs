'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const {
    createSuggestCanonicalRelationsUseCase,
} = require('../src/application/dedup/suggest-canonical-relations');
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

function ref(item) {
    return {
        question_id: item.question_id,
        source_note_id: item.source_note_id,
        source_question_index: item.source_question_index,
    };
}

function createUseCase(questions, entitySeed, overrides = {}) {
    const adapters = createInMemoryDedupSuggestionAdapters({
        questions,
        entity_refs: {
            [entitySeed]: questions.map(ref),
        },
    });
    const useCase = createSuggestCanonicalRelationsUseCase({
        taxonomy,
        indexRepository: adapters.indexRepository,
        questionRepository: adapters.questionRepository,
        relationCandidateStore: adapters.relationCandidateStore,
        ...overrides,
    });
    return { useCase, adapters };
}

test('suggestion application retrieves facts and persists pending relation review queue only', async () => {
    const questions = [
        question({ question_id: 'q_redis_a', source_note_id: 'note-a', original_question: 'Redis 为什么快？' }),
        question({ question_id: 'q_redis_b', source_note_id: 'note-b', original_question: 'Redis 为什么这么快？' }),
        question({ question_id: 'q_redis_a', source_note_id: 'note-c', original_question: 'Redis 为什么快？' }),
        question({ question_id: 'q_mysql_a', source_note_id: 'note-d', original_question: 'MySQL 索引为什么用 B+ 树？', domain: { l1: '数据库', l2: 'MySQL' } }),
        question({ question_id: 'q_mysql_b', source_note_id: 'note-e', original_question: 'MySQL 为什么使用 B+ 树索引？', domain: { l1: '数据库', l2: 'MySQL' } }),
    ];
    const before = structuredClone(questions);
    const { useCase, adapters } = createUseCase(questions, 'database');

    const result = await useCase({
        mode: 'entity',
        seed: 'database',
        limit: 1,
    });

    assert.equal(result.schema_version, 'dedup_relation_suggestions.v1');
    assert.equal(result.mode, 'entity');
    assert.equal(result.seed, 'database');
    assert.equal(result.detection_count, 2);
    assert.equal(result.candidate_count, 1);
    assert.equal(result.relation_candidates[0].review_state, 'pending');
    assert.equal(result.relation_candidates[0].member_count, 3);
    assert.deepEqual(result.relation_candidates[0].question_ids, ['q_redis_a', 'q_redis_b']);
    assert.equal(result.relation_candidates[0].relation_candidate_key, 'entity|database|q_redis_a,q_redis_b');
    assert.equal(Object.hasOwn(result.relation_candidates[0], 'relation'), false);
    assert.equal(Object.hasOwn(result.relation_candidates[0], 'canonical_id'), false);
    assert.equal(Object.hasOwn(result, 'plan'), false);
    assert.equal(Object.hasOwn(result, 'commit'), false);
    assert.deepEqual(result.source_revisions.map((item) => item.resource), [
        'dedup-entity-index:database',
        'dedup-question-catalog',
    ]);
    assert.equal(result.queue.resource, 'dedup-relation-queue:entity:database');
    assert.equal(result.queue.candidate_count, 1);

    const storedQueue = adapters.snapshot().queues[result.queue.resource];
    assert.equal(storedQueue.schema_version, 'dedup_relation_candidate_queue.v1');
    assert.equal(storedQueue.candidate_count, 1);
    assert.deepEqual(storedQueue.source_revisions, result.source_revisions);
    assert.equal(storedQueue.relation_candidates[0].review_state, 'pending');
    assert.equal(Object.hasOwn(storedQueue.relation_candidates[0], 'relation'), false);
    assert.equal(Object.hasOwn(storedQueue.relation_candidates[0], 'canonical_id'), false);
    assert.deepEqual(questions, before);
});

test('suggestion application normalizes domain context after retrieving Questions', async () => {
    let detectorInput = null;
    const detector = (questions) => {
        detectorInput = structuredClone(questions);
        return [{
            domain_key: questions[0].domain_key,
            anchor_question_id: 'q_a',
            question_ids: ['q_a', 'q_b'],
            member_count: 2,
            distinct_source_count: 2,
            members: [
                { question_id: 'q_a', source_note_id: 'note-a', source_question_index: 0 },
                { question_id: 'q_b', source_note_id: 'note-b', source_question_index: 0 },
            ],
            evidence: [{
                signal: 'same_question_id',
                left_question_id: 'q_a',
                right_question_id: 'q_b',
                matched: true,
            }],
        }];
    };
    const questions = [
        question({ question_id: 'q_a' }),
        question({ question_id: 'q_b', source_note_id: 'note-b' }),
    ];
    const { useCase } = createUseCase(questions, 'Redis', {
        detectEntityQuestionClusters: detector,
    });

    await useCase({ mode: 'entity', seed: 'Redis' });

    assert.equal(detectorInput[0].domain_key, '缓存/Redis');
    assert.equal(detectorInput[1].domain_key, '缓存/Redis');
});

test('suggestion application owns retrieval and rejects bypassing Ports with raw Questions', async () => {
    const { useCase } = createUseCase([], 'Redis');

    await assert.rejects(
        useCase({ mode: 'entity', seed: 'Redis', questions: [] }),
        /must be retrieved through DedupQuestionRetrievalRepository/,
    );
});

test('suggestion application rejects unsupported modes and invalid limits before retrieval', async () => {
    const { useCase } = createUseCase([], 'Redis');

    await assert.rejects(
        useCase({ mode: 'hotspot', seed: 'hotspot' }),
        /Unsupported dedup suggestion mode/,
    );
    await assert.rejects(
        useCase({ mode: 'entity', seed: 'Redis', limit: -1 }),
        /Invalid suggestion limit/,
    );
});

test('suggestion application persists empty detection as an explicit empty review queue', async () => {
    const questions = [question()];
    const { useCase, adapters } = createUseCase(questions, 'Redis');
    const result = await useCase({ mode: 'entity', seed: 'Redis' });

    assert.equal(result.detection_count, 0);
    assert.equal(result.candidate_count, 0);
    assert.deepEqual(result.relation_candidates, []);
    const storedQueue = adapters.snapshot().queues[result.queue.resource];
    assert.equal(storedQueue.candidate_count, 0);
    assert.deepEqual(storedQueue.relation_candidates, []);
});
