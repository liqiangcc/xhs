#!/usr/bin/env node
'use strict';

const path = require('path');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const { createApplication } = require('../../src/bootstrap/create-application');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

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
        '  --noWrite     Do not persist Review state or write plans/manifests',
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
    const application = createApplication({ root });
    return application.review.mark({
        date: defaultDate(options),
        canonical_id: options['canonical-id'] || options._[0],
        result: options.result || options.status,
        oral_version: options['oral-version'] || null,
        followup_answered: Boolean(options['followup-answered']),
        quality_defects: options['quality-defect'] || [],
        hard_failures: options['hard-failure'] || [],
        feedback_closed_at: options['feedback-closed-at'] || null,
        notes: options.notes || '',
        write_mutation: !options.noWrite,
    });
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
