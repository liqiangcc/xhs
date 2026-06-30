'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl } = require('../scripts/lib/io');
const { main: reportMain } = require('../scripts/commands/report');

function silenceConsole(fn) {
    const originalLog = console.log;
    const originalError = console.error;
    console.log = () => {};
    console.error = () => {};
    try {
        return fn();
    } finally {
        console.log = originalLog;
        console.error = originalError;
    }
}

function writeFixtureWithoutIndexes(root) {
    const questionId = computeQuestionId('Redis为什么快');
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{
        question_id: questionId,
        original_question: 'Redis为什么快',
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
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        canonical_id: 'cq_redis_fast',
        canonical_title: 'Redis为什么快',
        aliases: ['Redis为什么快'],
        question_ids: [questionId],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    }]);
}

test('report quality --noFail preserves report failure but exits successfully', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-report-no-fail-'));
    writeFixtureWithoutIndexes(root);

    const failingCode = silenceConsole(() => reportMain([
        'node',
        'scripts/commands/report.js',
        'quality',
        '--root',
        root,
        '--noWrite',
    ]));
    const noFailCode = silenceConsole(() => reportMain([
        'node',
        'scripts/commands/report.js',
        'quality',
        '--root',
        root,
        '--noWrite',
        '--noFail',
    ]));

    assert.equal(failingCode, 1);
    assert.equal(noFailCode, 0);
});
