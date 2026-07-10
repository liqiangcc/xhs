#!/usr/bin/env node
'use strict';

const path = require('path');
const { normalizeQuestion } = require('../lib/hash');
const { loadQuestions, saveQuestions } = require('../lib/question_store');
const { loadCanonicalQuestions, saveCanonicalQuestions } = require('../lib/canonical_store');
const { buildIndexes, writeIndexes } = require('../lib/index_store');
const { normalizeEntity, validateDomain } = require('../lib/taxonomy');

const ROOT = path.resolve(__dirname, '..', '..');

function parseArgs(argv) {
    const options = {};
    for (let i = 2; i < argv.length; i++) {
        if (argv[i] === '--target-assigned') options.targetAssigned = Number(argv[++i]);
        else if (argv[i] === '--limit') options.limit = Number(argv[++i]);
        else if (argv[i] === '--check') options.check = true;
    }
    return options;
}

function priority(frequency, companies) {
    if (frequency >= 5 || companies.length >= 4) return 'P0';
    if (frequency >= 3) return 'P1';
    return 'P2';
}

function normalizedDomain(row) {
    const checked = validateDomain(row.domain || {});
    return checked.valid ? checked.normalized_domain : { l1: '其他', l2: '其他' };
}

function pickTopDomain(rows) {
    const counts = new Map();
    for (const row of rows) {
        const domain = normalizedDomain(row);
        const key = JSON.stringify(domain);
        counts.set(key, (counts.get(key) || 0) + 1);
    }
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh'))[0];
    return top ? JSON.parse(top[0]) : { l1: '其他', l2: '其他' };
}

function canonicalIdFor(questionId) {
    return `cq_q_${questionId}`;
}

function main() {
    const options = parseArgs(process.argv);
    const questionsPath = path.join(ROOT, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(ROOT, 'data', 'questions', 'canonical_questions.jsonl');
    const indexDir = path.join(ROOT, 'data', 'indexes');
    const questions = loadQuestions({ filePath: questionsPath });
    const canonicals = loadCanonicalQuestions({ filePath: canonicalPath });
    const byNormalizedTitle = new Map();
    for (const record of canonicals) {
        for (const text of [record.canonical_title, ...(record.aliases || [])]) {
            const normalized = normalizeQuestion(text);
            if (normalized && !byNormalizedTitle.has(normalized)) byNormalizedTitle.set(normalized, record);
        }
    }

    const groups = new Map();
    for (const row of questions) {
        if (!row.is_valid_for_library || row.canonical_id) continue;
        if (!groups.has(row.question_id)) groups.set(row.question_id, []);
        groups.get(row.question_id).push(row);
    }
    const ordered = [...groups.entries()].sort((a, b) =>
        b[1].length - a[1].length
        || a[0].localeCompare(b[0])
    );
    const currentAssigned = questions.filter((row) => row.is_valid_for_library && row.canonical_id).length;
    let projectedAssigned = currentAssigned;
    const selected = [];
    for (const group of ordered) {
        if (options.limit && selected.length >= options.limit) break;
        if (options.targetAssigned && projectedAssigned >= options.targetAssigned) break;
        selected.push(group);
        projectedAssigned += group[1].length;
    }

    const assignments = new Map();
    const created = [];
    const attached = [];
    for (const [questionId, rows] of selected) {
        const aliases = [...new Set(rows.map((row) => row.original_question))]
            .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh'));
        const existing = aliases.map((alias) => byNormalizedTitle.get(normalizeQuestion(alias))).find(Boolean);
        if (existing) {
            existing.question_ids = [...new Set([...(existing.question_ids || []), questionId])].sort();
            existing.aliases = [...new Set([...(existing.aliases || []), ...aliases])]
                .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh'));
            attached.push({ question_id: questionId, canonical_id: existing.canonical_id, row_count: rows.length });
            assignments.set(questionId, existing.canonical_id);
            continue;
        }
        const companies = [...new Set(rows.map((row) => row.company || '未知'))].sort((a, b) => a.localeCompare(b, 'zh'));
        const entities = [...new Set(rows.flatMap((row) => row.tech_entities || []).map((entity) => normalizeEntity(entity)).filter(Boolean))]
            .sort((a, b) => a.localeCompare(b, 'zh')).slice(0, 8);
        const canonicalId = canonicalIdFor(questionId);
        const record = {
            canonical_id: canonicalId,
            canonical_title: aliases[0],
            aliases,
            question_ids: [questionId],
            primary_domain: pickTopDomain(rows),
            primary_entities: entities,
            companies,
            frequency: rows.length,
            review_priority: priority(rows.length, companies),
            answer_status: 'missing',
            schema_version: 'canonical_question.v1',
        };
        canonicals.push(record);
        byNormalizedTitle.set(normalizeQuestion(record.canonical_title), record);
        assignments.set(questionId, canonicalId);
        created.push({ canonical_id: canonicalId, question_id: questionId, row_count: rows.length });
    }

    const selectedIds = new Set(selected.map(([questionId]) => questionId));
    const updatedQuestions = questions.map((row) => selectedIds.has(row.question_id)
        ? { ...row, canonical_id: assignments.get(row.question_id) }
        : row);
    const rowsById = new Map();
    for (const row of updatedQuestions) {
        if (!row.canonical_id) continue;
        if (!rowsById.has(row.canonical_id)) rowsById.set(row.canonical_id, []);
        rowsById.get(row.canonical_id).push(row);
    }
    for (const record of canonicals) {
        const rows = rowsById.get(record.canonical_id) || [];
        record.frequency = rows.length;
        record.companies = [...new Set(rows.map((row) => row.company || '未知'))].sort((a, b) => a.localeCompare(b, 'zh'));
        record.review_priority = priority(record.frequency, record.companies);
    }
    const result = {
        ok: true,
        dry_run: Boolean(options.check),
        selected_group_count: selected.length,
        selected_row_count: selected.reduce((sum, [, rows]) => sum + rows.length, 0),
        created_count: created.length,
        attached_count: attached.length,
        canonical_count: canonicals.length,
        assigned_question_rows: projectedAssigned,
        created,
        attached,
    };
    if (!options.check) {
        saveQuestions(updatedQuestions, { filePath: questionsPath });
        saveCanonicalQuestions(canonicals, { filePath: canonicalPath });
        writeIndexes(buildIndexes(updatedQuestions, { canonicalQuestions: canonicals }), indexDir);
    }
    console.log(JSON.stringify(result, null, 2));
}

main();
