'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJsonl } = require('../scripts/lib/io');
const {
    createFsQuestionCatalogRepository,
} = require('../src/infrastructure/filesystem/question-catalog-repository');

function makeRoot() {
    return fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-question-catalog-'));
}

test('filesystem Question catalog adapter returns raw rows without stats semantics', () => {
    const root = makeRoot();
    try {
        const filePath = path.join(root, 'data', 'questions', 'questions.jsonl');
        const questions = [
            { question_id: 'q2', canonical_id: null, original_question: 'B' },
            { question_id: 'q1', canonical_id: 'cq_a', original_question: 'A' },
        ];
        writeJsonl(filePath, questions);

        const repository = createFsQuestionCatalogRepository({ root });
        const rows = repository.list();

        assert.deepEqual(rows, questions);
        rows[0].original_question = 'mutated';
        assert.equal(repository.list()[0].original_question, 'B');
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
