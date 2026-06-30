'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJson } = require('../scripts/lib/io');
const { runStatus } = require('../scripts/commands/migrate');

test('migration status reports applied and missing outputs from registry', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-migrate-status-'));
    writeJson(path.join(root, 'config', 'migrations.json'), {
        schema_version: 'migrations.v1',
        migrations: [{
            id: '001_build_questions',
            description: 'Build questions',
            outputs: [
                'data/questions/questions.jsonl',
                'data/questions/question_sources.jsonl',
            ],
        }],
    });
    ensureDir(path.join(root, 'data', 'questions'));
    fs.writeFileSync(path.join(root, 'data', 'questions', 'questions.jsonl'), '', 'utf8');

    const missing = runStatus({ root });
    assert.equal(missing.ok, true);
    assert.equal(missing.migrations[0].applied, false);
    assert.deepEqual(missing.migrations[0].missing_outputs, ['data/questions/question_sources.jsonl']);

    fs.writeFileSync(path.join(root, 'data', 'questions', 'question_sources.jsonl'), '', 'utf8');
    const applied = runStatus({ root });
    assert.equal(applied.migrations[0].applied, true);
    assert.deepEqual(applied.migrations[0].missing_outputs, []);

    fs.rmSync(root, { recursive: true, force: true });
});
