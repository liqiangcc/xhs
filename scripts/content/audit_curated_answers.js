#!/usr/bin/env node
'use strict';

const path = require('path');
const { listAnswerFiles, readAnswerFile } = require('../lib/answer_store');
const { auditOneCandidate } = require('../lib/answer_quality');
const { writeJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

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

function buildReport(options = {}) {
    const root = options.root || ROOT;
    const answersDir = path.join(root, 'review', 'answers');
    const rows = listAnswerFiles({ answersDir })
        .map((filePath) => ({ filePath, answer: readAnswerFile(filePath) }))
        .filter(({ answer }) => ['curated', 'curated_audit_failed'].includes(answer.metadata.quality_tier))
        .sort((a, b) => a.answer.metadata.canonical_id.localeCompare(b.answer.metadata.canonical_id))
        .map(({ filePath, answer }) => {
            const audit = auditOneCandidate(filePath, { root, allowFormal: true });
            return {
                canonical_id: answer.metadata.canonical_id,
                answer_status: answer.metadata.status,
                quality_tier: answer.metadata.quality_tier,
                answer_version: answer.metadata.version,
                audit_ok: audit.ok,
                total_score: audit.total_score,
                hard_failures: audit.hard_failures,
                errors: audit.errors,
                evidence_path: audit.evidence_path,
                review_decision: audit.errors.find((item) => item.error === 'review_not_passed')?.decision || (audit.ok ? 'pass' : null),
                candidate_sha256: audit.candidate_sha256,
            };
        });
    const failures = rows.filter((row) => !row.audit_ok);
    return {
        schema_version: 'curated_answer_audit.v1',
        ok: rows.length === 100 && failures.length === 0,
        curated_population_count: rows.length,
        passing_count: rows.length - failures.length,
        failing_count: failures.length,
        audited_at: '2026-07-11',
        hard_failure_counts: Object.fromEntries([...new Set(rows.flatMap((row) => row.hard_failures))]
            .sort()
            .map((id) => [id, rows.filter((row) => row.hard_failures.includes(id)).length])),
        rows,
    };
}

function main(argv = process.argv) {
    try {
        const options = parseArgs(argv);
        const report = buildReport(options);
        if (!options.noWrite) writeJson(path.join(options.root || ROOT, 'data', 'manifests', 'quality', 'curated_answer_audit.json'), report);
        console.log(JSON.stringify(report, null, 2));
        return report.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) process.exitCode = main(process.argv);

module.exports = { buildReport, main };
