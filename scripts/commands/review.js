#!/usr/bin/env node
'use strict';

const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const {
    loadProgress,
    saveProgress,
    ensureProgressItems,
    progressMap,
    applyReviewResult,
    appendSessionEvent,
    todayString,
} = require('../lib/review_store');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const { createApplication } = require('../../src/bootstrap/create-application');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        reviewDir: path.join(root, 'review'),
        progressPath: path.join(root, 'review', 'progress.json'),
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

function runPrepare(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({
        root,
        ...(options.strategyPath ? { reviewStrategyPath: options.strategyPath } : {}),
    });
    return application.review.prepare({
        date: defaultDate(options),
        target: options.target,
        limit: options.limit,
        priority: options.priority,
        status: options.status,
        domain: options.domain,
        company: options.company,
        level: options.level,
        topic: options.topic,
        days: options.days,
        with_issues: Boolean(options['with-issues']),
        write_progress: !options.noWrite,
        write_plan: !options.noWrite,
    });
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
