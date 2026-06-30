'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl, readJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { runSuggest, runAccept, runStats } = require('../scripts/commands/canonical');

function makeQuestion(original, noteId, index, company) {
    return {
        question_id: computeQuestionId(original),
        original_question: original,
        source_note_id: noteId,
        source_question_index: index,
        company,
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2024',
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
    };
}

test('suggests and accepts canonical hotspot candidates idempotently', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const indexDir = path.join(root, 'data', 'indexes');
    const questions = [
        makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'),
        makeQuestion('Redis 为什么快？', 'note-b', 0, '字节'),
        makeQuestion('MySQL 索引为什么用 B+ 树？', 'note-c', 0, '百度'),
    ];
    writeJsonl(questionsPath, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), indexDir);

    const manifest = runSuggest({ root, hotspot: true, limit: 10 });
    assert.equal(manifest.candidate_count, 1);
    const candidate = manifest.candidates[0];
    const accepted = runAccept({
        root,
        'candidate-id': candidate.candidate_id,
        'canonical-id': candidate.canonical_id_suggestion,
    });
    assert.equal(accepted.ok, true);
    assert.equal(accepted.updated_question_rows, 2);

    const acceptedAgain = runAccept({
        root,
        'candidate-id': candidate.candidate_id,
        'canonical-id': candidate.canonical_id_suggestion,
    });
    assert.equal(acceptedAgain.ok, true);
    assert.equal(readJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl')).length, 1);
    assert.equal(readJsonl(questionsPath).filter((question) => question.canonical_id).length, 2);
    assert.equal(runStats({ root }).canonical_count, 1);
    assert.equal(runSuggest({ root, hotspot: true, limit: 10 }).candidate_count, 0);

    fs.rmSync(root, { recursive: true, force: true });
});

test('suggests entity candidates by normalized entity and question overlap', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-entity-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const indexDir = path.join(root, 'data', 'indexes');
    const questions = [
        makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'),
        makeQuestion('Redis 为什么这么快？', 'note-b', 0, '字节'),
        makeQuestion('Redis 持久化机制是什么？', 'note-c', 0, '阿里'),
    ];
    writeJsonl(questionsPath, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), indexDir);

    const manifest = runSuggest({ root, entity: 'redis', limit: 5 });
    assert.equal(manifest.mode, 'entity');
    assert.equal(manifest.candidate_count, 1);
    assert.equal(manifest.candidates[0].question_ids.length, 2);
    assert.deepEqual(
        manifest.candidates[0].aliases,
        ['Redis 为什么快？', 'Redis 为什么这么快？'],
    );

    fs.rmSync(root, { recursive: true, force: true });
});
