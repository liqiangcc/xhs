'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { readJson, writeJson, writeJsonl } = require('../scripts/lib/io');
const { runToday, runMark, runNext, runWeak, runPrepare, runIntegrity } = require('../scripts/commands/review');
const { applyReviewResult } = require('../scripts/lib/review_store');

function canonical(canonicalId, title) {
    return {
        canonical_id: canonicalId,
        canonical_title: title,
        aliases: [title],
        question_ids: ['95ffbd750b81df63a427ad0d630a6b1d'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 3,
        review_priority: 'P0',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

test('prepares due review items and updates progress from marks', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [
        canonical('cq_redis_fast', 'Redis 为什么快？'),
        canonical('cq_redis_persistence', 'Redis 持久化机制'),
    ]);

    const today = runToday({ root, date: '2026-06-30', limit: 10 });
    assert.equal(today.returned_count, 2);
    assert.equal(Object.hasOwn(today.rows[0], 'issue_url'), false);
    const markedGood = runMark({ root, date: '2026-06-30', 'canonical-id': 'cq_redis_fast', result: 'good' });
    assert.equal(markedGood.progress.level, 1);
    assert.equal(markedGood.progress.next_review_at, '2026-07-01');
    const markedAgain = runMark({ root, date: '2026-06-30', 'canonical-id': 'cq_redis_persistence', result: 'again', notes: 'missed AOF' });
    assert.equal(markedAgain.progress.status, 'weak');
    assert.equal(runWeak({ root, date: '2026-06-30', limit: 10 }).returned_count, 1);

    const prepared = runPrepare({ root, date: '2026-06-30', target: 'redis', limit: 10, priority: 'P0' });
    assert.equal(prepared.ok, true);
    assert.equal(fs.existsSync(path.join(root, prepared.plan_path)), true);

    const weakPlan = runPrepare({ root, date: '2026-06-30', target: 'weak-redis', limit: 10, status: 'weak' });
    assert.equal(weakPlan.item_count, 1);
    assert.equal(weakPlan.rows[0].canonical_id, 'cq_redis_persistence');

    fs.rmSync(root, { recursive: true, force: true });
});

test('applies hard good and easy review intervals deterministically', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-intervals-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [canonical('cq_redis_fast', 'Redis 为什么快？')]);

    const hard = runMark({ root, date: '2026-06-30', 'canonical-id': 'cq_redis_fast', result: 'hard' });
    assert.equal(hard.progress.level, 0);
    assert.equal(hard.progress.next_review_at, '2026-07-01');
    assert.equal(hard.progress.status, 'weak');

    const good = runMark({ root, date: '2026-07-01', 'canonical-id': 'cq_redis_fast', result: 'good' });
    assert.equal(good.progress.level, 1);
    assert.equal(good.progress.next_review_at, '2026-07-02');

    const easy = runMark({ root, date: '2026-07-02', 'canonical-id': 'cq_redis_fast', result: 'easy' });
    assert.equal(easy.progress.level, 3);
    assert.equal(easy.progress.next_review_at, '2026-07-09');

    const session = readJson(path.join(root, 'review', 'sessions', '2026-07-02.json'));
    assert.equal(session.events.length, 1);
    assert.equal(session.events[0].result, 'easy');

    fs.rmSync(root, { recursive: true, force: true });
});

test('records one-minute oral checks, followups and closed quality feedback for stability audits', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-stability-event-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast', 'Redis 为什么快？')]);
    const marked = runMark({
        root, date: '2026-07-11', 'canonical-id': 'cq_redis_fast', result: 'good',
        'oral-version': 'one_minute', 'followup-answered': true,
        'quality-defect': ['too_long'], 'feedback-closed-at': '2026-07-11',
    });
    assert.equal(marked.session_event.oral_version, 'one_minute');
    assert.equal(marked.session_event.followup_answered, true);
    assert.deepEqual(marked.session_event.quality_defects, ['too_long']);
    const session = readJson(path.join(root, 'review', 'sessions', '2026-07-11.json'));
    assert.equal(session.events[0].feedback_closed_at, '2026-07-11');
    fs.rmSync(root, { recursive: true, force: true });
});

test('recovers a weak card through learning to mastered', () => {
    const weak = {
        canonical_id: 'cq_recovery_path',
        status: 'weak',
        level: 1,
        review_count: 2,
        last_reviewed_at: '2026-07-10',
        next_review_at: '2026-07-11',
        confidence: 0.55,
        difficulty: 4,
        mistake_count: 1,
        updated_at: '2026-07-10',
    };
    const learning = applyReviewResult(weak, 'easy', { date: '2026-07-11' });
    assert.equal(learning.status, 'learning');
    assert.equal(learning.level, 3);
    assert.equal(learning.mistake_count, 0);

    const mastered = applyReviewResult(learning, 'easy', { date: '2026-07-18' });
    assert.equal(mastered.status, 'mastered');
    assert.equal(mastered.level, 5);
    assert.equal(mastered.mistake_count, 0);
});

test('adds issue urls to review rows when requested', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-issues-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [canonical('cq_redis_fast', 'Redis 为什么快？')]);
    writeJson(path.join(root, 'review', 'issue_links.json'), {
        schema_version: 'review_issue_links.v1',
        updated_at: '2026-06-30',
        items: [
            {
                canonical_id: 'cq_redis_fast',
                issue_number: 12,
                issue_url: 'https://github.com/liqiangcc/xhs/issues/12',
                answer_status: 'ready',
                synced_at: '2026-06-30',
                body_hash: 'hash-a',
            },
        ],
    });

    const today = runToday({ root, date: '2026-06-30', limit: 10, 'with-issues': true });
    assert.equal(today.rows[0].issue_url, 'https://github.com/liqiangcc/xhs/issues/12');

    const prepared = runPrepare({ root, date: '2026-06-30', target: 'redis', limit: 10, 'with-issues': true });
    const plan = fs.readFileSync(path.join(root, prepared.plan_path), 'utf8');
    assert.match(plan, /\| canonical_id \| priority \| answer \| due \| issue \| title \|/);
    assert.match(plan, /https:\/\/github.com\/liqiangcc\/xhs\/issues\/12/);

    runMark({ root, date: '2026-06-30', 'canonical-id': 'cq_redis_fast', result: 'again' });
    const weak = runWeak({ root, date: '2026-06-30', limit: 10, 'with-issues': true });
    assert.equal(weak.rows[0].issue_url, 'https://github.com/liqiangcc/xhs/issues/12');

    fs.rmSync(root, { recursive: true, force: true });
});

test('supports review next status alias and prepare filters', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-scheduler-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    writeJsonl(canonicalPath, [
        {
            ...canonical('cq_redis_fast', 'Redis 为什么快？'),
            companies: ['字节'],
            primary_entities: ['Redis'],
            question_ids: ['95ffbd750b81df63a427ad0d630a6b1d'],
        },
        {
            ...canonical('cq_mysql_index', 'MySQL 索引'),
            companies: ['美团'],
            primary_domain: { l1: '数据库', l2: 'MySQL' },
            primary_entities: ['MySQL'],
            question_ids: ['c6f19f5588ca19f95c32bd557b6c078a'],
        },
    ]);
    writeJsonl(questionsPath, [
        {
            question_id: '95ffbd750b81df63a427ad0d630a6b1d',
            original_question: 'Redis 为什么快？',
            source_note_id: 'note-a',
            source_question_index: 0,
            company: '字节',
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
            canonical_id: 'cq_redis_fast',
            schema_version: 'question.v1',
            taxonomy_version: 'taxonomy.v1',
        },
        {
            question_id: 'c6f19f5588ca19f95c32bd557b6c078a',
            original_question: 'MySQL 索引',
            source_note_id: 'note-b',
            source_question_index: 0,
            company: '美团',
            position: 'Java后端',
            round: '一面',
            level: '校招',
            year: '2024',
            date: '未知',
            domain: { l1: '数据库', l2: 'MySQL' },
            question_type: '八股文_Concept',
            cognitive_depth: 'L1_Principle',
            tech_entities: ['MySQL'],
            business_context: [],
            is_valid_for_library: true,
            canonical_id: 'cq_mysql_index',
            schema_version: 'question.v1',
            taxonomy_version: 'taxonomy.v1',
        },
    ]);

    const marked = runMark({ root, date: '2026-06-30', 'canonical-id': 'cq_redis_fast', status: 'good' });
    assert.equal(marked.result, 'good');
    const next = runNext({ root, date: '2026-06-30', days: 3, limit: 10 });
    assert.equal(next.returned_count, 2);
    assert.equal(next.rows.every((row) => typeof row.review_score === 'number'), true);

    const prepared = runPrepare({
        root,
        date: '2026-06-30',
        target: 'redis-social',
        days: 3,
        company: '字节',
        topic: 'Redis',
        level: '社招',
        limit: 10,
    });
    assert.equal(prepared.item_count, 1);
    assert.equal(prepared.rows[0].canonical_id, 'cq_redis_fast');

    fs.rmSync(root, { recursive: true, force: true });
});

test('reports duplicate and stale review progress and session references without writing', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-integrity-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [canonical('cq_redis_fast', 'Redis 为什么快？')]);
    writeJson(path.join(root, 'review', 'progress.json'), {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-06-30',
        items: [
            { canonical_id: 'cq_redis_fast' },
            { canonical_id: 'cq_redis_fast' },
            { canonical_id: 'cq_removed' },
            {},
        ],
    });
    writeJson(path.join(root, 'review', 'sessions', '2026-06-30.json'), {
        schema_version: 'review_session.v1',
        date: '2026-06-30',
        events: [{ canonical_id: 'cq_removed' }, {}],
    });

    const result = runIntegrity({ root, noWrite: true });
    assert.equal(result.ok, false);
    assert.deepEqual(result.duplicate_progress_canonical_ids, [{ canonical_id: 'cq_redis_fast', count: 2 }]);
    assert.deepEqual(result.stale_progress_canonical_ids, ['cq_removed']);
    assert.equal(result.malformed_progress_items.length, 1);
    assert.equal(result.stale_session_events.length, 2);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs')), false);

    fs.rmSync(root, { recursive: true, force: true });
});
