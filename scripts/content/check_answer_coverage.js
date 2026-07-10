#!/usr/bin/env node
'use strict';

const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { loadQuestions } = require('../lib/question_store');
const {
    listAnswerFiles,
    readAnswerFile,
    validateAnswerContent,
} = require('../lib/answer_store');
const { writeJson } = require('../lib/io');
const { answerType } = require('./generate_long_tail_answers');

const ROOT = path.resolve(__dirname, '..', '..');

function increment(target, key) {
    target[key || 'unknown'] = (target[key || 'unknown'] || 0) + 1;
}

function main(argv = process.argv) {
    const noWrite = argv.includes('--noWrite') || argv.includes('--check');
    const rootIndex = argv.indexOf('--root');
    const root = rootIndex >= 0 ? path.resolve(argv[rootIndex + 1]) : ROOT;
    const canonicals = loadCanonicalQuestions({
        filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
    });
    const questions = loadQuestions({
        filePath: path.join(root, 'data', 'questions', 'questions.jsonl'),
    });
    const answersDir = path.join(root, 'review', 'answers');
    const byCanonical = new Map();
    for (const question of questions) {
        if (!question.canonical_id) continue;
        if (!byCanonical.has(question.canonical_id)) byCanonical.set(question.canonical_id, []);
        byCanonical.get(question.canonical_id).push(question);
    }

    const answerByCanonical = new Map();
    const duplicateAnswerIds = [];
    const strictErrors = [];
    const statuses = {};
    const qualityTiers = {};
    const answerTypes = {};
    for (const filePath of listAnswerFiles({ answersDir })) {
        const answer = readAnswerFile(filePath);
        const id = answer.metadata.canonical_id;
        if (answerByCanonical.has(id)) duplicateAnswerIds.push(id);
        answerByCanonical.set(id, answer);
        increment(statuses, answer.metadata.status);
        increment(qualityTiers, answer.metadata.quality_tier || 'curated');
        increment(answerTypes, answer.metadata.answer_type || 'curated');
        for (const issue of validateAnswerContent(answer)) {
            strictErrors.push({ canonical_id: id, file: path.relative(root, filePath), ...issue });
        }
    }

    const missing = [];
    const statusMismatches = [];
    const nonReady = [];
    const codingWithoutImplementation = [];
    const personalWithoutTruthBoundary = [];
    for (const canonical of canonicals) {
        const answer = answerByCanonical.get(canonical.canonical_id);
        if (!answer) {
            missing.push(canonical.canonical_id);
            continue;
        }
        if (answer.metadata.status !== 'ready') nonReady.push(canonical.canonical_id);
        if (canonical.answer_status !== answer.metadata.status) {
            statusMismatches.push({
                canonical_id: canonical.canonical_id,
                canonical_status: canonical.answer_status,
                answer_status: answer.metadata.status,
            });
        }
        const type = answerType(byCanonical.get(canonical.canonical_id) || []);
        if (type === 'coding' && !/(~~~|\x60\x60\x60)(java|sql)/i.test(answer.content)) {
            codingWithoutImplementation.push(canonical.canonical_id);
        }
        if ((type === 'project' || type === 'behavior') && !/(真实|不虚构|不得编造|不要虚构|未亲历)/.test(answer.content)) {
            personalWithoutTruthBoundary.push(canonical.canonical_id);
        }
    }

    const canonicalIds = new Set(canonicals.map((canonical) => canonical.canonical_id));
    const orphanAnswers = [...answerByCanonical.keys()].filter((id) => !canonicalIds.has(id));
    const readyCount = canonicals.length - missing.length - nonReady.length;
    const report = {
        schema_version: 'answer_coverage_report.v1',
        ok: missing.length === 0
            && nonReady.length === 0
            && statusMismatches.length === 0
            && orphanAnswers.length === 0
            && duplicateAnswerIds.length === 0
            && strictErrors.length === 0
            && codingWithoutImplementation.length === 0
            && personalWithoutTruthBoundary.length === 0,
        canonical_count: canonicals.length,
        answer_file_count: answerByCanonical.size,
        ready_answer_count: readyCount,
        ready_rate: canonicals.length ? readyCount / canonicals.length : 1,
        statuses,
        quality_tiers: qualityTiers,
        answer_types: answerTypes,
        missing_count: missing.length,
        non_ready_count: nonReady.length,
        status_mismatch_count: statusMismatches.length,
        orphan_answer_count: orphanAnswers.length,
        duplicate_answer_id_count: duplicateAnswerIds.length,
        strict_error_count: strictErrors.length,
        coding_without_implementation_count: codingWithoutImplementation.length,
        personal_without_truth_boundary_count: personalWithoutTruthBoundary.length,
        missing: missing.slice(0, 100),
        non_ready: nonReady.slice(0, 100),
        status_mismatches: statusMismatches.slice(0, 100),
        orphan_answers: orphanAnswers.slice(0, 100),
        strict_errors: strictErrors.slice(0, 100),
        coding_without_implementation: codingWithoutImplementation.slice(0, 100),
        personal_without_truth_boundary: personalWithoutTruthBoundary.slice(0, 100),
    };
    if (!noWrite) {
        writeJson(path.join(root, 'data', 'manifests', 'quality', 'answer_coverage_report.json'), report);
    }
    console.log(JSON.stringify(report, null, 2));
    return report.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();

module.exports = { main };
