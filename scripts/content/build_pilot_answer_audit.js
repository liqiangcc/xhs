#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { readJson, stablePrettyStringify, writeJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

function outputPaths(root) {
    return {
        pilotSet: path.join(root, 'data', 'manifests', 'quality', 'answer_pilot_set.json'),
        audit: path.join(root, 'data', 'manifests', 'quality', 'pilot_answer_audit.json'),
        candidates: path.join(root, 'review', 'candidates', 'answers'),
        candidateAudits: path.join(root, 'review', 'candidates', 'audits'),
        evidence: path.join(root, 'review', 'evidence'),
    };
}

function readJsonIfExists(filePath) {
    return fs.existsSync(filePath) ? readJson(filePath) : null;
}

function rowProgress(paths, canonicalId) {
    const candidatePath = path.join(paths.candidates, `${canonicalId}.md`);
    const evidence = readJsonIfExists(path.join(paths.evidence, `${canonicalId}.json`));
    const audit = readJsonIfExists(path.join(paths.candidateAudits, `${canonicalId}.json`));
    const auditPassed = audit?.ok === true;
    const independentReviewPassed = evidence?.review?.independent === true && evidence.review.decision === 'pass';
    const humanApproved = evidence?.human_review?.reviewer_type === 'human' && evidence.human_review.decision === 'approved';
    return {
        candidate_status: fs.existsSync(candidatePath) ? 'rendered' : 'pending',
        independent_review_status: independentReviewPassed ? 'passed' : 'pending',
        evidence_status: auditPassed ? 'verified' : (evidence ? 'present' : 'pending'),
        human_review_status: humanApproved ? 'approved' : 'pending',
        promotion_status: humanApproved && auditPassed ? 'ready_to_promote' : (auditPassed ? 'awaiting_human_review' : 'needs_update'),
    };
}

function buildAudit(options = {}) {
    const root = options.root || ROOT;
    const paths = outputPaths(root);
    const pilot = readJson(paths.pilotSet);
    const rows = (pilot.items || []).map((item) => ({
        canonical_id: item.canonical_id,
        answer_type: item.answer_type,
        batch_id: `pilot-${item.answer_type}`,
        risk_flags: item.risk_flags || [],
        selection_reasons: item.selection_reasons || [],
        ...rowProgress(paths, item.canonical_id),
    })).sort((a, b) => a.answer_type.localeCompare(b.answer_type) || a.canonical_id.localeCompare(b.canonical_id));
    const count = (field, value) => rows.filter((row) => row[field] === value).length;
    return {
        schema_version: 'pilot_answer_audit.v1',
        pilot_size: rows.length,
        required_human_review_rate: 1,
        summary: {
            candidate_rendered: count('candidate_status', 'rendered'),
            candidate_pending: count('candidate_status', 'pending'),
            independent_review_passed: count('independent_review_status', 'passed'),
            independent_review_pending: count('independent_review_status', 'pending'),
            evidence_verified: count('evidence_status', 'verified'),
            evidence_pending: count('evidence_status', 'pending'),
            human_review_approved: count('human_review_status', 'approved'),
            human_review_pending: count('human_review_status', 'pending'),
            awaiting_human_review: count('promotion_status', 'awaiting_human_review'),
            promoted_count: count('promotion_status', 'promoted'),
        },
        rows,
    };
}

function main(argv = process.argv) {
    const rootIndex = argv.indexOf('--root');
    const root = rootIndex >= 0 ? path.resolve(argv[rootIndex + 1]) : ROOT;
    const check = argv.includes('--check');
    const paths = outputPaths(root);
    const value = buildAudit({ root });
    const expected = stablePrettyStringify(value);
    const actual = fs.existsSync(paths.audit) ? fs.readFileSync(paths.audit, 'utf8') : '';
    const ok = !check || actual === expected;
    if (!check) writeJson(paths.audit, value);
    console.log(JSON.stringify({ schema_version: 'pilot_answer_audit_report.v1', ok, check, pilot_size: value.pilot_size, output: path.relative(root, paths.audit) }, null, 2));
    return ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();
module.exports = { buildAudit, rowProgress, main };
