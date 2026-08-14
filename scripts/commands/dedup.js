#!/usr/bin/env node
'use strict';

const path = require('path');
const { createApplication } = require('../../src/bootstrap/create-application');
const { presentDedupDecisionResult } = require('../../src/interfaces/cli/dedup-decision-presenter');
const { presentDedupApplyResult } = require('../../src/interfaces/cli/dedup-apply-presenter');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    for (let index = 1; index < args.length; index += 1) {
        const arg = args[index];
        if (!arg) continue;
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            const next = args[index + 1];
            if (next == null || String(next).startsWith('--')) {
                throw new Error(`Option --${key} requires a value`);
            }
            options[key] = next;
            index += 1;
        } else {
            options._.push(arg);
        }
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js dedup <decide|apply> [options]',
        '',
        'Commands:',
        '  decide --relation-candidate-key <key> --relation <relation> --actor-type <human|ai> --actor-id <id>',
        '         [--actor-display-name <name>] [--rationale <text>] [--decided-at <timestamp>]',
        '  apply  --relation-candidate-key <key> [--canonical-id <cq_id> --canonical-title <title>]',
        '',
        'The CLI delegates all review freshness, relation policy, Canonical planning, and mutation control to Application.',
    ].join('\n'));
}

function rootFrom(options) {
    return options.root ? path.resolve(options.root) : DEFAULT_ROOT;
}

async function runDecide(options = {}) {
    const relationCandidateKey = options['relation-candidate-key'];
    const relation = options.relation;
    const actorType = options['actor-type'];
    const actorId = options['actor-id'];
    if (!relationCandidateKey || !relation || !actorType || !actorId) {
        throw new Error(
            'Usage: dedup decide --relation-candidate-key <key> --relation <relation> --actor-type <human|ai> --actor-id <id>',
        );
    }

    const actor = {
        type: actorType,
        id: actorId,
        ...(options['actor-display-name'] == null
            ? {}
            : { display_name: options['actor-display-name'] }),
    };
    const application = createApplication({ root: rootFrom(options) });
    const result = await application.dedup.recordDecision({
        relation_candidate_key: relationCandidateKey,
        relation,
        actor,
        ...(options.rationale == null ? {} : { rationale: options.rationale }),
        ...(options['decided-at'] == null ? {} : { decided_at: options['decided-at'] }),
    });
    return presentDedupDecisionResult(result);
}

async function runApply(options = {}) {
    const relationCandidateKey = options['relation-candidate-key'];
    if (!relationCandidateKey) {
        throw new Error('Usage: dedup apply --relation-candidate-key <key> [--canonical-id <cq_id> --canonical-title <title>]');
    }
    const hasCanonicalId = options['canonical-id'] != null;
    const hasCanonicalTitle = options['canonical-title'] != null;
    if (hasCanonicalId !== hasCanonicalTitle) {
        throw new Error('--canonical-id and --canonical-title must be provided together');
    }

    const application = createApplication({ root: rootFrom(options) });
    const result = await application.dedup.applyDecision({
        relation_candidate_key: relationCandidateKey,
        ...(hasCanonicalId ? {
            canonical_id: options['canonical-id'],
            canonical_title: options['canonical-title'],
        } : {}),
    });
    return presentDedupApplyResult(result);
}

function emitResult(result) {
    console.log(JSON.stringify(result, null, 2));
    return 0;
}

function handleError(error) {
    console.error(error.message);
    return 1;
}

function main(argv = process.argv) {
    let parsed;
    try {
        parsed = parseArgs(argv);
    } catch (error) {
        return handleError(error);
    }
    const { command, options } = parsed;
    if (!command || command === 'help' || command === '--help') {
        printHelp();
        return 0;
    }

    try {
        let result;
        if (command === 'decide') result = runDecide(options);
        else if (command === 'apply') result = runApply(options);
        else throw new Error(`Unknown dedup command: ${command}`);
        return Promise.resolve(result)
            .then(emitResult)
            .catch(handleError);
    } catch (error) {
        return handleError(error);
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
    parseArgs,
    runDecide,
    runApply,
    main,
};
