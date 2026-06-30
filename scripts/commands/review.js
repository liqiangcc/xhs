#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { ensureDir } = require('../lib/io');
const { loadIssueLinks, issueLinkMap } = require('../lib/issue_store');
const {
    loadProgress,
    saveProgress,
    ensureProgressItems,
    progressMap,
    isDue,
    applyReviewResult,
    appendSessionEvent,
    todayString,
} = require('../lib/review_store');
const { writeRunManifest } = require('../lib/run_manifest');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        reviewDir: path.join(root, 'review'),
        progressPath: path.join(root, 'review', 'progress.json'),
        plansDir: path.join(root, 'review', 'plans'),
        issueLinksPath: path.join(root, 'review', 'issue_links.json'),
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    const booleanFlags = new Set(['with-issues']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (booleanFlags.has(key)) options[key] = true;
            else options[key] = args[++index];
        } else {
            options._.push(arg);
        }
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js review <prepare|today|mark|weak> [options]',
        '',
        'Commands:',
        '  prepare --target <name> [--limit <n>] [--priority <P0|P1>] [--domain <l1>] [--with-issues]',
        '  today [--limit <n>] [--with-issues]',
        '  mark --canonical-id <id> --result <again|hard|good|easy> [--notes <text>]',
        '  weak [--limit <n>] [--with-issues]',
    ].join('\n'));
}

function priorityRank(priority) {
    return { P0: 0, P1: 1, P2: 2, P3: 3 }[priority] ?? 9;
}

function canonicalRows(records, progress, options = {}) {
    const byProgress = progressMap(progress);
    return records.map((record) => {
        const row = {
            canonical_id: record.canonical_id,
            canonical_title: record.canonical_title,
            review_priority: record.review_priority,
            answer_status: record.answer_status,
            frequency: record.frequency,
            primary_domain: record.primary_domain,
            progress: byProgress.get(record.canonical_id),
        };
        if (options.issueLinks) row.issue_url = options.issueLinks.get(record.canonical_id)?.issue_url || null;
        return row;
    });
}

function dueRows(records, progress, options = {}) {
    const date = todayString(options);
    return canonicalRows(records, progress, options)
        .filter((row) => isDue(row.progress, date))
        .sort((a, b) =>
            priorityRank(a.review_priority) - priorityRank(b.review_priority)
            || (a.progress.next_review_at || '').localeCompare(b.progress.next_review_at || '')
            || b.frequency - a.frequency
            || a.canonical_id.localeCompare(b.canonical_id)
        );
}

function loadReviewState(root, options = {}) {
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    let progress = loadProgress({ progressPath: paths.progressPath, date: options.date });
    progress = ensureProgressItems(progress, records, { date: options.date });
    progress = saveProgress(progress, { progressPath: paths.progressPath, date: options.date });
    const issueLinks = options['with-issues']
        ? issueLinkMap(loadIssueLinks({ filePath: paths.issueLinksPath, date: options.date }))
        : null;
    return { paths, records, progress, issueLinks };
}

function runToday(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const { records, progress, issueLinks } = loadReviewState(root, options);
    const limit = Number(options.limit || 20);
    const rowOptions = { ...options, issueLinks };
    const rows = dueRows(records, progress, rowOptions).slice(0, limit);
    return {
        schema_version: 'review_today.v1',
        date: todayString(options),
        total_due_count: dueRows(records, progress, rowOptions).length,
        returned_count: rows.length,
        rows,
    };
}

function safeName(value) {
    return String(value || 'default')
        .toLowerCase()
        .replace(/[^a-z0-9_\-\u4e00-\u9fa5]+/g, '_')
        .replace(/^_+|_+$/g, '') || 'default';
}

function writePlan(filePath, target, rows, options = {}) {
    ensureDir(path.dirname(filePath));
    const withIssues = Boolean(options['with-issues']);
    const table = withIssues
        ? [
            '| canonical_id | priority | answer | due | issue | title |',
            '|---|---|---|---|---|---|',
            ...rows.map((row) => `| ${row.canonical_id} | ${row.review_priority} | ${row.answer_status} | ${row.progress.next_review_at || ''} | ${row.issue_url || ''} | ${row.canonical_title} |`),
        ]
        : [
            '| canonical_id | priority | answer | due | title |',
            '|---|---|---|---|---|',
            ...rows.map((row) => `| ${row.canonical_id} | ${row.review_priority} | ${row.answer_status} | ${row.progress.next_review_at || ''} | ${row.canonical_title} |`),
        ];
    const lines = [
        `# ${target}`,
        '',
        `Generated: ${todayString(options)}`,
        '',
        ...table,
        '',
    ];
    fs.writeFileSync(filePath, lines.join('\n'), 'utf8');
}

function runPrepare(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const { paths, records, progress, issueLinks } = loadReviewState(root, options);
    const target = options.target;
    if (!target) throw new Error('Usage: review prepare --target <name>');
    const limit = Number(options.limit || 20);
    const rowOptions = { ...options, issueLinks };
    let rows = dueRows(records, progress, rowOptions);
    if (options.priority) rows = rows.filter((row) => row.review_priority === options.priority);
    if (options.domain) rows = rows.filter((row) => row.primary_domain?.l1 === options.domain);
    rows = rows.slice(0, limit);
    const filePath = path.join(paths.plansDir, `${safeName(target)}.md`);
    writePlan(filePath, target, rows, options);
    return {
        schema_version: 'review_prepare_result.v1',
        ok: true,
        target,
        plan_path: path.relative(root, filePath),
        item_count: rows.length,
        rows,
    };
}

function runMark(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const canonicalId = options['canonical-id'] || options._[0];
    const result = options.result;
    if (!canonicalId || !result) throw new Error('Usage: review mark --canonical-id <id> --result <again|hard|good|easy>');
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    if (!records.some((record) => record.canonical_id === canonicalId)) {
        throw new Error(`Canonical not found: ${canonicalId}`);
    }
    let progress = loadProgress({ progressPath: paths.progressPath, date: options.date });
    progress = ensureProgressItems(progress, records, { date: options.date });
    const byId = progressMap(progress);
    const updated = applyReviewResult(byId.get(canonicalId), result, options);
    progress.items = progress.items.map((item) => item.canonical_id === canonicalId ? updated : item);
    progress = saveProgress(progress, { progressPath: paths.progressPath, date: options.date });
    const sessionPath = appendSessionEvent({
        canonical_id: canonicalId,
        result,
        notes: options.notes || '',
        reviewed_at: todayString(options),
        next_review_at: updated.next_review_at,
    }, { reviewDir: paths.reviewDir, date: options.date });
    return {
        schema_version: 'review_mark_result.v1',
        ok: true,
        canonical_id: canonicalId,
        result,
        progress: updated,
        session_path: path.relative(root, sessionPath),
    };
}

function runWeak(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const { records, progress, issueLinks } = loadReviewState(root, options);
    const limit = Number(options.limit || 20);
    const rows = canonicalRows(records, progress, { ...options, issueLinks })
        .filter((row) => row.progress.status === 'weak' || row.progress.mistake_count > 0 || (row.progress.review_count > 0 && row.progress.confidence < 0.5))
        .sort((a, b) =>
            b.progress.mistake_count - a.progress.mistake_count
            || b.progress.difficulty - a.progress.difficulty
            || a.progress.confidence - b.progress.confidence
            || priorityRank(a.review_priority) - priorityRank(b.review_priority)
            || a.canonical_id.localeCompare(b.canonical_id)
        )
        .slice(0, limit);
    return {
        schema_version: 'review_weak.v1',
        returned_count: rows.length,
        rows,
    };
}

function main(argv = process.argv) {
    const { command, options } = parseArgs(argv);
    if (!command || command === 'help' || options.help) {
        printHelp();
        return 0;
    }
    try {
        let result;
        if (command === 'prepare') result = runPrepare(options);
        else if (command === 'today') result = runToday(options);
        else if (command === 'mark') result = runMark(options);
        else if (command === 'weak') result = runWeak(options);
        else throw new Error(`Unknown review command: ${command}`);
        writeRunManifest(options.root ? path.resolve(options.root) : DEFAULT_ROOT, `review_${command}`, result, options);
        console.log(JSON.stringify(result, null, 2));
        return result.ok === false ? 1 : 0;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    runPrepare,
    runToday,
    runMark,
    runWeak,
    main,
};
