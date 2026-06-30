'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJsonl } = require('../scripts/lib/io');
const { runValidate } = require('../scripts/commands/answer');

function canonical(canonicalId, status = 'ready') {
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

function readyAnswer(canonicalId, title = 'Redis 为什么快？') {
    return [
        `<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"${canonicalId}","version":1,"status":"ready","updated_at":"2026-06-30"} -->`,
        `# ${title}`,
        '',
        '## 核心结论',
        '这是核心结论。',
        '',
        '## 1 分钟版',
        '这是 1 分钟回答。',
        '',
        '## 3 分钟版',
        '这是 3 分钟回答。',
        '',
        '## 关键细节',
        '- 关键细节。',
        '',
        '## 原理机制',
        '- 原理机制。',
        '',
        '## 项目经验版',
        '这是项目经验。',
        '',
        '## 常见追问',
        '- 常见追问。',
        '',
        '## 易错点',
        '- 易错点。',
        '',
    ].join('\n');
}

test('strict validation accepts complete ready answers', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-strict-ok-'));
    const answersDir = path.join(root, 'review', 'answers');
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    ensureDir(answersDir);
    fs.writeFileSync(path.join(answersDir, 'cq_redis_fast.md'), readyAnswer('cq_redis_fast'), 'utf8');

    const report = runValidate({ root, strict: true });

    assert.equal(report.ok, true);
    assert.equal(report.strict, true);
    assert.equal(report.error_count, 0);
});

test('strict validation rejects ready placeholders missing sections and stale ready statuses', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-strict-bad-'));
    const answersDir = path.join(root, 'review', 'answers');
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [
        canonical('cq_ready_todo'),
        canonical('cq_ready_missing_section'),
        canonical('cq_ready_no_file'),
        canonical('cq_draft_todo', 'draft'),
    ]);
    ensureDir(answersDir);
    fs.writeFileSync(
        path.join(answersDir, 'cq_ready_todo.md'),
        readyAnswer('cq_ready_todo').replace('这是核心结论。', 'TODO'),
        'utf8'
    );
    fs.writeFileSync(
        path.join(answersDir, 'cq_ready_missing_section.md'),
        readyAnswer('cq_ready_missing_section').replace('## 易错点\n- 易错点。\n', ''),
        'utf8'
    );
    fs.writeFileSync(
        path.join(answersDir, 'cq_draft_todo.md'),
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_draft_todo","version":1,"status":"draft","updated_at":"2026-06-30"} -->\n# draft\n\nTODO\n',
        'utf8'
    );

    const report = runValidate({ root, strict: true });
    const errors = report.errors.map((error) => error.error);

    assert.equal(report.ok, false);
    assert.equal(errors.includes('todo_placeholder'), true);
    assert.equal(errors.includes('missing_section'), true);
    assert.equal(errors.includes('ready_status_without_ready_file'), true);
    assert.equal(errors.includes('invalid_status'), false);
});
