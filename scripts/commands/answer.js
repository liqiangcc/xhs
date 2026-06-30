#!/usr/bin/env node
'use strict';

const path = require('path');
const {
    loadCanonicalQuestions,
    saveCanonicalQuestions,
} = require('../lib/canonical_store');
const {
    answerPath,
    listAnswerFiles,
    readAnswerFile,
    writeAnswerTemplate,
    statusByCanonicalId,
} = require('../lib/answer_store');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_BUILD_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';

function defaultPaths(root) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        answersDir: path.join(root, 'review', 'answers'),
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = {};
    const booleanFlags = new Set(['missing', 'draft', 'ready', 'overwrite']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (applyGlobalBooleanOption(options, key)) continue;
            if (booleanFlags.has(key)) options[key] = true;
            else options[key] = args[++index];
        }
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js answer <init|init-batch|missing|status|validate|sync> [options]',
        '',
        'Commands:',
        '  init --canonical-id <id> [--overwrite] [--status <draft|ready|needs_update>]',
        '  init-batch [--priority <P0|P1|P2|P3>] [--limit <n>] [--status <draft|ready|needs_update>]',
        '  missing [--priority <P0|P1|P2|P3>] [--limit <n>]',
        '  status [--missing|--draft|--ready]',
        '  validate',
        '  sync',
        '',
        'Options:',
        '  --noWrite     Do not write run manifests for read-only commands',
        '  --noManifest  Do not write the run manifest',
    ].join('\n'));
}

function runInit(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const canonicalId = options['canonical-id'];
    if (!canonicalId) throw new Error('Usage: answer init --canonical-id <id>');
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const record = records.find((item) => item.canonical_id === canonicalId);
    if (!record) throw new Error(`Canonical not found: ${canonicalId}`);
    const result = writeAnswerTemplate(record, {
        answersDir: paths.answersDir,
        overwrite: options.overwrite,
        date: options.date || DEFAULT_BUILD_DATE,
        status: options.status,
    });
    return {
        schema_version: 'answer_init_result.v1',
        ok: true,
        canonical_id: canonicalId,
        created: result.created,
        answer_path: path.relative(root, result.filePath),
    };
}

function answerStatusFor(record, statuses) {
    return statuses.get(record.canonical_id) || record.answer_status || 'missing';
}

function missingRows(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const limit = Number(options.limit || 100);
    const statuses = statusByCanonicalId({ answersDir: paths.answersDir });
    return loadCanonicalQuestions({ filePath: paths.canonicalQuestions })
        .map((record) => ({
            canonical_id: record.canonical_id,
            canonical_title: record.canonical_title,
            review_priority: record.review_priority,
            answer_status: answerStatusFor(record, statuses),
            frequency: record.frequency,
            primary_domain: record.primary_domain,
            primary_entities: record.primary_entities,
            companies: record.companies,
        }))
        .filter((row) => row.answer_status === 'missing')
        .filter((row) => !options.priority || row.review_priority === options.priority)
        .sort((a, b) =>
            ({ P0: 0, P1: 1, P2: 2, P3: 3 }[a.review_priority] ?? 9) - ({ P0: 0, P1: 1, P2: 2, P3: 3 }[b.review_priority] ?? 9)
            || b.frequency - a.frequency
            || a.canonical_id.localeCompare(b.canonical_id)
        )
        .slice(0, limit);
}

function runMissing(options = {}) {
    const rows = missingRows(options);
    return {
        schema_version: 'answer_missing_report.v1',
        ok: true,
        priority: options.priority || null,
        returned_count: rows.length,
        rows,
    };
}

function runInitBatch(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const byId = new Map(records.map((record) => [record.canonical_id, record]));
    const rows = missingRows(options);
    const initialized = [];
    for (const row of rows) {
        const record = byId.get(row.canonical_id);
        const filePath = answerPath(record.canonical_id, { answersDir: paths.answersDir });
        const result = options.noWrite
            ? { created: false, filePath }
            : writeAnswerTemplate(record, {
                answersDir: paths.answersDir,
                overwrite: options.overwrite,
                date: options.date || DEFAULT_BUILD_DATE,
                status: options.status || 'draft',
            });
        initialized.push({
            canonical_id: record.canonical_id,
            created: result.created,
            answer_path: path.relative(root, result.filePath),
        });
    }
    return {
        schema_version: 'answer_init_batch_result.v1',
        ok: true,
        priority: options.priority || null,
        requested_count: rows.length,
        created_count: initialized.filter((row) => row.created).length,
        rows: initialized,
    };
}

function runValidate(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const canonicalIds = new Set(records.map((record) => record.canonical_id));
    const errors = [];
    const files = [];
    for (const filePath of listAnswerFiles({ answersDir: paths.answersDir })) {
        try {
            const answer = readAnswerFile(filePath);
            const expectedId = path.basename(filePath, '.md');
            if (answer.metadata.schema_version !== 'answer.v1') {
                errors.push({ file: path.relative(root, filePath), error: 'invalid_schema_version' });
            }
            if (answer.metadata.canonical_id !== expectedId) {
                errors.push({ file: path.relative(root, filePath), error: 'filename_metadata_mismatch', canonical_id: answer.metadata.canonical_id, expected_id: expectedId });
            }
            if (!canonicalIds.has(answer.metadata.canonical_id)) {
                errors.push({ file: path.relative(root, filePath), error: 'unknown_canonical_id', canonical_id: answer.metadata.canonical_id });
            }
            if (!['draft', 'ready', 'needs_update'].includes(answer.metadata.status)) {
                errors.push({ file: path.relative(root, filePath), error: 'invalid_status', status: answer.metadata.status });
            }
            files.push({ file: path.relative(root, filePath), canonical_id: answer.metadata.canonical_id, status: answer.metadata.status });
        } catch (error) {
            errors.push({ file: path.relative(root, filePath), error: error.message });
        }
    }
    return {
        schema_version: 'answer_validate_report.v1',
        ok: errors.length === 0,
        answer_count: files.length,
        error_count: errors.length,
        files,
        errors,
    };
}

function runSync(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const validation = runValidate(options);
    if (!validation.ok) return { ...validation, synced: false };
    const statuses = statusByCanonicalId({ answersDir: paths.answersDir });
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const updated = records.map((record) => ({
        ...record,
        answer_status: statuses.get(record.canonical_id) || 'missing',
    }));
    saveCanonicalQuestions(updated, { filePath: paths.canonicalQuestions });
    return {
        schema_version: 'answer_sync_result.v1',
        ok: true,
        synced: true,
        canonical_count: updated.length,
        answer_count: statuses.size,
        missing_count: updated.filter((record) => record.answer_status === 'missing').length,
    };
}

function runStatus(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const statuses = statusByCanonicalId({ answersDir: paths.answersDir });
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const rows = records.map((record) => ({
        canonical_id: record.canonical_id,
        canonical_title: record.canonical_title,
        review_priority: record.review_priority,
        answer_status: statuses.get(record.canonical_id) || 'missing',
        answer_path: statuses.has(record.canonical_id) ? path.relative(root, answerPath(record.canonical_id, { answersDir: paths.answersDir })) : null,
    })).filter((row) => {
        if (options.missing) return row.answer_status === 'missing';
        if (options.draft) return row.answer_status === 'draft';
        if (options.ready) return row.answer_status === 'ready';
        return true;
    }).sort((a, b) =>
        a.answer_status.localeCompare(b.answer_status)
        || a.canonical_id.localeCompare(b.canonical_id)
    );
    return {
        schema_version: 'answer_status.v1',
        total_count: rows.length,
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
        if (command === 'init') result = runInit(options);
        else if (command === 'init-batch') result = runInitBatch(options);
        else if (command === 'missing') result = runMissing(options);
        else if (command === 'status') result = runStatus(options);
        else if (command === 'validate') result = runValidate(options);
        else if (command === 'sync') result = runSync(options);
        else throw new Error(`Unknown answer command: ${command}`);
        writeRunManifest(options.root ? path.resolve(options.root) : DEFAULT_ROOT, `answer_${command}`, result, options);
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
    runInit,
    runInitBatch,
    runMissing,
    runStatus,
    runValidate,
    runSync,
    main,
};
