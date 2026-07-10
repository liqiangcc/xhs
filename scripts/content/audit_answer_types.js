#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { readJsonl, stableStringify, writeJsonl } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = ['concept', 'mechanism', 'scenario', 'coding', 'project', 'behavior'];

function classify(canonical, questions) {
    const title = [canonical.canonical_title, ...(canonical.aliases || []), ...questions.map((row) => row.original_question)].join(' ').toLowerCase();
    const rawTypes = questions.map((row) => row.question_type || '').join('|').toLowerCase();
    let answerType = 'concept';
    let rationale = 'definition_or_comparison_default';
    if (/coding|算法|leetcode|sql|手撕|代码实现|编程题/.test(`${title} ${rawTypes}`)) {
        answerType = 'coding'; rationale = 'requires_runnable_algorithm_or_sql';
    } else if (/behavioral|non_tech|personal|reflection|自我介绍|职业规划|优缺点|冲突|沟通|为什么选择/.test(`${title} ${rawTypes}`)) {
        answerType = 'behavior'; rationale = 'requires_real_star_or_personal_boundary';
    } else if (/project|experience|postmortem|项目|故障复盘|线上排障|我的职责|性能优化经历/.test(`${title} ${rawTypes}`)) {
        answerType = 'project'; rationale = 'requires_real_project_evidence_or_framework';
    } else if (/scenario|architecture|设计|如何实现|如何保证|如何处理|高并发|系统|方案|容量|一致性|选型/.test(`${title} ${rawTypes}`)) {
        answerType = 'scenario'; rationale = 'requires_assumptions_data_flow_and_tradeoffs';
    } else if (/underthehood|lowlevel|原理|机制|流程|底层|生命周期|源码|协议|为什么快|怎么实现/.test(`${title} ${rawTypes}`)) {
        answerType = 'mechanism'; rationale = 'requires_participants_state_flow_and_boundary';
    }
    const secondary = [];
    if (answerType === 'scenario' && /原理|底层|源码/.test(title)) secondary.push('mechanism');
    if (answerType === 'project' && /设计|方案/.test(title)) secondary.push('scenario');
    if (answerType === 'behavior' && /项目|技术/.test(title)) secondary.push('project');
    const sourceTypeSignals = TYPES.filter((type) => ({
        coding: /coding|算法/.test(rawTypes), behavior: /behavioral|non_tech|personal|reflection/.test(rawTypes), project: /project|experience|postmortem/.test(rawTypes), scenario: /scenario|architecture|tooling|integration|analysis/.test(rawTypes), mechanism: /underthehood|lowlevel/.test(rawTypes), concept: !/coding|算法|behavioral|non_tech|personal|reflection|project|experience|postmortem|scenario|architecture|tooling|integration|analysis|underthehood|lowlevel/.test(rawTypes),
    }[type]));
    const flags = [];
    if (sourceTypeSignals.length > 1) flags.push('mixed_source_question_type');
    if (secondary.length) flags.push('secondary_coverage_required');
    if (sourceTypeSignals.length && !sourceTypeSignals.includes(answerType)) flags.push('source_type_overridden');
    return { answer_type: answerType, rationale, secondary_requirements: secondary, source_type_signals: sourceTypeSignals, risk_flags: flags };
}

function buildAudit(options = {}) {
    const root = options.root || ROOT;
    const canonicals = loadCanonicalQuestions({ filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl') });
    const byCanonical = new Map();
    for (const question of readJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'))) {
        if (!byCanonical.has(question.canonical_id)) byCanonical.set(question.canonical_id, []);
        byCanonical.get(question.canonical_id).push(question);
    }
    return canonicals.map((canonical) => ({ schema_version: 'answer_type_audit.v1', canonical_id: canonical.canonical_id, canonical_title: canonical.canonical_title, ...classify(canonical, byCanonical.get(canonical.canonical_id) || []) }))
        .sort((a, b) => a.canonical_id.localeCompare(b.canonical_id));
}

function run(options = {}) {
    const root = options.root || ROOT;
    const output = path.join(root, 'data', 'manifests', 'quality', 'answer_type_audit.jsonl');
    const rows = buildAudit({ root });
    const expected = `${rows.map(stableStringify).join('\n')}\n`;
    const current = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : '';
    if (!options.noWrite && !options.check) writeJsonl(output, rows);
    return { schema_version: 'answer_type_audit_report.v1', ok: !options.check || current === expected, check: Boolean(options.check), canonical_count: rows.length, type_counts: Object.fromEntries(TYPES.map((type) => [type, rows.filter((row) => row.answer_type === type).length])), mixed_count: rows.filter((row) => row.risk_flags.length > 0).length, output: path.relative(root, output) };
}

function main(argv = process.argv) {
    const options = { check: argv.includes('--check'), noWrite: argv.includes('--noWrite') };
    const rootIndex = argv.indexOf('--root'); if (rootIndex >= 0) options.root = path.resolve(argv[rootIndex + 1]);
    const result = run(options); console.log(JSON.stringify(result, null, 2)); return result.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();
module.exports = { classify, buildAudit, run, main };
