'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const {
    buildQuestionsFromTagged,
    writeOutputs,
    checkOutputs,
} = require('../scripts/migrate/build_questions_from_tagged');
const { readJsonl, readJson } = require('../scripts/lib/io');
const { main: coverageMain } = require('../scripts/content/check_question_coverage');

function writeTaggedNote(dir, name, data) {
    fs.writeFileSync(path.join(dir, `${name}.json`), `${JSON.stringify(data, null, 2)}\n`, 'utf8');
}

test('builds question main data from tagged notes and reports source drift', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-build-questions-'));
    const taggedDir = path.join(root, 'note_tagged');
    fs.mkdirSync(taggedDir, { recursive: true });

    writeTaggedNote(taggedDir, 'note-a', {
        note_id: 'note-a',
        source: '小红书',
        company: '美团',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: 2024,
        date: '未知',
        tagged_questions: [
            {
                question_id: 'badbadbadbadbadbadbadbadbadbadba',
                original_question: 'Redis 有哪些集群模式？',
                domain: { l1: '缓存', l2: 'Redis' },
                question_type: '八股文_Concept',
                cognitive_depth: 'L1_Principle',
                tech_entities: ['redis'],
                business_context: [],
                is_valid_for_library: true,
            },
            {
                question_id: 'missing-original',
                domain: { l1: '其他', l2: '其他' },
                question_type: '行为软技_Behavioral',
                cognitive_depth: 'N_A',
                tech_entities: [],
                is_valid_for_library: false,
            },
        ],
    });
    writeTaggedNote(taggedDir, 'note-empty', {
        note_id: 'note-empty',
        source: '小红书',
        company: '未知',
        position: '未知',
        round: '未知',
        level: '未知',
        year: '未知',
        date: '未知',
        tagged_questions: [],
    });

    const result = buildQuestionsFromTagged({ root, taggedDir, buildDate: '2026-06-30' });
    assert.equal(result.questions.length, 1);
    assert.equal(result.questionSources.length, 1);
    assert.equal(result.sourceNotes.length, 2);
    assert.equal(result.questions[0].question_id, computeQuestionId('Redis 有哪些集群模式？'));
    assert.equal(result.report.counts.skipped_questions, 1);
    assert.equal(result.report.counts.old_hash_mismatches, 1);
    assert.equal(result.report.counts.empty_notes, 1);

    writeOutputs(root, result);
    assert.equal(checkOutputs(root, result).ok, true);
    assert.equal(readJsonl(path.join(root, 'data', 'questions', 'questions.jsonl')).length, 1);
    assert.equal(readJson(path.join(root, 'data', 'manifests', 'quality', 'build_questions_report.json')).counts.skipped_questions, 1);

    fs.rmSync(root, { recursive: true, force: true });
});

test('validity audit restores complete questions and explains excluded fragments', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-validity-audit-'));
    const taggedDir = path.join(root, 'note_tagged');
    const configDir = path.join(root, 'config');
    fs.mkdirSync(taggedDir, { recursive: true });
    fs.mkdirSync(configDir, { recursive: true });

    writeTaggedNote(taggedDir, 'note-a', {
        note_id: 'note-a',
        company: '示例公司',
        position: 'Java后端',
        tagged_questions: [
            {
                question_id: 'legacy-include',
                original_question: '介绍一次你处理线上故障的完整过程。',
                domain: { l1: '其他', l2: '项目经历' },
                question_type: '行为软技_Behavioral',
                cognitive_depth: 'L3_Experience',
                tech_entities: [],
                business_context: [],
                is_valid_for_library: false,
            },
            {
                question_id: 'legacy-exclude',
                original_question: '算法题一道。',
                domain: { l1: '其他', l2: '其他' },
                question_type: '算法_Coding',
                cognitive_depth: 'N_A',
                tech_entities: [],
                business_context: [],
                is_valid_for_library: true,
            },
        ],
    });
    fs.writeFileSync(path.join(configDir, 'question_validity_audit.json'), `${JSON.stringify({
        schema_version: 'question_validity_audit.v1',
        decisions: [
            {
                source_note_id: 'note-a',
                source_question_index: 0,
                decision: 'include',
                exclusion_reason: null,
                exclusion_note: null,
            },
            {
                source_note_id: 'note-a',
                source_question_index: 1,
                decision: 'exclude',
                exclusion_reason: 'incomplete_or_unreadable',
                exclusion_note: '题干未提供具体算法问题。',
            },
        ],
    }, null, 2)}\n`, 'utf8');

    const result = buildQuestionsFromTagged({ root, taggedDir, buildDate: '2026-06-30' });
    assert.equal(result.questions[0].is_valid_for_library, true);
    assert.equal(result.questions[0].exclusion_reason, null);
    assert.equal(result.questions[1].is_valid_for_library, false);
    assert.equal(result.questions[1].exclusion_reason, 'incomplete_or_unreadable');
    assert.equal(result.report.counts.validity_audit_decisions, 2);
    assert.equal(result.report.counts.unexplained_invalid_questions, 0);

    writeOutputs(root, result);
    const valid = result.questions[0];
    fs.writeFileSync(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), `${JSON.stringify({
        canonical_id: 'cq_audit_example',
        canonical_title: valid.original_question,
        aliases: [valid.original_question],
        question_ids: [valid.question_id],
        primary_domain: valid.domain,
        primary_entities: [],
        companies: [valid.company],
        frequency: 1,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    })}\n`, 'utf8');
    const questions = readJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'));
    questions[0].canonical_id = 'cq_audit_example';
    fs.writeFileSync(path.join(root, 'data', 'questions', 'questions.jsonl'), `${questions.map(JSON.stringify).join('\n')}\n`, 'utf8');

    const originalLog = console.log;
    console.log = () => {};
    let coverageCode;
    try {
        coverageCode = coverageMain(['node', 'check_question_coverage.js', '--root', root, '--check']);
    } finally {
        console.log = originalLog;
    }
    assert.equal(coverageCode, 0);

    fs.rmSync(root, { recursive: true, force: true });
});
