#!/usr/bin/env node
/**
 * XHS Tagged Note Query Tool
 * Usage: node scripts/query_tagged.js <command> [options]
 *
 * Commands:
 *   domain  --l1 <name>        Filter by domain.l1  (e.g. Java基础)
 *   domain  --l2 <name>        Filter by domain.l2  (e.g. JVM)
 *   company --name <name>      Filter by company     (e.g. 字节跳动)
 *   type    --value <type>     Filter by question_type
 *   depth   --value <depth>    Filter by cognitive_depth
 *   entity  --value <keyword>  Filter by tech_entities (partial match)
 *   stats                      Print count summary across all dimensions
 *   hotspot                    Show questions appearing in 2+ notes (same question_id)
 *   note    --id <note_id>     Show all questions from a specific note
 *
 * Global options:
 *   --slim   Only output question_id + original_question (saves tokens for downstream use)
 */

'use strict';

const fs = require('fs');
const path = require('path');

// ─── Config ────────────────────────────────────────────────────────────────
const TAGGED_DIR = path.resolve(__dirname, '..', 'note_tagged');

// ─── Load all tagged files ──────────────────────────────────────────────────
function loadAllNotes() {
    const files = fs.readdirSync(TAGGED_DIR).filter(f => f.endsWith('.json'));
    const notes = [];
    for (const file of files) {
        try {
            const raw = fs.readFileSync(path.join(TAGGED_DIR, file), 'utf-8');
            notes.push(JSON.parse(raw));
        } catch (_) {
            // skip malformed files
        }
    }
    return notes;
}

// Flatten every note into a list of question records with note-level metadata
function flattenQuestions(notes) {
    const rows = [];
    for (const note of notes) {
        for (const q of (note.tagged_questions || [])) {
            rows.push({
                question_id: q.question_id,
                original_question: q.original_question,
                domain_l1: q.domain?.l1 || '',
                domain_l2: q.domain?.l2 || '',
                question_type: q.question_type || '',
                cognitive_depth: q.cognitive_depth || '',
                tech_entities: q.tech_entities || [],
                business_context: q.business_context || [],
                is_valid_for_library: q.is_valid_for_library,
                // note-level info
                note_id: note.note_id,
                company: note.company || '未知',
                position: note.position || '未知',
                round: note.round || '未注明',
                level: note.level || '未知',
                year: note.year || '未知',
            });
        }
    }
    return rows;
}

// ─── Formatters ────────────────────────────────────────────────────────────
function printTable(rows, slim = false) {
    if (rows.length === 0) { console.log('(无匹配结果)'); return; }
    const output = slim
        ? rows.map(r => ({ question_id: r.question_id, original_question: r.original_question }))
        : rows;
    console.log(JSON.stringify(output, null, 2));
    console.error(`\n共 ${rows.length} 条结果`);  // summary to stderr so JSON stdout stays clean
}

function printStats(rows) {
    const count = (arr, key) =>
        arr.reduce((m, r) => { m[r[key]] = (m[r[key]] || 0) + 1; return m; }, {});

    const section = (title, obj) => {
        console.log(`\n── ${title} ──`);
        const sorted = Object.entries(obj).sort((a, b) => b[1] - a[1]);
        const maxLen = Math.max(...sorted.map(([k]) => k.length), 10);
        for (const [k, v] of sorted) {
            const bar = '█'.repeat(Math.round(v / rows.length * 30));
            console.log(`  ${k.padEnd(maxLen)}  ${String(v).padStart(4)}  ${bar}`);
        }
    };

    section('domain.l1', count(rows, 'domain_l1'));
    section('question_type', count(rows, 'question_type'));
    section('cognitive_depth', count(rows, 'cognitive_depth'));
    section('company (top 15)', (() => {
        const c = count(rows, 'company');
        return Object.fromEntries(Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 15));
    })());
    section('level', count(rows, 'level'));
    section('year', count(rows, 'year'));

    console.log(`\n总题目数: ${rows.length}  |  有效题(is_valid): ${rows.filter(r => r.is_valid_for_library).length}`);
}

function printHotspot(rows, slim = false) {
    // group by question_id
    const byId = {};
    for (const r of rows) {
        if (!byId[r.question_id]) byId[r.question_id] = [];
        byId[r.question_id].push(r);
    }
    const hot = Object.values(byId)
        .filter(arr => arr.length >= 2)
        .sort((a, b) => b.length - a.length);

    if (hot.length === 0) { console.log('(当前数据集中暂无重复出现的题目)'); return; }

    const output = slim
        ? hot.map(arr => ({ question_id: arr[0].question_id, original_question: arr[0].original_question, frequency: arr.length }))
        : hot.map(arr => ({
            question_id: arr[0].question_id,
            original_question: arr[0].original_question,
            frequency: arr.length,
            domain_l1: arr[0].domain_l1,
            domain_l2: arr[0].domain_l2,
            question_type: arr[0].question_type,
            appearances: arr.map(r => ({ company: r.company, note_id: r.note_id, round: r.round })),
        }));
    console.log(JSON.stringify(output, null, 2));
    console.error(`\n共 ${hot.length} 道高频题（出现 ≥2 次）`);
}

// ─── Arg Parsing ───────────────────────────────────────────────────────────
function parseArgs(argv) {
    const args = argv.slice(2);
    const cmd = args[0];
    const opts = {};
    // Collect boolean flags (e.g. --slim) and key-value pairs (e.g. --l1 Java基础)
    const boolFlags = new Set(['slim']);
    for (let i = 1; i < args.length; i++) {
        const key = args[i]?.replace(/^--/, '');
        if (!key) continue;
        if (boolFlags.has(key)) {
            opts[key] = true;
        } else {
            opts[key] = args[i + 1];
            i++; // consume value
        }
    }
    return { cmd, opts };
}

// ─── Main ──────────────────────────────────────────────────────────────────
function main() {
    const { cmd, opts } = parseArgs(process.argv);
    const slim = !!opts.slim;

    if (!cmd || cmd === 'help') {
        console.log([
            'XHS Query Tool',
            '',
            'Usage: node scripts/query_tagged.js <command> [options]',
            '',
            'Commands:',
            '  domain  --l1 <name>       按 domain.l1 筛题  (e.g. Java基础)',
            '  domain  --l2 <name>       按 domain.l2 筛题  (e.g. JVM)',
            '  company --name <name>     按公司筛题         (e.g. 字节跳动)',
            '  type    --value <type>    按 question_type   (e.g. 算法手撕_Coding)',
            '  depth   --value <depth>   按 cognitive_depth (e.g. L3_Diagnostic)',
            '  entity  --value <kw>      按 tech_entities 模糊匹配 (e.g. Redis)',
            '  stats                     各维度统计汇总',
            '  hotspot                   高频题（跨笔记重复出现）',
            '  note    --id <note_id>    指定笔记 ID 的全部题目',
            '  help                      显示此帮助',
            '',
            'Global options:',
            '  --slim   只输出 question_id + original_question（减少 token，适合 Agent 分析）',
        ].join('\n'));
        return;
    }

    const notes = loadAllNotes();
    const rows = flattenQuestions(notes);

    switch (cmd) {
        case 'domain': {
            const key = opts.l1 ? 'domain_l1' : 'domain_l2';
            const val = (opts.l1 || opts.l2 || '').trim();
            if (!val) { console.error('Usage: domain --l1 <name>  OR  domain --l2 <name>'); process.exit(1); }
            printTable(rows.filter(r => r[key] === val), slim);
            break;
        }
        case 'company': {
            const name = (opts.name || '').trim();
            if (!name) { console.error('Usage: company --name <name>'); process.exit(1); }
            // fuzzy: allow partial match (e.g. "字节" matches "字节跳动")
            printTable(rows.filter(r => r.company.includes(name)), slim);
            break;
        }
        case 'type': {
            const val = (opts.value || '').trim();
            if (!val) { console.error('Usage: type --value <question_type>'); process.exit(1); }
            printTable(rows.filter(r => r.question_type === val), slim);
            break;
        }
        case 'depth': {
            const val = (opts.value || '').trim();
            if (!val) { console.error('Usage: depth --value <cognitive_depth>'); process.exit(1); }
            printTable(rows.filter(r => r.cognitive_depth === val), slim);
            break;
        }
        case 'entity': {
            const kw = (opts.value || '').trim().toLowerCase();
            if (!kw) { console.error('Usage: entity --value <keyword>'); process.exit(1); }
            printTable(rows.filter(r =>
                r.tech_entities.some(e => e.toLowerCase().includes(kw))
            ), slim);
            break;
        }
        case 'stats': {
            printStats(rows); // stats always shows full breakdown
            break;
        }
        case 'hotspot': {
            printHotspot(rows, slim);
            break;
        }
        case 'note': {
            const id = (opts.id || '').trim();
            if (!id) { console.error('Usage: note --id <note_id>'); process.exit(1); }
            const matched = rows.filter(r => r.note_id === id);
            if (matched.length === 0) {
                console.error(`未找到 note_id=${id} 的记录，请确认 ID 正确`);
                process.exit(1);
            }
            // Print note-level metadata once, then questions
            const meta = {
                note_id: matched[0].note_id, company: matched[0].company,
                position: matched[0].position, round: matched[0].round,
                level: matched[0].level, year: matched[0].year
            };
            if (!slim) console.error(JSON.stringify(meta, null, 2));
            printTable(matched, slim);
            break;
        }
        default:
            console.error(`未知命令: ${cmd}。运行 node scripts/query_tagged.js help 查看帮助`);
            process.exit(1);
    }
}

main();
