'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { readJson, writeJson, writeJsonl } = require('../scripts/lib/io');
const { runToday, runMark, runWeak, runPrepare } = require('../scripts/commands/review');

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
