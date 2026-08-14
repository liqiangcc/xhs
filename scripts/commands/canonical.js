#!/usr/bin/env node
'use strict';

const path = require('path');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const { createApplication } = require('../../src/bootstrap/create-application');
const { presentCanonicalMergeResult } = require('../../src/interfaces/cli/canonical-merge-presenter');
const { presentCanonicalSplitResult } = require('../../src/interfaces/cli/canonical-split-presenter');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    const booleanFlags = new Set(['hotspot', 'valid']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (!arg) continue;
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (applyGlobalBooleanOption(options, key)) continue;
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
        'Usage: node scripts/xhs.js canonical <suggest|list|check|merge|split|stats> [options]',
        '',
        'Commands:',
        '  suggest --entity <value> [--limit <n>]',
        '  suggest --hotspot [--limit <n>]',
        '  list [--priority <P0|P1|P2|P3>] [--answer-status <status>] [--limit <n>]',
        '  check',
        '  merge --target <canonical_id> --source <canonical_id> --reason <text>',
        '  split --canonical-id <id> --question-id <qid> --new-canonical-id <id> --title <title>',
        '  stats',
        '',
        'Suggestion commands produce Dedup RelationCandidates for explicit review.',
        '',
        'Options:',
        '  --noWrite     Do not write reports or run manifests for read-only commands',
        '  --noManifest  Do not write the run manifest',
    ].join('\n'));
}

function assertCanonicalId(canonicalId) {
    if (!/^cq_[a-z0-9_]+$/.test(canonicalId || '')) {
        throw new Error(`Invalid canonical_id: ${canonicalId}`);
    }
}

function runSuggest(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({ root });
    if (options.hotspot) {
        return application.dedup.suggest({
            mode: 'hotspot',
            limit: Number(options.limit ?? 100),
        });
    }

    const entity = options.entity || options._?.[0];
    if (!entity) throw new Error('Usage: canonical suggest --entity <value>');
    return application.dedup.suggest({
        mode: 'entity',
        seed: entity,
        limit: Number(options.limit ?? 50),
    });
}

function runList(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({ root });
    return application.canonical.list({
        priority: options.priority,
        answer_status: options['answer-status'],
        limit: options.limit,
    });
}

function runCheck(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({ root });
    return application.canonical.check({
        write_report: !options.noWrite,
    });
}

async function runMerge(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const targetId = options.target;
    const sourceId = options.source;
    if (!targetId || !sourceId || !options.reason) {
        throw new Error('Usage: canonical merge --target <canonical_id> --source <canonical_id> --reason <text>');
    }
    assertCanonicalId(targetId);
    assertCanonicalId(sourceId);
    if (targetId === sourceId) throw new Error('target and source must be different');

    const application = createApplication({
        root,
        clock: () => defaultDate(options),
    });
    const result = await application.canonical.merge({
        target: targetId,
        source: sourceId,
        reason: options.reason,
    });
    return presentCanonicalMergeResult(result);
}

async function runSplit(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const canonicalId = options['canonical-id'];
    const questionId = options['question-id'];
    const newCanonicalId = options['new-canonical-id'];
    const title = options.title;
    if (!canonicalId || !questionId || !newCanonicalId || !title) {
        throw new Error('Usage: canonical split --canonical-id <id> --question-id <qid> --new-canonical-id <id> --title <title>');
    }
    assertCanonicalId(canonicalId);
    assertCanonicalId(newCanonicalId);
    if (canonicalId === newCanonicalId) throw new Error('new-canonical-id must differ from canonical-id');

    const application = createApplication({ root });
    const result = await application.canonical.split({
        source: canonicalId,
        question_id: questionId,
        new_canonical_id: newCanonicalId,
        title,
    });
    return presentCanonicalSplitResult(result);
}

function runStats(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const application = createApplication({ root });
    return application.canonical.stats({
        limit: options.limit,
    });
}

function emitCommandResult(command, options, result) {
    writeRunManifest(options.root ? path.resolve(options.root) : DEFAULT_ROOT, `canonical_${command}`, result, options);
    console.log(JSON.stringify(result, null, 2));
    return 0;
}

function handleCommandError(error) {
    console.error(error.message);
    return 1;
}

function main(argv = process.argv) {
    const { command, options } = parseArgs(argv);
    if (!command || command === 'help' || options.help) {
        printHelp();
        return 0;
    }
    try {
        let result;
        if (command === 'suggest') result = runSuggest(options);
        else if (command === 'list') result = runList(options);
        else if (command === 'check') result = runCheck(options);
        else if (command === 'merge') result = runMerge(options);
        else if (command === 'split') result = runSplit(options);
        else if (command === 'stats') result = runStats(options);
        else throw new Error(`Unknown canonical command: ${command}`);

        if (result && typeof result.then === 'function') {
            return result
                .then((resolved) => emitCommandResult(command, options, resolved))
                .catch(handleCommandError);
        }
        return emitCommandResult(command, options, result);
    } catch (error) {
        return handleCommandError(error);
    }
}

if (require.main === module) {
    Promise.resolve(main(process.argv))
        .then((exitCode) => {
            process.exitCode = exitCode;
        })
        .catch((error) => {
            console.error(error.message);
            process.exitCode = 1;
        });
}

module.exports = {
    runSuggest,
    runList,
    runCheck,
    runMerge,
    runSplit,
    runStats,
    main,
};
