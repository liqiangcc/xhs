'use strict';

const path = require('path');
const { spawnSync } = require('child_process');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

test('curated answer specs render without drift', () => {
    const result = spawnSync(process.execPath, [
        'scripts/content/render_answer_specs.js',
        '--spec',
        'review/answer_specs/c5_core_topics.json',
        '--check',
        '--date',
        '2026-07-10',
    ], { cwd: ROOT, encoding: 'utf8' });
    assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
    const report = JSON.parse(result.stdout);
    assert.equal(report.answer_count, 40);
    assert.deepEqual(report.changed_files, []);
});
