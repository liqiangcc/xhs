'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const {
    createSuggestCanonicalRelationsUseCase,
} = require('../src/application/dedup/suggest-canonical-relations');

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

test('suggestion application turns detection evidence into pending relation candidates only', async () => {
    const useCase = createSuggestCanonicalRelationsUseCase({ taxonomy });
    const questions = [
        question({ question_id: 'q_redis_a', source_note_id: 'note-a', original_question: 'Redis 为什么快？' }),
        question({ question_id: 'q_redis_b', source_note_id: 'note-b', original_question: 'Redis 为什么这么快？' }),
        question({ question_id: 'q_redis_a', source_note_id: 'note-c', original_question: 'Redis 为什么快？' }),
        question({ question_id: 'q_mysql_a', source_note_id: 'note-d', original_question: 'MySQL 索引为什么用 B+ 树？', domain: { l1: '数据库', l2: 'MySQL' } }),
        question({ question_id: 'q_mysql_b', source_note_id: 'note-e', original_question: 'MySQL 为什么使用 B+ 树索引？', domain: { l1: '数据库', l2: 'MySQL' } }),
    ];
    const before = structuredClone(questions);

    const result = await useCase({
        mode: 'entity',
        seed: 'database',
        questions,
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
    assert.equal(Object.hasOwn(result.relation_candidates[0], 'relation'), false);
    assert.equal(Object.hasOwn(result.relation_candidates[0], 'canonical_id'), false);
    assert.equal(Object.hasOwn(result, 'plan'), false);
    assert.equal(Object.hasOwn(result, 'commit'), false);
    assert.deepEqual(questions, before);
});

test('suggestion application normalizes domain context before calling Detect', async () => {
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
    const useCase = createSuggestCanonicalRelationsUseCase({
        taxonomy,
        detectEntityQuestionClusters: detector,
    });

    await useCase({
        mode: 'entity',
        seed: 'Redis',
        questions: [
            question({ question_id: 'q_a' }),
            question({ question_id: 'q_b', source_note_id: 'note-b' }),
        ],
    });

    assert.equal(detectorInput[0].domain_key, '缓存/Redis');
    assert.equal(detectorInput[1].domain_key, '缓存/Redis');
});

test('suggestion application rejects unsupported modes and invalid limits', async () => {
    const useCase = createSuggestCanonicalRelationsUseCase({ taxonomy });

    await assert.rejects(
        useCase({ mode: 'hotspot', seed: 'hotspot', questions: [] }),
        /Unsupported dedup suggestion mode/,
    );
    await assert.rejects(
        useCase({ mode: 'entity', seed: 'Redis', questions: [], limit: -1 }),
        /Invalid suggestion limit/,
    );
});

test('suggestion application preserves empty detection as an explicit empty review queue', async () => {
    const useCase = createSuggestCanonicalRelationsUseCase({ taxonomy });
    const result = await useCase({
        mode: 'entity',
        seed: 'Redis',
        questions: [question()],
    });

    assert.equal(result.detection_count, 0);
    assert.equal(result.candidate_count, 0);
    assert.deepEqual(result.relation_candidates, []);
});
