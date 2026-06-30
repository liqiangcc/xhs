#!/usr/bin/env node
'use strict';

const path = require('path');
const { loadQuestions, toQueryRow, refKey, questionRef } = require('../lib/question_store');
const { loadIndexes } = require('../lib/index_store');
const { normalizeEntity } = require('../lib/taxonomy');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    const booleanFlags = new Set(['slim', 'valid', 'filter-valid', 'canonical']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (!arg) continue;
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (booleanFlags.has(key)) {
                options[key] = true;
            } else {
                options[key] = args[++index];
            }
        } else {
            options._.push(arg);
        }
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js query <entity|company|domain|hotspot> [value] [options]',
        '',
        'Examples:',
        '  node scripts/xhs.js query entity Redis --valid',
        '  node scripts/xhs.js query company 美团 --slim',
        '  node scripts/xhs.js query domain --l1 系统设计 --l2 高并发',
        '  node scripts/xhs.js query hotspot --limit 50',
        '',
        'Options:',
        '  --value <value>      Query value for entity/company',
        '  --name <value>       Query value for company',
        '  --l1 <value>         Domain l1',
        '  --l2 <value>         Domain l2',
        '  --valid              Only include is_valid_for_library=true',
        '  --filter-valid       Alias for --valid',
        '  --company <value>    Secondary company filter',
        '  --level <value>      Secondary level filter',
        '  --year <value>       Secondary year filter',
        '  --round <value>      Secondary round filter',
        '  --limit <n>          Limit output rows',
        '  --slim               Output compact rows',
    ].join('\n'));
}

function buildQuestionMap(questions) {
    const map = new Map();
    for (const question of questions) {
        map.set(refKey(questionRef(question)), question);
    }
    return map;
}

function uniqueRefs(refs) {
    const seen = new Set();
    const out = [];
    for (const ref of refs || []) {
        const key = refKey(ref);
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(ref);
    }
    return out;
}

function rowsFromRefs(refs, questionMap) {
    return uniqueRefs(refs)
        .map((ref) => questionMap.get(refKey(ref)))
        .filter(Boolean);
}

function includesText(value, needle) {
    if (!needle) return true;
    return String(value || '').toLowerCase().includes(String(needle).toLowerCase());
}

function applyGlobalFilters(questions, options) {
    return questions.filter((question) => {
        if ((options.valid || options['filter-valid']) && question.is_valid_for_library !== true) return false;
        if (options.company && !includesText(question.company, options.company)) return false;
        if (options.level && !includesText(question.level, options.level)) return false;
        if (options.round && !includesText(question.round, options.round)) return false;
        if (options.year && String(question.year) !== String(options.year)) return false;
        return true;
    });
}

function sortQuestions(questions) {
    return questions.sort((a, b) =>
        a.source_note_id.localeCompare(b.source_note_id, 'zh')
        || (a.source_question_index ?? 0) - (b.source_question_index ?? 0)
        || a.question_id.localeCompare(b.question_id)
    );
}

function formatRows(questions, options) {
    const rows = sortQuestions([...questions]).map(toQueryRow);
    const limited = options.limit ? rows.slice(0, Number(options.limit)) : rows;
    if (options.slim) {
        return limited.map((row) => ({
            question_id: row.question_id,
            original_question: row.original_question,
            source_note_id: row.source_note_id,
            company: row.company,
        }));
    }
    return limited;
}

function queryEntity(indexes, questionMap, value) {
    const normalized = normalizeEntity(value);
    const lower = String(value || '').toLowerCase();
    const matchedRefs = [];
    for (const [key, bucket] of Object.entries(indexes.entity.entries || {})) {
        if (key === normalized || key.toLowerCase().includes(lower)) {
            matchedRefs.push(...bucket.refs);
        }
    }
    return rowsFromRefs(matchedRefs, questionMap);
}

function queryCompany(indexes, questionMap, value) {
    const lower = String(value || '').toLowerCase();
    const matchedRefs = [];
    for (const [key, bucket] of Object.entries(indexes.company.entries || {})) {
        if (key.toLowerCase().includes(lower)) matchedRefs.push(...bucket.refs);
    }
    return rowsFromRefs(matchedRefs, questionMap);
}

function queryDomain(indexes, questionMap, options) {
    const matchedRefs = [];
    const l1 = options.l1 || options._[0];
    const l2 = options.l2;
    if (l1 && l2) {
        const bucket = indexes.domain.l2?.[`${l1}/${l2}`];
        if (bucket) matchedRefs.push(...bucket.refs);
    } else if (l2) {
        for (const [key, bucket] of Object.entries(indexes.domain.l2 || {})) {
            if (key.endsWith(`/${l2}`)) matchedRefs.push(...bucket.refs);
        }
    } else if (l1) {
        const bucket = indexes.domain.l1?.[l1];
        if (bucket) matchedRefs.push(...bucket.refs);
    }
    return rowsFromRefs(matchedRefs, questionMap);
}

function hotspotFromQuestions(questions) {
    const byId = new Map();
    for (const question of questions) {
        if (!byId.has(question.question_id)) {
            byId.set(question.question_id, []);
        }
        byId.get(question.question_id).push(question);
    }
    return [...byId.entries()]
        .filter(([, items]) => items.length >= 2)
        .map(([questionId, items]) => ({
            question_id: questionId,
            original_question: items[0].original_question,
            frequency: items.length,
            companies: [...new Set(items.map((item) => item.company))].sort((a, b) => a.localeCompare(b, 'zh')),
            source_note_ids: [...new Set(items.map((item) => item.source_note_id))].sort((a, b) => a.localeCompare(b, 'zh')),
            domain_l1: items[0].domain?.l1 || '',
            domain_l2: items[0].domain?.l2 || '',
            appearances: sortQuestions([...items]).map((item) => ({
                source_note_id: item.source_note_id,
                source_question_index: item.source_question_index,
                company: item.company,
                round: item.round,
            })),
        }))
        .sort((a, b) =>
            b.frequency - a.frequency
            || b.companies.length - a.companies.length
            || a.question_id.localeCompare(b.question_id)
        );
}

function formatHotspots(hotspots, options) {
    const limited = options.limit ? hotspots.slice(0, Number(options.limit)) : hotspots;
    if (options.slim) {
        return limited.map((item) => ({
            question_id: item.question_id,
            original_question: item.original_question,
            frequency: item.frequency,
        }));
    }
    return limited;
}

function formatIndexedHotspots(entries, options) {
    const filtered = options.canonical
        ? entries.filter((entry) => entry.canonical_id)
        : entries;
    const limited = options.limit ? filtered.slice(0, Number(options.limit)) : filtered;
    if (options.slim) {
        return limited.map((item) => ({
            canonical_id: item.canonical_id || null,
            question_id: item.question_id,
            original_question: item.original_question,
            frequency: item.frequency,
        }));
    }
    return limited.map((item) => ({
        canonical_id: item.canonical_id || null,
        question_id: item.question_id,
        question_ids: item.question_ids || [item.question_id],
        original_question: item.original_question,
        frequency: item.frequency,
        companies: item.companies || [],
        source_note_ids: item.source_note_ids || [],
        domain_l1: item.domain?.l1 || '',
        domain_l2: item.domain?.l2 || '',
        appearances: item.refs || [],
    }));
}

function runQuery(command, options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const questionsPath = options.questions ? path.resolve(options.questions) : path.join(root, 'data', 'questions', 'questions.jsonl');
    const indexDir = options['index-dir'] ? path.resolve(options['index-dir']) : path.join(root, 'data', 'indexes');
    const questions = loadQuestions({ filePath: questionsPath });
    const indexes = loadIndexes(indexDir);
    const questionMap = buildQuestionMap(questions);

    let resultQuestions = [];
    if (command === 'entity') {
        const value = options.value || options._[0];
        if (!value) throw new Error('Usage: query entity <value>');
        resultQuestions = queryEntity(indexes, questionMap, value);
    } else if (command === 'company') {
        const value = options.name || options.value || options._[0];
        if (!value) throw new Error('Usage: query company <value>');
        resultQuestions = queryCompany(indexes, questionMap, value);
    } else if (command === 'domain') {
        if (!options.l1 && !options.l2 && !options._[0]) throw new Error('Usage: query domain --l1 <value> [--l2 <value>]');
        resultQuestions = queryDomain(indexes, questionMap, options);
    } else if (command === 'hotspot') {
        if (options.canonical) {
            return formatIndexedHotspots(indexes.hotspot.entries || [], options);
        }
        const filtered = applyGlobalFilters(questions, options);
        return formatHotspots(hotspotFromQuestions(filtered), options);
    } else {
        throw new Error(`Unknown query command: ${command}`);
    }

    return formatRows(applyGlobalFilters(resultQuestions, options), options);
}

function main(argv = process.argv) {
    const { command, options } = parseArgs(argv);
    if (!command || command === 'help' || options.help) {
        printHelp();
        return 0;
    }

    try {
        const output = runQuery(command, options);
        console.log(JSON.stringify(output, null, 2));
        console.error(`\n共 ${output.length} 条结果`);
        return 0;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    runQuery,
    main,
};
