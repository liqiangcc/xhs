'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl, writeJson } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { main: validateMain } = require('../scripts/commands/validate');
const { main: canonicalMain } = require('../scripts/commands/canonical');
const { main: reviewMain } = require('../scripts/commands/review');
const { main: answerMain } = require('../scripts/commands/answer');
const { main: buildIndexMain } = require('../scripts/build_index');
const {
    buildQuestionsFromTagged,
    writeOutputs,
    main: buildQuestionsMain,
} = require('../scripts/migrate/build_questions_from_tagged');

const REPO_ROOT = path.resolve(__dirname, '..');

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

function copySchemas(root) {
    const schemaDir = path.join(root, 'schemas');
    fs.mkdirSync(schemaDir, { recursive: true });
    for (const file of ['question.schema.json', 'canonical_question.schema.json', 'review_progress.schema.json']) {
        fs.copyFileSync(path.join(REPO_ROOT, 'schemas', file), path.join(schemaDir, file));
    }
}

function makeQuestion(original = 'Redis 为什么快？') {
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
        canonical_id: 'cq_redis_fast',
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    };
}

function makeCanonical(questionId) {
    return {
        canonical_id: 'cq_redis_fast',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？'],
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

function writeQuestionData(root, options = {}) {
    const question = makeQuestion(options.original);
    const canonical = makeCanonical(question.question_id);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [question]);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical]);
    return { question, canonical };
}

test('validate all --noWrite does not write reports or manifests', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-no-write-validate-'));
    copySchemas(root);
    writeQuestionData(root);

    const code = silenceConsole(() => validateMain([
        'node',
        'scripts/commands/validate.js',
        'all',
        '--root',
        root,
        '--taxonomy',
        path.join(REPO_ROOT, 'config', 'taxonomy.json'),
        '--noWrite',
    ]));

    assert.equal(code, 0);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'quality')), false);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs', 'latest_validate_all.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('canonical check --noWrite does not write quality reports or manifests', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-no-write-canonical-'));
    writeQuestionData(root);

    const code = silenceConsole(() => canonicalMain([
        'node',
        'scripts/commands/canonical.js',
        'check',
        '--root',
        root,
        '--noWrite',
    ]));

    assert.equal(code, 0);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'canonical')), false);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs', 'latest_canonical_check.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('review today and weak --noWrite do not initialize progress or manifests', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-no-write-review-'));
    writeQuestionData(root);

    const todayCode = silenceConsole(() => reviewMain([
        'node',
        'scripts/commands/review.js',
        'today',
        '--root',
        root,
        '--date',
        '2026-06-30',
        '--noWrite',
    ]));
    const weakCode = silenceConsole(() => reviewMain([
        'node',
        'scripts/commands/review.js',
        'weak',
        '--root',
        root,
        '--date',
        '2026-06-30',
        '--noWrite',
    ]));

    assert.equal(todayCode, 0);
    assert.equal(weakCode, 0);
    assert.equal(fs.existsSync(path.join(root, 'review', 'progress.json')), false);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs', 'latest_review_today.json')), false);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs', 'latest_review_weak.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('answer validate and index check --noWrite do not write manifests', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-no-write-read-checks-'));
    const { question } = writeQuestionData(root);
    writeIndexes(buildIndexes([question], { canonicalQuestions: [makeCanonical(question.question_id)] }), path.join(root, 'data', 'indexes'));

    const answerCode = silenceConsole(() => answerMain([
        'node',
        'scripts/commands/answer.js',
        'validate',
        '--root',
        root,
        '--noWrite',
    ]));
    const indexCode = silenceConsole(() => buildIndexMain([
        'node',
        'scripts/build_index.js',
        '--root',
        root,
        '--check',
        '--noWrite',
    ]));

    assert.equal(answerCode, 0);
    assert.equal(indexCode, 0);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('migrate build-questions --check --noWrite does not write manifests', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-no-write-migrate-'));
    const taggedDir = path.join(root, 'note_tagged');
    fs.mkdirSync(taggedDir, { recursive: true });
    writeJson(path.join(taggedDir, 'note-a.json'), {
        note_id: 'note-a',
        source: '小红书',
        company: '字节',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2024',
        date: '未知',
        tagged_questions: [makeQuestion()],
    });
    const result = buildQuestionsFromTagged({ root, taggedDir, buildDate: '2026-06-30' });
    writeOutputs(root, result);

    const code = silenceConsole(() => buildQuestionsMain([
        'node',
        'scripts/migrate/build_questions_from_tagged.js',
        '--root',
        root,
        '--tagged-dir',
        taggedDir,
        '--check',
        '--noWrite',
    ]));

    assert.equal(code, 0);
    assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs')), false);
    fs.rmSync(root, { recursive: true, force: true });
});
