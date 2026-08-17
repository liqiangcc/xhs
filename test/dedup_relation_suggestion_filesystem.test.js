'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJsonl, readJson, writeJson } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { createApplication } = require('../src/bootstrap/create-application');
const {
    createFsDedupSuggestionRepositories,
} = require('../src/infrastructure/filesystem/dedup-suggestion-repositories');
const { createDedupFsPaths } = require('../src/infrastructure/filesystem/dedup-paths');

function question(overrides = {}) {
    return {
        question_id: 'q_default',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2026',
        date: '未知',
        domain: { l1: '缓存', l2: 'Redis' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: ['Redis'],
        business_context: [],
        is_valid_for_library: true,
        canonical_id: null,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
        ...overrides,
    };
}

function makeRoot(prefix) {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeFixture(root, questions) {
    const paths = createDedupFsPaths(root);
    writeJsonl(paths.questions, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), path.dirname(paths.entityIndex));
    return paths;
}

test('production composition root persists dedup relation suggestions in a separate filesystem review queue', async () => {
    const root = makeRoot('xhs-dedup-fs-');
    try {
        const questions = [
            question({
                question_id: 'q_redis_a',
                source_note_id: 'note-a',
                original_question: 'Redis 为什么快？',
            }),
            question({
                question_id: 'q_redis_b',
                source_note_id: 'note-b',
                company: '字节',
                original_question: 'Redis 为什么这么快？',
            }),
            question({
                question_id: 'q_mysql',
                source_note_id: 'note-c',
                company: '阿里',
                original_question: 'MySQL 索引为什么用 B+ 树？',
                domain: { l1: '数据库', l2: 'MySQL' },
                tech_entities: ['MySQL'],
            }),
        ];
        const paths = writeFixture(root, questions);
        const app = createApplication({ root });

        const result = await app.dedup.suggest({
            mode: 'entity',
            seed: 'redis',
            limit: 10,
        });

        assert.equal(result.mode, 'entity');
        assert.equal(result.seed, 'Redis');
        assert.equal(result.detection_count, 1);
        assert.equal(result.candidate_count, 1);
        assert.deepEqual(result.relation_candidates[0].question_ids, ['q_redis_a', 'q_redis_b']);
        assert.equal(result.relation_candidates[0].review_state, 'pending');
        assert.equal(Object.hasOwn(result.relation_candidates[0], 'relation'), false);
        assert.equal(Object.hasOwn(result.relation_candidates[0], 'canonical_id'), false);
        assert.equal(result.source_revisions[0].resource, 'dedup-entity-index:Redis');
        assert.match(result.source_revisions[1].resource, /^dedup-questions-by-refs:/);
        assert.equal(result.queue.resource, 'dedup-relation-queue:entity:Redis');
        assert.equal(result.queue.candidate_count, 1);

        const manifest = readJson(paths.relationCandidateQueues);
        assert.equal(manifest.schema_version, 'dedup_relation_candidate_queues.v1');
        const queue = manifest.queues['entity|Redis'];
        assert.equal(queue.schema_version, 'dedup_relation_candidate_queue.v1');
        assert.equal(queue.candidate_count, 1);
        assert.deepEqual(queue.source_revisions, result.source_revisions);
        assert.equal(queue.relation_candidates[0].relation_candidate_key, 'entity|Redis|q_redis_a,q_redis_b');

        const executableCandidateManifest = path.join(
            root,
            'data',
            'manifests',
            'canonical',
            'canonical_candidates.json',
        );
        assert.equal(fs.existsSync(executableCandidateManifest), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('filesystem dedup revisions are scoped to the data used by the suggestion', async () => {
    const root = makeRoot('xhs-dedup-fs-revisions-');
    try {
        const q1 = question({ question_id: 'q_redis_a', source_note_id: 'note-a' });
        const q2 = question({
            question_id: 'q_redis_b',
            source_note_id: 'note-b',
            original_question: 'Redis 为什么这么快？',
        });
        const q3 = question({
            question_id: 'q_kafka',
            source_note_id: 'note-c',
            original_question: 'Kafka 为什么快？',
            domain: { l1: '中间件', l2: 'Kafka' },
            tech_entities: ['Kafka'],
        });
        const paths = writeFixture(root, [q1, q2, q3]);
        const { indexRepository, questionRepository } = createFsDedupSuggestionRepositories({ root });

        const redisIndexBefore = await indexRepository.findEntityRefs('Redis');
        const questionsBefore = await questionRepository.findByRefs(redisIndexBefore.refs);

        const entityIndex = readJson(paths.entityIndex);
        entityIndex.entries.Kafka.question_ids.push('q_unrelated');
        writeJson(paths.entityIndex, entityIndex);
        const redisIndexAfterUnrelatedChange = await indexRepository.findEntityRefs('Redis');
        assert.equal(redisIndexAfterUnrelatedChange.revision, redisIndexBefore.revision);

        const unrelated = question({
            question_id: 'q_mysql',
            source_note_id: 'note-d',
            original_question: 'MySQL MVCC 是什么？',
            domain: { l1: '数据库', l2: 'MySQL' },
            tech_entities: ['MySQL'],
        });
        writeJsonl(paths.questions, [q1, q2, q3, unrelated]);
        const questionsAfterUnrelatedChange = await questionRepository.findByRefs(redisIndexBefore.refs);
        assert.equal(questionsAfterUnrelatedChange.revision, questionsBefore.revision);

        writeJsonl(paths.questions, [
            q1,
            { ...q2, original_question: 'Redis 为什么会这么快？' },
            q3,
            unrelated,
        ]);
        const questionsAfterRelevantChange = await questionRepository.findByRefs(redisIndexBefore.refs);
        assert.notEqual(questionsAfterRelevantChange.revision, questionsBefore.revision);

        const relevantIndex = readJson(paths.entityIndex);
        relevantIndex.entries.Redis.refs = relevantIndex.entries.Redis.refs.filter(
            (ref) => ref.question_id !== 'q_redis_b',
        );
        writeJson(paths.entityIndex, relevantIndex);
        const redisIndexAfterRelevantChange = await indexRepository.findEntityRefs('Redis');
        assert.notEqual(redisIndexAfterRelevantChange.revision, redisIndexBefore.revision);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
