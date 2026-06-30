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
