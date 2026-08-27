'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJson, writeJsonl } = require('../scripts/lib/io');
const { extractCodeBlocks, runAnswerAudit } = require('../scripts/lib/answer_quality');
const QUALITY = require('../config/answer_quality.json');

function fixtureRoot() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-javascript-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        schema_version: 'canonical_question.v1', canonical_id: 'cq_js', canonical_title: 'JavaScript 数组求和', aliases: [],
        question_ids: ['q_js'], primary_domain: { l1: '前端', l2: 'JavaScript基础' }, primary_entities: ['javascript'],
        companies: [], frequency: 1, review_priority: 'P3', answer_status: 'needs_update',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{
        schema_version: 'question.v1', question_id: 'q_js', canonical_id: 'cq_js', original_question: '手写 JavaScript 数组求和函数',
        question_type: '算法手撕_Coding', is_valid_for_library: true,
    }]);
    return root;
}

function candidate(code) {
    return [
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_js","version":1,"status":"draft","updated_at":"2026-08-27","answer_type":"coding","quality_tier":"candidate"} -->',
        '# JavaScript 数组求和', '',
        '## 核心结论', '', 'JavaScript 数组求和可以用一次线性遍历完成。', '',
        '## 1 分钟版', '', '遍历数组并累加元素，时间复杂度 O(n)，额外空间 O(1)。', '',
        '## 3 分钟版', '', '```javascript', code, '```', '',
        '## 关键细节', '', '空数组返回 0；这里把输入限定为有限数值数组。', '',
        '## 原理机制', '', '累加器在每一步保存已经遍历前缀的和。', '',
        '## 项目经验版', '', '来源没有真实项目经历，因此不虚构项目数据。', '',
        '## 常见追问', '',
        '- 问：空数组怎么办？答：按当前契约返回 0。',
        '- 问：复杂度是多少？答：时间 O(n)，空间 O(1)。',
        '- 问：遇到非数字怎么办？答：当前契约不接受非数字，需要业务另行定义。', '',
        '## 易错点', '', '不要在题目未定义时擅自做字符串到数字的隐式转换。', '',
    ].join('\n');
}

test('JavaScript coding candidates are discovered by require-code and syntax checked', () => {
    const root = fixtureRoot();
    const dir = path.join(root, 'review', 'candidates', 'answers');
    ensureDir(dir);
    const file = path.join(dir, 'cq_js.md');
    const validCode = 'export function sum(values) {\n  let total = 0;\n  for (const value of values) total += value;\n  return total;\n}';
    fs.writeFileSync(file, candidate(validCode), 'utf8');
    assert.deepEqual(extractCodeBlocks(fs.readFileSync(file, 'utf8')).map((block) => block.language), ['javascript']);
    const valid = runAnswerAudit({ root, candidate: file, noWrite: true, 'require-code': true });
    assert.equal(valid.candidate_count, 1);
    assert.equal(valid.rows[0].errors.some((row) => row.error === 'coding_block_required'), false);
    assert.equal(valid.rows[0].errors.some((row) => row.error === 'javascript_validation_failed'), false);

    fs.writeFileSync(file, candidate('export function broken( {'), 'utf8');
    const invalid = runAnswerAudit({ root, candidate: file, noWrite: true, 'require-code': true });
    assert.equal(invalid.candidate_count, 1);
    assert.equal(invalid.rows[0].errors.some((row) => row.error === 'javascript_validation_failed'), true);
    fs.rmSync(root, { recursive: true, force: true });
});
