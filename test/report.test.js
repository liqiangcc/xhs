'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { buildQualityReport, renderMarkdown, writeReports, main: reportMain } = require('../scripts/commands/report');

function question(original, canonicalId = 'cq_redis_fast') {
    return {
        question_id: computeQuestionId(original),
        original_question: original,
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
        canonical_id: canonicalId,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    };
}

function canonical(questionId) {
    return {
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
    };
}

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

test('quality report summarizes repository health and writes reports', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-report-'));
    const q = question('Redis为什么快');
    const c = canonical(q.question_id);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [q]);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [c]);
    writeIndexes(buildIndexes([q], { canonicalQuestions: [c] }), path.join(root, 'data', 'indexes'));

    const report = buildQualityReport({ root, date: '2026-06-30' });
    assert.equal(report.ok, true);
    assert.equal(report.questions.total_count, 1);
    assert.equal(report.canonical.p0_missing_answer_count, 1);
    assert.equal(report.next_actions[0].action, 'answer missing --priority P0');

    const markdown = renderMarkdown(report);
    assert.match(markdown, /P0 Missing Answers/);
    assert.match(markdown, /cq_redis_fast/);

    const output = writeReports(report, { root });
    assert.equal(fs.existsSync(path.join(root, output.json_report)), true);
    assert.equal(fs.existsSync(path.join(root, output.markdown_report)), true);

    fs.rmSync(root, { recursive: true, force: true });
});

test('report quality --noWrite does not create report files or run manifests', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-report-no-write-'));
    const q = question('Redis为什么快');
    const c = canonical(q.question_id);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [q]);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [c]);
    writeIndexes(buildIndexes([q], { canonicalQuestions: [c] }), path.join(root, 'data', 'indexes'));

    const code = silenceConsole(() => reportMain([
        'node',
        'scripts/commands/report.js',
        'quality',
        '--root',
        root,
        '--noWrite',
    ]));

    assert.equal(code, 0);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'reports', 'quality_report.json')), false);
    assert.equal(fs.existsSync(path.join(root, 'review', 'plans', 'quality_report.md')), false);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs', 'latest_report_quality.json')), false);

    fs.rmSync(root, { recursive: true, force: true });
});
