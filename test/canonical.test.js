'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl, readJsonl, writeJson } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { runSuggest, runStats, runList, runCheck, runMerge, runSplit } = require('../scripts/commands/canonical');
const { runDecide, runApply } = require('../scripts/commands/dedup');
const { runIntegrity } = require('../scripts/commands/review');
const { answerPath } = require('../scripts/lib/answer_store');

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

test('suggests reviews and applies hotspot relations through the Dedup pipeline', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-hotspot-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const candidateManifestPath = path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json');
    const relationQueuePath = path.join(root, 'data', 'manifests', 'dedup', 'relation_candidate_queues.json');
    const indexDir = path.join(root, 'data', 'indexes');
    const questions = [
        makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'),
        makeQuestion('Redis 为什么快？', 'note-b', 0, '字节'),
        makeQuestion('MySQL 索引为什么用 B+ 树？', 'note-c', 0, '百度'),
    ];
    writeJsonl(questionsPath, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), indexDir);

    const suggestions = await runSuggest({ root, hotspot: true, limit: 10 });
    assert.equal(suggestions.schema_version, 'dedup_relation_suggestions.v1');
    assert.equal(suggestions.mode, 'hotspot');
    assert.equal(suggestions.seed, 'hotspot');
    assert.equal(suggestions.candidate_count, 1);
    const candidate = suggestions.relation_candidates[0];
    assert.equal(candidate.scope, 'hotspot');
    assert.deepEqual(candidate.question_ids, [questions[0].question_id]);
    assert.equal(candidate.member_count, 2);
    assert.equal(candidate.evidence[0].signal, 'hotspot_question_id');
    assert.equal(fs.existsSync(relationQueuePath), true);
    assert.equal(fs.existsSync(candidateManifestPath), false);

    await runDecide({
        root,
        'relation-candidate-key': candidate.relation_candidate_key,
        relation: 'same',
        'actor-type': 'human',
        'actor-id': 'hotspot-reviewer',
        rationale: 'same repeated hotspot question',
        'decided-at': '2026-08-14T14:45:00+08:00',
    });
    const applied = await runApply({
        root,
        'relation-candidate-key': candidate.relation_candidate_key,
        'canonical-id': 'cq_redis_hotspot',
        'canonical-title': 'Redis 为什么快？',
    });
    assert.equal(applied.applied, true);
    assert.equal(applied.operation, 'canonicalize');
    assert.equal(applied.updated_question_rows, 2);
    assert.equal(readJsonl(canonicalPath).length, 1);
    assert.equal(readJsonl(questionsPath).filter((question) => question.canonical_id).length, 2);
    assert.equal(runStats({ root }).canonical_count, 1);

    const after = await runSuggest({ root, hotspot: true, limit: 10 });
    assert.equal(after.candidate_count, 0);
    assert.equal(fs.existsSync(candidateManifestPath), false);

    fs.rmSync(root, { recursive: true, force: true });
});

test('delegates entity suggestions to the Dedup Application review queue', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-entity-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const indexDir = path.join(root, 'data', 'indexes');
    const candidateManifestPath = path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json');
    const relationQueuePath = path.join(root, 'data', 'manifests', 'dedup', 'relation_candidate_queues.json');
    const questions = [
        makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'),
        makeQuestion('Redis 为什么这么快？', 'note-b', 0, '字节'),
        makeQuestion('Redis 持久化机制是什么？', 'note-c', 0, '阿里'),
    ];
    writeJsonl(questionsPath, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), indexDir);

    const suggestions = await runSuggest({ root, entity: 'redis', limit: 5 });
    assert.equal(suggestions.schema_version, 'dedup_relation_suggestions.v1');
    assert.equal(suggestions.mode, 'entity');
    assert.equal(suggestions.seed, 'Redis');
    assert.equal(suggestions.candidate_count, 1);
    assert.equal(suggestions.relation_candidates[0].question_ids.length, 2);
    assert.deepEqual(suggestions.relation_candidates[0].allowed_relations, [
        'same', 'alias', 'parent_child', 'followup', 'related', 'unrelated',
    ]);
    assert.equal(fs.existsSync(relationQueuePath), true);
    assert.equal(fs.existsSync(candidateManifestPath), false);

    fs.rmSync(root, { recursive: true, force: true });
});

test('lists checks merges and splits canonical records', async () => {
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
    const merged = await runMerge({ root, target: targetId, source: sourceId, reason: 'same_topic' });
    assert.equal(merged.ok, true);
    assert.equal(readJsonl(canonicalPath).length, 1);
    assert.equal(readJsonl(questionsPath).find((question) => question.question_id === q2.question_id).canonical_id, targetId);

    const split = await runSplit({
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

test('merge migrates review references and archives the redundant formal answer', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-merge-history-'));
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const targetId = 'cq_redis_target';
    const sourceId = 'cq_redis_source';
    const q1 = { ...makeQuestion('Redis 为什么快？', 'note-a', 0, '美团'), canonical_id: targetId };
    const q2 = { ...makeQuestion('Redis 为什么这么快？', 'note-b', 0, '字节'), canonical_id: sourceId };
    writeJsonl(questionsPath, [q1, q2]);
    writeJsonl(canonicalPath, [
        makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
        makeCanonical(sourceId, 'Redis 为什么这么快？', [q2.question_id]),
    ]);
    writeJson(path.join(root, 'review', 'progress.json'), {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-06-30',
        items: [
            { canonical_id: targetId, status: 'learning', level: 2, review_count: 1, last_reviewed_at: '2026-06-29', next_review_at: '2026-07-03', confidence: 0.7, difficulty: 2, mistake_count: 0, updated_at: '2026-06-29' },
            { canonical_id: sourceId, status: 'weak', level: 1, review_count: 2, last_reviewed_at: '2026-06-30', next_review_at: '2026-07-01', confidence: 0.4, difficulty: 5, mistake_count: 1, updated_at: '2026-06-30' },
        ],
    });
    writeJson(path.join(root, 'review', 'sessions', '2026-06-30.json'), {
        schema_version: 'review_session.v1', date: '2026-06-30', events: [{ canonical_id: sourceId, result: 'again' }],
    });
    for (const canonicalId of [targetId, sourceId]) {
        fs.mkdirSync(path.join(root, 'review', 'answers'), { recursive: true });
        fs.writeFileSync(answerPath(canonicalId, { answersDir: path.join(root, 'review', 'answers') }), `<!-- xhs-answer: ${JSON.stringify({ schema_version: 'answer.v1', canonical_id: canonicalId, version: 1, status: 'needs_update', updated_at: '2026-06-30', quality_tier: 'long_tail_baseline' })} -->\n# ${canonicalId}\n`, 'utf8');
    }

    const result = await runMerge({ root, target: targetId, source: sourceId, reason: 'semantic_duplicate', date: '2026-06-30' });
    assert.equal(result.ok, true);
    assert.equal(result.review_migration.migrated_session_event_count, 1);
    assert.equal(fs.existsSync(answerPath(sourceId, { answersDir: path.join(root, 'review', 'answers') })), false);
    assert.equal(fs.existsSync(path.join(root, 'review', 'archive', 'answers', `${sourceId}.md`)), true);
    const progress = readJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'));
    assert.equal(progress.length, 1);
    const migratedProgress = require('../scripts/lib/io').readJson(path.join(root, 'review', 'progress.json')).items;
    assert.equal(migratedProgress.length, 1);
    assert.equal(migratedProgress[0].canonical_id, targetId);
    assert.equal(migratedProgress[0].review_count, 3);
    assert.equal(migratedProgress[0].status, 'weak');
    const event = require('../scripts/lib/io').readJson(path.join(root, 'review', 'sessions', '2026-06-30.json')).events[0];
    assert.equal(event.canonical_id, targetId);
    assert.equal(event.migrated_from_canonical_id, sourceId);
    assert.equal(runIntegrity({ root, noWrite: true }).ok, true);
    const history = require('../scripts/lib/io').readJson(path.join(root, 'data', 'manifests', 'canonical', 'canonical_merge_history.json'));
    assert.equal(history.items[0].source, sourceId);
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
