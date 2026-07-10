#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { listAnswerFiles, readAnswerFile } = require('../lib/answer_store');
const { buildAnswerContext, validateSpecializedCandidate } = require('../lib/answer_quality');
const { readJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

function main(argv = process.argv) {
    const rootIndex = argv.indexOf('--root');
    const root = rootIndex >= 0 ? path.resolve(argv[rootIndex + 1]) : ROOT;
    const rows = [];
    for (const filePath of listAnswerFiles({ answersDir: path.join(root, 'review', 'answers') })) {
        const answer = readAnswerFile(filePath);
        if (answer.metadata.status !== 'ready' || answer.metadata.quality_tier !== 'curated' || answer.metadata.answer_type !== 'coding') continue;
        const evidencePath = path.join(root, 'review', 'evidence', `${answer.metadata.canonical_id}.json`);
        const evidence = fs.existsSync(evidencePath) ? readJson(evidencePath) : null;
        const result = validateSpecializedCandidate(answer, evidence, buildAnswerContext({ root, canonicalId: answer.metadata.canonical_id, includeStyleSamples: false }));
        rows.push({ canonical_id: answer.metadata.canonical_id, ok: result.hard_failures.length === 0, errors: result.errors, hard_failures: result.hard_failures });
    }
    const report = { schema_version: 'answer_code_check.v1', ok: rows.every((row) => row.ok), curated_coding_count: rows.length, rows };
    console.log(JSON.stringify(report, null, 2));
    return report.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();

module.exports = { main };
