#!/usr/bin/env node
'use strict';

const path = require('path');
const { readJson, readJsonl, writeJsonl } = require('../lib/io');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { inferAnswerType } = require('../lib/answer_quality');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPE_ORDER = ['mechanism', 'concept', 'scenario', 'coding', 'project', 'behavior'];

function parseArgs(argv) {
    const options = { noWrite: false };
    for (let index = 2; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--noWrite' || arg === '--check') options.noWrite = true;
        else if (arg === '--root') options.root = path.resolve(argv[++index]);
        else throw new Error(`Unknown option: ${arg}`);
    }
    return options;
}

function buildQueue(options = {}) {
    const root = options.root || ROOT;
    const audit = readJson(path.join(root, 'data', 'manifests', 'quality', 'curated_answer_audit.json'));
    const canonicals = new Map(loadCanonicalQuestions({ filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl') })
        .map((row) => [row.canonical_id, row]));
    const questions = readJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'));
    const questionsByCanonical = new Map();
    for (const question of questions) {
        if (!questionsByCanonical.has(question.canonical_id)) questionsByCanonical.set(question.canonical_id, []);
        questionsByCanonical.get(question.canonical_id).push(question);
    }
    const rows = audit.rows.map((auditRow) => {
        const canonical = canonicals.get(auditRow.canonical_id);
        const answerType = inferAnswerType(questionsByCanonical.get(auditRow.canonical_id) || [], canonical);
        return {
            schema_version: 'curated_answer_audit_queue.v1',
            canonical_id: auditRow.canonical_id,
            canonical_title: canonical?.canonical_title || auditRow.canonical_id,
            answer_type: answerType,
            current_status: auditRow.answer_status,
            current_quality_tier: auditRow.quality_tier,
            audit_ok: auditRow.audit_ok,
            hard_failures: auditRow.hard_failures,
            evidence_path: auditRow.evidence_path,
            review_decision: auditRow.review_decision,
            batch: null,
            disposition: auditRow.audit_ok ? 'verified' : 'needs_evidence_or_rewrite',
        };
    }).sort((a, b) =>
        Number(b.current_quality_tier === 'curated_audit_failed') - Number(a.current_quality_tier === 'curated_audit_failed')
        || TYPE_ORDER.indexOf(a.answer_type) - TYPE_ORDER.indexOf(b.answer_type)
        || a.canonical_id.localeCompare(b.canonical_id)
    ).map((row, index) => ({ ...row, batch: `curated-audit-${String(Math.floor(index / 10) + 1).padStart(3, '0')}` }));
    return { rows, report: { schema_version: 'curated_answer_audit_queue_report.v1', ok: rows.length === audit.curated_population_count, queued_count: rows.length, batch_count: Math.ceil(rows.length / 10), by_type: Object.fromEntries(TYPE_ORDER.map((type) => [type, rows.filter((row) => row.answer_type === type).length])) } };
}

function main(argv = process.argv) {
    try {
        const options = parseArgs(argv);
        const result = buildQueue(options);
        if (!options.noWrite) writeJsonl(path.join(options.root || ROOT, 'data', 'manifests', 'quality', 'curated_answer_audit_queue.jsonl'), result.rows);
        console.log(JSON.stringify(result.report, null, 2));
        return result.report.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) process.exitCode = main(process.argv);

module.exports = { buildQueue, main };
