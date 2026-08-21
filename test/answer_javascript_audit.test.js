'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJson, writeJsonl } = require('../scripts/lib/io');
const { runAnswerAudit } = require('../scripts/lib/answer_quality');

const QUALITY = require('../config/answer_quality.json');

function fixtureRoot() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-js-audit-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        schema_version: 'canonical_question.v1',
        canonical_id: 'cq_js',
        canonical_title: '手写 Promise.all',
        aliases: [],
        question_ids: ['q-js'],
        primary_domain: { l1: '前端', l2: 'JavaScript' },
        primary_entities: ['Promise.all'],
        companies: [],
        frequency: 1,
        review_priority: 'P2',
        answer_status: 'needs_update',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{
        question_id: 'q-js',
        canonical_id: 'cq_js',
        original_question: '手写 Promise.all',
        question_type: 'Coding',
    }]);
    ensureDir(path.join(root, 'review', 'candidates', 'answers'));
    const candidate = [
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_js","version":1,"status":"draft","updated_at":"2026-08-21","quality_tier":"candidate","answer_type":"coding"} -->',
        '# 手写 Promise.all',
        '',
        '## 核心结论', '', '使用输入索引保存结果，并在所有输入 fulfilled 后完成聚合。',
        '',
        '## 1 分钟版', '', '结果顺序按输入顺序；任一 rejection 会拒绝聚合 Promise。',
        '',
        '## 3 分钟版', '', '遍历时固定索引并累计 remaining，完成时写回固定槽位。',
        '',
        '## 关键细节', '', '空输入、thenable、异常迭代器都需要明确处理。',
        '',
        '## 原理机制', '',
        '```js',
        'function interviewPromiseAll(iterable) {',
        '  return Promise.all(iterable);',
        '}',
        '```',
        '',
        '## 项目经验版', '', '不虚构项目数据，只说明使用边界。',
        '',
        '## 常见追问', '',
        '- 问：为什么顺序稳定？答：按输入索引写结果。',
        '- 问：空数组怎么办？答：完成为空数组。',
        '- 问：失败会取消其它任务吗？答：聚合器本身不提供取消。',
        '',
        '## 易错点', '', '不要按完成顺序 push 结果。',
        '',
    ].join('\n');
    const candidatePath = path.join(root, 'review', 'candidates', 'answers', 'cq_js.md');
    fs.writeFileSync(candidatePath, candidate, 'utf8');
    return { root, candidatePath };
}

test('answer audit recognizes and syntax-checks JavaScript coding fences when require-code is enabled', () => {
    const { root, candidatePath } = fixtureRoot();
    try {
        const report = runAnswerAudit({ root, candidate: candidatePath, noWrite: true, 'require-code': true });
        assert.equal(report.candidate_count, 1);
        assert.equal(report.rows.length, 1);
        assert.equal(report.rows[0].errors.some((row) => row.error === 'coding_block_required'), false);
        assert.equal(report.rows[0].hard_failures.includes('placeholder_implementation'), false);
        assert.equal(report.rows[0].hard_failures.includes('unrunnable_implementation'), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('answer audit reports invalid JavaScript syntax as an unrunnable implementation', () => {
    const { root, candidatePath } = fixtureRoot();
    try {
        const broken = fs.readFileSync(candidatePath, 'utf8').replace('return Promise.all(iterable);', 'return Promise.all(iterable;');
        fs.writeFileSync(candidatePath, broken, 'utf8');
        const report = runAnswerAudit({ root, candidate: candidatePath, noWrite: true, 'require-code': true });
        assert.equal(report.candidate_count, 1);
        assert.equal(report.rows[0].hard_failures.includes('unrunnable_implementation'), true);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
