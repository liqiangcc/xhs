'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl, readJsonl, writeJson } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { runSuggest, runAccept, runStats, runList, runCheck, runMerge, runSplit } = require('../scripts/commands/canonical');

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

function makeCanonical(canonicalId, title, questionIds) {
    return {
        canonical_id: canonicalId,
        canonical_title: title,
        aliases: [title],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: questionIds.length,
        review_priority: 'P0',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
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

test('lists checks merges and splits canonical records', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-maintain-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const indexDir = path.join(root, 'data', 'indexes');
    const targetId = 'cq_redis_fast_target';
    const sourceId = 'cq_redis_fast_source';
    const splitId = 'cq_redis_single_thread';
    const q1 = { ...makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'), canonical_id: targetId };
    const q2 = { ...makeQuestion('Redis 单线程为什么快？', 'note-b', 0, '字节'), canonical_id: sourceId };
    writeJsonl(questionsPath, [q1, q2]);
    writeJsonl(canonicalPath, [
        makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
        makeCanonical(sourceId, 'Redis 单线程为什么快？', [q2.question_id]),
    ]);
    writeIndexes(buildIndexes([q1, q2], {
        canonicalQuestions: readJsonl(canonicalPath),
    }), indexDir);

    assert.equal(runList({ root, priority: 'P0' }).returned_count, 2);
    assert.equal(runCheck({ root }).ok, true);
    const merged = runMerge({ root, target: targetId, source: sourceId, reason: 'same_topic' });
    assert.equal(merged.ok, true);
    assert.equal(readJsonl(canonicalPath).length, 1);
    assert.equal(readJsonl(questionsPath).find((question) => question.question_id === q2.question_id).canonical_id, targetId);

    const split = runSplit({
        root,
        'canonical-id': targetId,
        'question-id': q2.question_id,
        'new-canonical-id': splitId,
        title: 'Redis 单线程为什么快？',
    });
    assert.equal(split.ok, true);
    assert.equal(readJsonl(canonicalPath).length, 2);
    assert.equal(readJsonl(questionsPath).find((question) => question.question_id === q2.question_id).canonical_id, splitId);
    assert.equal(runCheck({ root }).ok, true);

    fs.rmSync(root, { recursive: true, force: true });
});

test('rejects accepting a candidate whose question is already bound elsewhere', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-conflict-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const manifestPath = path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json');
    const q1 = { ...makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'), canonical_id: 'cq_existing_redis' };
    writeJsonl(questionsPath, [q1]);
    writeJsonl(canonicalPath, [makeCanonical('cq_existing_redis', 'Redis 为什么快？', [q1.question_id])]);
    writeJson(manifestPath, {
        schema_version: 'canonical_candidates.v1',
        candidates: [{
            candidate_id: 'cand_conflict',
            canonical_title: 'Redis 为什么快？',
            aliases: ['Redis 为什么快？'],
            question_ids: [q1.question_id],
            primary_domain: { l1: '缓存', l2: 'Redis' },
            primary_entities: ['Redis'],
            companies: ['美团'],
            frequency: 1,
            review_priority: 'P2',
        }],
    });

    assert.throws(
        () => runAccept({ root, 'candidate-id': 'cand_conflict', 'canonical-id': 'cq_new_redis' }),
        /already belongs to cq_existing_redis/
    );
    assert.equal(readJsonl(questionsPath)[0].canonical_id, 'cq_existing_redis');

    fs.rmSync(root, { recursive: true, force: true });
});

test('canonical check reports duplicates missing rows mismatches orphans and unlisted bindings', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-quality-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const q1 = { ...makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'), canonical_id: 'cq_a' };
    const q2 = { ...makeQuestion('Redis 持久化机制？', 'note-b', 0, '字节'), canonical_id: 'cq_missing_record' };
    const q3 = { ...makeQuestion('Redis 淘汰策略？', 'note-c', 0, '阿里'), canonical_id: 'cq_a' };
    writeJsonl(questionsPath, [q1, q2, q3]);
    writeJsonl(canonicalPath, [
        makeCanonical('cq_a', 'Redis A', [q1.question_id, '00000000000000000000000000000000']),
        makeCanonical('cq_b', 'Redis B', [q1.question_id]),
    ]);

    const report = runCheck({ root });
    assert.equal(report.ok, false);
    assert.equal(report.duplicate_question_id_count, 1);
    assert.equal(report.missing_question_id_count, 1);
    assert.equal(report.binding_mismatch_count, 1);
    assert.equal(report.orphan_binding_count, 1);
    assert.equal(report.unlisted_binding_count, 1);

    fs.rmSync(root, { recursive: true, force: true });
});
