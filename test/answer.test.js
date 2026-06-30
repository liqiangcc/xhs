'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJsonl, readJsonl } = require('../scripts/lib/io');
const { runInit, runInitBatch, runMissing, runStatus, runValidate, runSync } = require('../scripts/commands/answer');

function canonical(canonicalId, status = 'missing') {
    return {
        canonical_id: canonicalId,
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？'],
        question_ids: ['95ffbd750b81df63a427ad0d630a6b1d'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: status,
        schema_version: 'canonical_question.v1',
    };
}

test('initializes validates statuses and syncs answer metadata', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [canonical('cq_redis_fast')]);

    const created = runInit({ root, 'canonical-id': 'cq_redis_fast', date: '2026-06-30' });
    assert.equal(created.created, true);
    assert.equal(runInit({ root, 'canonical-id': 'cq_redis_fast', date: '2026-06-30' }).created, false);
    assert.equal(runValidate({ root }).ok, true);
    assert.equal(runStatus({ root, draft: true }).total_count, 1);

    const synced = runSync({ root });
    assert.equal(synced.ok, true);
    assert.equal(readJsonl(canonicalPath)[0].answer_status, 'draft');

    fs.rmSync(root, { recursive: true, force: true });
});

test('validates malformed answer metadata and refuses sync on invalid files', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-invalid-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const answersDir = path.join(root, 'review', 'answers');
    writeJsonl(canonicalPath, [canonical('cq_redis_fast')]);
    ensureDir(answersDir);
    fs.writeFileSync(
        path.join(answersDir, 'cq_wrong_file.md'),
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_redis_fast","version":1,"status":"draft","updated_at":"2026-06-30"} -->\n# wrong\n',
        'utf8'
    );
    fs.writeFileSync(
        path.join(answersDir, 'cq_unknown.md'),
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_unknown","version":1,"status":"draft","updated_at":"2026-06-30"} -->\n# unknown\n',
        'utf8'
    );
    fs.writeFileSync(
        path.join(answersDir, 'cq_bad_status.md'),
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_bad_status","version":1,"status":"done","updated_at":"2026-06-30"} -->\n# bad\n',
        'utf8'
    );
    fs.writeFileSync(path.join(answersDir, 'cq_missing_meta.md'), '# no metadata\n', 'utf8');

    const validation = runValidate({ root });
    assert.equal(validation.ok, false);
    assert.equal(validation.error_count, 5);
    const errors = validation.errors.map((error) => error.error);
    assert.equal(errors.filter((error) => error === 'unknown_canonical_id').length, 2);
    assert.equal(errors.filter((error) => error === 'invalid_status').length, 1);
    assert.equal(errors.filter((error) => error === 'filename_metadata_mismatch').length, 1);
    assert.equal(errors.filter((error) => error.startsWith('Missing xhs-answer metadata')).length, 1);

    const synced = runSync({ root });
    assert.equal(synced.ok, false);
    assert.equal(synced.synced, false);
    assert.equal(readJsonl(canonicalPath)[0].answer_status, 'missing');

    fs.rmSync(root, { recursive: true, force: true });
});

test('lists missing answers and initializes a priority batch with expanded template', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-batch-'));
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [
        canonical('cq_redis_fast'),
        { ...canonical('cq_hashmap'), review_priority: 'P1' },
    ]);

    const missing = runMissing({ root, priority: 'P0', limit: 10 });
    assert.equal(missing.returned_count, 1);
    assert.equal(missing.rows[0].canonical_id, 'cq_redis_fast');

    const initialized = runInitBatch({ root, priority: 'P0', limit: 10, date: '2026-06-30' });
    assert.equal(initialized.created_count, 1);
    assert.equal(runMissing({ root, priority: 'P0', limit: 10 }).returned_count, 0);

    const answer = fs.readFileSync(path.join(root, 'review', 'answers', 'cq_redis_fast.md'), 'utf8');
    assert.match(answer, /## 1 分钟版/);
    assert.match(answer, /## 3 分钟版/);
    assert.match(answer, /## 原理机制/);
    assert.match(answer, /## 项目经验版/);
    assert.match(answer, /## 易错点/);

    fs.rmSync(root, { recursive: true, force: true });
});
