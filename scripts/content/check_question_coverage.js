#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadQuestions } = require('../lib/question_store');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { writeJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

function main(argv = process.argv) {
    const noWrite = argv.includes('--noWrite') || argv.includes('--check');
    const rootIndex = argv.indexOf('--root');
    const root = rootIndex >= 0 ? path.resolve(argv[rootIndex + 1]) : ROOT;
    const questions = loadQuestions({
        filePath: path.join(root, 'data', 'questions', 'questions.jsonl'),
    });
    const canonicals = loadCanonicalQuestions({
        filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
    });
    const canonicalIds = new Set(canonicals.map((record) => record.canonical_id));
    const valid = questions.filter((question) => question.is_valid_for_library);
    const invalid = questions.filter((question) => !question.is_valid_for_library);
    const validUnassigned = valid.filter((question) => !question.canonical_id || !canonicalIds.has(question.canonical_id));
    const validWithExclusion = valid.filter((question) => question.exclusion_reason || question.exclusion_note);
    const invalidAssigned = invalid.filter((question) => question.canonical_id);
    const invalidWithoutReason = invalid.filter((question) => !question.exclusion_reason);
    const invalidOtherWithoutNote = invalid.filter((question) => question.exclusion_reason === 'other' && !question.exclusion_note);
    const report = {
        schema_version: 'question_coverage_report.v1',
        ok: validUnassigned.length === 0
            && validWithExclusion.length === 0
            && invalidAssigned.length === 0
            && invalidWithoutReason.length === 0
            && invalidOtherWithoutNote.length === 0,
        question_count: questions.length,
        reviewable_question_count: valid.length,
        excluded_question_count: invalid.length,
        canonical_count: canonicals.length,
        assigned_reviewable_count: valid.length - validUnassigned.length,
        unassigned_reviewable_count: validUnassigned.length,
        unexplained_invalid_count: invalidWithoutReason.length,
        invalid_assigned_count: invalidAssigned.length,
        valid_with_exclusion_count: validWithExclusion.length,
        invalid_other_without_note_count: invalidOtherWithoutNote.length,
        reviewable_assigned_rate: valid.length ? (valid.length - validUnassigned.length) / valid.length : 1,
        invalid_reason_rate: invalid.length ? (invalid.length - invalidWithoutReason.length) / invalid.length : 1,
        unassigned_reviewable: validUnassigned.slice(0, 100),
        unexplained_invalid: invalidWithoutReason.slice(0, 100),
        invalid_assigned: invalidAssigned.slice(0, 100),
        valid_with_exclusion: validWithExclusion.slice(0, 100),
    };
    if (!noWrite) {
        writeJson(path.join(root, 'data', 'manifests', 'quality', 'question_coverage_report.json'), report);
    }
    console.log(JSON.stringify(report, null, 2));
    return report.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();

module.exports = { main };
