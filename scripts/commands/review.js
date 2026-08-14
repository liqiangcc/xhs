#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { loadQuestions } = require('../lib/question_store');
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
    addDays,
} = require('../lib/review_store');
const { loadReviewStrategy, rankReviewRows } = require('../lib/review_scheduler');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const { createApplication } = require('../../src/bootstrap/create-application');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
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
    const booleanFlags = new Set(['with-issues', 'followup-answered']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (applyGlobalBooleanOption(options, key)) continue;
            if (booleanFlags.has(key)) options[key] = true;
            else if (key === 'quality-defect' || key === 'hard-failure') options[key] = [...(options[key] || []), args[++index]];
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
        '  prepare --target <name> [--limit <n>] [--priority <P0|P1>] [--status <new|weak|learning|mastered>] [--domain <l1>] [--company <name>] [--topic <text>] [--level <text>] [--days <n>] [--with-issues]',
        '  today [--limit <n>] [--with-issues]',
        '  mark --canonical-id <id> --result <again|hard|good|easy> [--oral-version one_minute] [--followup-answered] [--quality-defect <kind>] [--hard-failure <id>] [--feedback-closed-at <YYYY-MM-DD>] [--notes <text>]',
        '  next [--limit <n>] [--days <n>] [--with-issues]',
        '  weak [--limit <n>] [--with-issues]',
        '  integrity',
        '',
        'Options:',
        '  --noWrite     Do not initialize progress, write plans, or write run manifests for read-only commands',
        '  --noManifest  Do not write the run manifest',
    ].join('\n'));
}

function questionMetadata(records, questions) {
    const byCanonicalId = new Map(records.map((record) => [record.canonical_id, {
        levels: new Set(),
        companies: new Set(record.companies || []),
    }]));
    const canonicalByQuestionId = new Map();
    for (const record of records) {
        for (const questionId of record.question_ids || []) {
            canonicalByQuestionId.set(questionId, record.canonical_id);
        }
    }
    for (const question of questions || []) {
        const canonicalId = question.canonical_id || canonicalByQuestionId.get(question.question_id);
        if (!canonicalId || !byCanonicalId.has(canonicalId)) continue;
        const meta = byCanonicalId.get(canonicalId);
        if (question.level) meta.levels.add(String(question.level));
        if (question.company) meta.companies.add(String(question.company));
    }
    return byCanonicalId;
}

function canonicalRows(records, progress, options = {}) {
    const byProgress = progressMap(progress);
    const metaByCanonicalId = questionMetadata(records, options.questions || []);
    return records.map((record) => {
        const meta = metaByCanonicalId.get(record.canonical_id);
        const row = {
            canonical_id: record.canonical_id,
            canonical_title: record.canonical_title,
            review_priority: record.review_priority,
            answer_status: record.answer_status,
            frequency: record.frequency,
            primary_domain: record.primary_domain,
            primary_entities: record.primary_entities || [],
            companies: [...(meta?.companies || new Set(record.companies || []))].sort((a, b) => a.localeCompare(b, 'zh')),
            levels: [...(meta?.levels || new Set())].sort((a, b) => a.localeCompare(b, 'zh')),
            question_ids: record.question_ids || [],
            progress: byProgress.get(record.canonical_id),
        };
        if (options.issueLinks) row.issue_url = options.issueLinks.get(record.canonical_id)?.issue_url || null;
        return row;
    });
}

function dueRows(records, progress, options = {}) {
    const date = todayString(options);
    return rankReviewRows(
        canonicalRows(records, progress, options).filter((row) => isDue(row.progress, date)),
        options
    );
}

function upcomingRows(records, progress, options = {}) {
    const date = todayString(options);
    const maxDate = addDays(date, Number(options.days || 7));
    return rankReviewRows(
        canonicalRows(records, progress, options).filter((row) => !row.progress.next_review_at || row.progress.next_review_at <= maxDate),
        options
    );
}

function loadReviewState(root, options = {}) {
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const questions = loadQuestions({ filePath: paths.questions });
    let progress = loadProgress({ progressPath: paths.progressPath, date: options.date });
    progress = ensureProgressItems(progress, records, { date: options.date });
    if (!options.noWrite) {
        progress = saveProgress(progress, { progressPath: paths.progressPath, date: options.date });
    }
    const issueLinks = options['with-issues']
        ? issueLinkMap(loadIssueLinks({ filePath: paths.issueLinksPath, date: options.date }))
        : null;
    const strategy = loadReviewStrategy(options);
    return { paths, records, questions, progress, issueLinks, strategy };
}

function runToday(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({
        root,
        ...(options.strategyPath ? { reviewStrategyPath: options.strategyPath } : {}),
    });
    return application.review.today({
        date: defaultDate(options),
        limit: options.limit,
        with_issues: Boolean(options['with-issues']),
        write_progress: !options.noWrite,
    });
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
    const { paths, records, questions, progress, issueLinks, strategy } = loadReviewState(root, options);
    const target = options.target;
    if (!target) throw new Error('Usage: review prepare --target <name>');
    const limit = Number(options.limit || 20);
    const rowOptions = { ...options, issueLinks, questions, strategy };
    let rows = options.days ? upcomingRows(records, progress, rowOptions) : dueRows(records, progress, rowOptions);
    if (options.priority) rows = rows.filter((row) => row.review_priority === options.priority);
    if (options.status) rows = rows.filter((row) => row.progress.status === options.status);
    if (options.domain) rows = rows.filter((row) => row.primary_domain?.l1 === options.domain);
    if (options.company) rows = rows.filter((row) => (row.companies || []).some((company) => company.includes(options.company)));
    if (options.level) rows = rows.filter((row) => (row.levels || []).some((level) => level.includes(options.level)));
    if (options.topic) {
        const topic = String(options.topic).toLowerCase();
        rows = rows.filter((row) =>
            row.canonical_title.toLowerCase().includes(topic)
            || (row.primary_entities || []).some((entity) => String(entity).toLowerCase().includes(topic))
            || row.primary_domain?.l1?.toLowerCase().includes(topic)
            || row.primary_domain?.l2?.toLowerCase().includes(topic)
        );
    }
    rows = rows.slice(0, limit);
    const filePath = path.join(paths.plansDir, `${safeName(target)}.md`);
    const relativePlanPath = path.relative(root, filePath);
    if (!options.noWrite) {
        writePlan(filePath, target, rows, options);
    }
    return {
        schema_version: 'review_prepare_result.v1',
        ok: true,
        dry_run: Boolean(options.noWrite),
        target,
        plan_path: options.noWrite ? null : relativePlanPath,
        item_count: rows.length,
        rows,
    };
}

function runMark(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const canonicalId = options['canonical-id'] || options._[0];
    const result = options.result || options.status;
    if (!canonicalId || !result) throw new Error('Usage: review mark --canonical-id <id> --result <again|hard|good|easy>');
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    if (!records.some((record) => record.canonical_id === canonicalId)) {
        throw new Error(`Canonical not found: ${canonicalId}`);
    }
    const oralVersion = options['oral-version'] || null;
    if (oralVersion && oralVersion !== 'one_minute') throw new Error('oral-version must be one_minute');
    const qualityDefects = [...new Set(options['quality-defect'] || [])].filter(Boolean);
    const hardFailures = [...new Set(options['hard-failure'] || [])].filter(Boolean);
    const feedbackClosedAt = options['feedback-closed-at'] || null;
    if (feedbackClosedAt && !/^\d{4}-\d{2}-\d{2}$/.test(feedbackClosedAt)) throw new Error('feedback-closed-at must use YYYY-MM-DD');
    if (feedbackClosedAt && qualityDefects.length === 0) throw new Error('feedback-closed-at requires at least one quality-defect');
    let progress = loadProgress({ progressPath: paths.progressPath, date: options.date });
    progress = ensureProgressItems(progress, records, { date: options.date });
    const byId = progressMap(progress);
    const updated = applyReviewResult(byId.get(canonicalId), result, options);
    progress.items = progress.items.map((item) => item.canonical_id === canonicalId ? updated : item);
    const event = {
        canonical_id: canonicalId,
        result,
        notes: options.notes || '',
        reviewed_at: todayString(options),
        next_review_at: updated.next_review_at,
        oral_version: oralVersion,
        followup_answered: Boolean(options['followup-answered']),
        quality_defects: qualityDefects,
        hard_failures: hardFailures,
        feedback_closed_at: feedbackClosedAt,
    };
    if (!options.noWrite) progress = saveProgress(progress, { progressPath: paths.progressPath, date: options.date });
    const sessionPath = options.noWrite ? null : appendSessionEvent(event, { reviewDir: paths.reviewDir, date: options.date });
    return {
        schema_version: 'review_mark_result.v1',
        ok: true,
        dry_run: Boolean(options.noWrite),
        canonical_id: canonicalId,
        result,
        progress: updated,
        session_event: event,
        session_path: sessionPath ? path.relative(root, sessionPath) : null,
    };
}

function runWeak(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({
        root,
        ...(options.strategyPath ? { reviewStrategyPath: options.strategyPath } : {}),
    });
    return application.review.weak({
        date: defaultDate(options),
        limit: options.limit,
        with_issues: Boolean(options['with-issues']),
        write_progress: !options.noWrite,
    });
}

function runNext(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({
        root,
        ...(options.strategyPath ? { reviewStrategyPath: options.strategyPath } : {}),
    });
    return application.review.next({
        date: defaultDate(options),
        days: options.days,
        limit: options.limit,
        with_issues: Boolean(options['with-issues']),
        write_progress: !options.noWrite,
    });
}

function runIntegrity(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({ root });
    return application.review.integrity();
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
        else if (command === 'next') result = runNext(options);
        else if (command === 'weak') result = runWeak(options);
        else if (command === 'integrity') result = runIntegrity(options);
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
    runNext,
    runWeak,
    runIntegrity,
    main,
};
