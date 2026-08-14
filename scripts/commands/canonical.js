#!/usr/bin/env node
'use strict';

const path = require('path');
const { writeJson } = require('../lib/io');
const { loadQuestions } = require('../lib/question_store');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption, shouldWriteReports } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { priorityRank } = require('../../src/domain/canonical/priority-policy');
const { evaluateCanonicalIntegrity } = require('../../src/domain/canonical/integrity-policy');
const { createApplication } = require('../../src/bootstrap/create-application');
const { presentCanonicalAcceptResult } = require('../../src/interfaces/cli/canonical-accept-presenter');
const { presentCanonicalMergeResult } = require('../../src/interfaces/cli/canonical-merge-presenter');
const { presentCanonicalSplitResult } = require('../../src/interfaces/cli/canonical-split-presenter');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        qualityReport: path.join(root, 'data', 'manifests', 'canonical', 'canonical_quality_report.json'),
    };
}

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
        'Usage: node scripts/xhs.js canonical <suggest|accept|stats> [options]',
        '',
        'Commands:',
        '  suggest --entity <value> [--limit <n>]',
        '  suggest --hotspot [--limit <n>]',
        '  accept --candidate-id <id> --canonical-id <cq_id>  (legacy candidate manifest)',
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

/**
 * @deprecated Legacy compatibility for historical/manual canonical_candidates.v1 only.
 * New relationships must use canonical suggest -> dedup decide -> dedup apply.
 */
async function runAccept(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const candidateId = options['candidate-id'];
    const canonicalId = options['canonical-id'];
    if (!candidateId || !canonicalId) {
        throw new Error('Usage: canonical accept --candidate-id <id> --canonical-id <cq_id>');
    }
    assertCanonicalId(canonicalId);

    const application = createApplication({ root });
    const result = await application.canonical.accept({
        candidate_id: candidateId,
        canonical_id: canonicalId,
        ...(options.title ? { title: options.title } : {}),
    });
    return presentCanonicalAcceptResult(result);
}

function runList(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const limit = Number(options.limit || 50);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions })
        .filter((record) => !options.priority || record.review_priority === options.priority)
        .filter((record) => !options['answer-status'] || record.answer_status === options['answer-status'])
        .sort((a, b) =>
            priorityRank(a.review_priority) - priorityRank(b.review_priority)
            || b.frequency - a.frequency
            || a.canonical_id.localeCompare(b.canonical_id)
        );
    return {
        schema_version: 'canonical_list.v1',
        total_count: records.length,
        returned_count: Math.min(records.length, limit),
        records: records.slice(0, limit).map((record) => ({
            canonical_id: record.canonical_id,
            canonical_title: record.canonical_title,
            review_priority: record.review_priority,
            answer_status: record.answer_status,
            frequency: record.frequency,
            question_ids: record.question_ids,
            companies: record.companies,
            primary_domain: record.primary_domain,
            primary_entities: record.primary_entities,
        })),
    };
}

function runCheck(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const questions = loadQuestions({ filePath: paths.questions });
    const report = evaluateCanonicalIntegrity(records, questions);
    if (shouldWriteReports(options)) {
        writeJson(paths.qualityReport, report);
    }
    return report;
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
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const questions = loadQuestions({ filePath: paths.questions });
    const canonicalQuestionIds = new Set(records.flatMap((record) => record.question_ids || []));
    return {
        schema_version: 'canonical_stats.v1',
        canonical_count: records.length,
        canonical_question_id_count: canonicalQuestionIds.size,
        assigned_question_rows: questions.filter((question) => question.canonical_id).length,
        top_canonical: [...records]
            .sort((a, b) => b.frequency - a.frequency || a.canonical_id.localeCompare(b.canonical_id))
            .slice(0, Number(options.limit || 20))
            .map((record) => ({
                canonical_id: record.canonical_id,
                canonical_title: record.canonical_title,
                frequency: record.frequency,
                companies: record.companies,
                primary_entities: record.primary_entities,
            })),
    };
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
        else if (command === 'accept') result = runAccept(options);
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
    runAccept,
    runList,
    runCheck,
    runMerge,
    runSplit,
    runStats,
    main,
};
