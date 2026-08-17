#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { readJsonl, stablePrettyStringify, writeJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = ['coding', 'concept', 'mechanism', 'scenario', 'project', 'behavior'];

function paths(root) {
    return {
        queue: path.join(root, 'data', 'manifests', 'quality', 'answer_rewrite_queue.jsonl'),
        output: path.join(root, 'data', 'manifests', 'quality', 'answer_pilot_set.json'),
    };
}

function riskRank(row) {
    const risks = new Set(row.risk_flags || []);
    return (risks.has('historical_curated_audit_failed') ? 100 : 0)
        + (risks.has('placeholder_implementation') ? 50 : 0)
        + (risks.has('mixed_source_question_type') ? 30 : 0)
        + (risks.has('secondary_coverage_required') ? 20 : 0)
        + (risks.has('source_type_overridden') ? 10 : 0)
        + (risks.has('personal_fact_verification_required') ? 40 : 0)
        + (risks.has('long_tail_baseline') ? 1 : 0);
}

function selectType(rows, type) {
    const sorted = rows.filter((row) => row.answer_type === type).sort((a, b) =>
        riskRank(b) - riskRank(a) || b.frequency - a.frequency || a.canonical_id.localeCompare(b.canonical_id));
    const hardRisk = sorted.filter((row) => {
        const risks = new Set(row.risk_flags || []);
        return risks.has('historical_curated_audit_failed')
            || risks.has('placeholder_implementation')
            || risks.has('personal_fact_verification_required');
    }).slice(0, 3);
    const selected = new Map(hardRisk.map((row) => [row.canonical_id, {
        ...row,
        selection_reasons: [(row.risk_flags || []).includes('historical_curated_audit_failed')
            ? 'historical_quality_hard_failure'
            : (row.risk_flags || []).includes('placeholder_implementation')
                ? 'known_placeholder_hard_failure'
                : 'personal_evidence_hard_failure_risk'],
    }]));
    for (const row of sorted) {
        if (selected.size >= 10) break;
        if (selected.has(row.canonical_id)) continue;
        const reasons = [];
        if ((row.risk_flags || []).includes('placeholder_implementation')) reasons.push('known_placeholder_risk');
        if ((row.risk_flags || []).includes('long_tail_baseline')) reasons.push('long_tail_baseline');
        if ((row.risk_flags || []).includes('personal_fact_verification_required')) reasons.push('personal_fact_verification');
        if ((row.risk_flags || []).includes('mixed_source_question_type')) reasons.push('mixed_type_risk');
        if ((row.risk_flags || []).includes('secondary_coverage_required')) reasons.push('coverage_risk');
        if (!reasons.length) reasons.push('priority_and_domain_coverage');
        selected.set(row.canonical_id, { ...row, selection_reasons: reasons });
    }
    if (selected.size !== 10 || hardRisk.length < 3) throw new Error(`Cannot choose a 10-question pilot for ${type} with three hard-failure-risk samples`);
    return [...selected.values()].sort((a, b) => a.canonical_id.localeCompare(b.canonical_id));
}

function buildPilot(options = {}) {
    const root = options.root || ROOT;
    const rows = readJsonl(paths(root).queue);
    const items = TYPES.flatMap((type) => selectType(rows, type));
    return {
        schema_version: 'answer_pilot_set.v1',
        source_queue: 'data/manifests/quality/answer_rewrite_queue.jsonl',
        required_human_review_rate: 1,
        canonical_ids: items.map((item) => item.canonical_id),
        items,
        type_counts: Object.fromEntries(TYPES.map((type) => [type, items.filter((item) => item.answer_type === type).length])),
    };
}

function main(argv = process.argv) {
    const rootIndex = argv.indexOf('--root');
    const root = rootIndex >= 0 ? path.resolve(argv[rootIndex + 1]) : ROOT;
    const check = argv.includes('--check');
    const value = buildPilot({ root });
    const output = paths(root).output;
    const expected = stablePrettyStringify(value);
    const actual = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : '';
    const ok = !check || actual === expected;
    if (!check) writeJson(output, value);
    console.log(JSON.stringify({ schema_version: 'answer_pilot_set_report.v1', ok, check, item_count: value.items.length, type_counts: value.type_counts, output: path.relative(root, output) }, null, 2));
    return ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();
module.exports = { buildPilot, main };
