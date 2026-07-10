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
        candidate_status: 'pending',
        independent_review_status: 'pending',
        evidence_status: 'pending',
        human_review_status: 'pending',
        promotion_status: 'needs_update',
    })).sort((a, b) => a.answer_type.localeCompare(b.answer_type) || a.canonical_id.localeCompare(b.canonical_id));
    return {
        schema_version: 'pilot_answer_audit.v1',
        pilot_size: rows.length,
        required_human_review_rate: 1,
        summary: {
            candidate_pending: rows.length,
            independent_review_pending: rows.length,
            evidence_pending: rows.length,
            human_review_pending: rows.length,
            promoted_count: 0,
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
module.exports = { buildAudit, main };
