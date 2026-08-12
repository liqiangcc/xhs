'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { detectEntityQuestionClusters } = require('../src/domain/dedup/entity-cluster-detection');
const { groupEntityCandidates } = require('../scripts/commands/canonical');

function question(overrides = {}) {
    return {
        question_id: 'q_default',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        domain_key: '缓存/Redis',
        is_valid_for_library: true,
        canonical_id: null,
        ...overrides,
    };
}

test('entity detection groups same-domain similar questions and exposes evidence only', () => {
    const input = [
        question({ question_id: 'q_redis_fast', source_note_id: 'note-a', original_question: 'Redis 为什么快？' }),
        question({ question_id: 'q_redis_faster', source_note_id: 'note-b', original_question: 'Redis 为什么这么快？' }),
        question({ question_id: 'q_redis_persistence', source_note_id: 'note-c', original_question: 'Redis 持久化机制是什么？' }),
    ];
    const before = structuredClone(input);

    const clusters = detectEntityQuestionClusters(input);

    assert.equal(clusters.length, 1);
    assert.deepEqual(clusters[0].question_ids, ['q_redis_fast', 'q_redis_faster']);
    assert.equal(clusters[0].member_count, 2);
    assert.equal(clusters[0].distinct_source_count, 2);
    assert.equal(clusters[0].evidence.length, 1);
    assert.equal(clusters[0].evidence[0].signal, 'jaccard');
    assert.equal(clusters[0].evidence[0].matched, true);
    assert.ok(clusters[0].evidence[0].score >= 0.38);
    assert.equal(Object.hasOwn(clusters[0], 'canonical_id'), false);
    assert.equal(Object.hasOwn(clusters[0], 'candidate_id'), false);
    assert.equal(Object.hasOwn(clusters[0], 'relation'), false);
    assert.deepEqual(input, before);
});

test('same question id is a detection signal even when source rows have different domains', () => {
    const clusters = detectEntityQuestionClusters([
        question({ question_id: 'q_same', source_note_id: 'note-a', domain_key: '缓存/Redis' }),
        question({ question_id: 'q_same', source_note_id: 'note-b', domain_key: '中间件/Kafka' }),
    ]);

    assert.equal(clusters.length, 1);
    assert.deepEqual(clusters[0].question_ids, ['q_same']);
    assert.equal(clusters[0].distinct_source_count, 2);
    assert.deepEqual(clusters[0].evidence, [{
        signal: 'same_question_id',
        left_question_id: 'q_same',
        right_question_id: 'q_same',
        matched: true,
    }]);
});

test('different question ids do not compare across domains', () => {
    const clusters = detectEntityQuestionClusters([
        question({ question_id: 'q_a', source_note_id: 'note-a', domain_key: '缓存/Redis', original_question: 'Redis 为什么快？' }),
        question({ question_id: 'q_b', source_note_id: 'note-b', domain_key: '中间件/Kafka', original_question: 'Redis 为什么快？' }),
    ]);

    assert.deepEqual(clusters, []);
});

test('invalid or already assigned questions are outside the detection set', () => {
    const clusters = detectEntityQuestionClusters([
        question({ question_id: 'q_a', source_note_id: 'note-a' }),
        question({ question_id: 'q_b', source_note_id: 'note-b', original_question: 'Redis 为什么这么快？', canonical_id: 'cq_existing' }),
        question({ question_id: 'q_c', source_note_id: 'note-c', original_question: 'Redis 为什么这么快？', is_valid_for_library: false }),
    ]);

    assert.deepEqual(clusters, []);
});

test('same question id from only one source does not become a duplicate cluster', () => {
    const clusters = detectEntityQuestionClusters([
        question({ question_id: 'q_same', source_note_id: 'note-a', source_question_index: 0 }),
        question({ question_id: 'q_same', source_note_id: 'note-a', source_question_index: 1 }),
    ]);

    assert.deepEqual(clusters, []);
});

test('new detector characterizes the legacy entity grouping boundary without replacing production', () => {
    const legacyQuestions = [
        {
            question_id: 'q_redis_fast',
            original_question: 'Redis 为什么快？',
            source_note_id: 'note-a',
            source_question_index: 0,
            company: '美团',
            domain: { l1: '缓存', l2: 'Redis' },
            tech_entities: ['Redis'],
            is_valid_for_library: true,
            canonical_id: null,
        },
        {
            question_id: 'q_redis_faster',
            original_question: 'Redis 为什么这么快？',
            source_note_id: 'note-b',
            source_question_index: 0,
            company: '字节',
            domain: { l1: '缓存', l2: 'Redis' },
            tech_entities: ['Redis'],
            is_valid_for_library: true,
            canonical_id: null,
        },
        {
            question_id: 'q_redis_persistence',
            original_question: 'Redis 持久化机制是什么？',
            source_note_id: 'note-c',
            source_question_index: 0,
            company: '阿里',
            domain: { l1: '缓存', l2: 'Redis' },
            tech_entities: ['Redis'],
            is_valid_for_library: true,
            canonical_id: null,
        },
    ];

    const legacyQuestionGroups = groupEntityCandidates(legacyQuestions, 'redis', 10)
        .map((candidate) => candidate.question_ids);
    const detectedQuestionGroups = detectEntityQuestionClusters(
        legacyQuestions.map((item) => ({
            ...item,
            domain_key: `${item.domain.l1}/${item.domain.l2}`,
        })),
    ).map((cluster) => cluster.question_ids);

    assert.deepEqual(detectedQuestionGroups, legacyQuestionGroups);
});
