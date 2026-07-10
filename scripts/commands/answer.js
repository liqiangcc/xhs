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
    writeAnswerMetadata,
    writeAnswerTemplate,
    statusByCanonicalId,
    validateAnswerContent,
} = require('../lib/answer_store');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const { run: runAnswerTypeAudit } = require('../content/audit_answer_types');
const { run: runAnswerQueue } = require('../content/build_answer_rewrite_queue');
const {
    buildAnswerContext,
    renderCandidate,
    runAnswerAudit,
    atomicPromote,
    atomicDemote,
    atomicDemoteMissingEvidence,
    recordHumanReview,
} = require('../lib/answer_quality');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        answersDir: path.join(root, 'review', 'answers'),
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    const booleanFlags = new Set(['missing', 'draft', 'ready', 'overwrite', 'strict', 'check', 'fixtures', 'require-evidence', 'require-code']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (applyGlobalBooleanOption(options, key)) continue;
            if (booleanFlags.has(key)) {
                options[key] = true;
                if (key === 'check') options.noWrite = true;
            }
            else if (key === 'type') {
                const value = args[++index];
                options.type = [...(options.type || []), value];
            } else options[key] = args[++index];
        }
        else options._.push(arg);
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js answer <init|init-batch|missing|status|validate|sync|quality-migrate|context|candidate|audit|promote|demote|demote-missing-evidence|human-review|type-audit|queue> [options]',
        '',
        'Commands:',
        '  init --canonical-id <id> [--overwrite] [--status <draft|ready|needs_update>]',
        '  init-batch [--priority <P0|P1|P2|P3>] [--limit <n>] [--status <draft|ready|needs_update>]',
        '  missing [--priority <P0|P1|P2|P3>] [--limit <n>]',
        '  status [--missing|--draft|--ready]',
        '  validate [--strict]',
        '  sync',
        '  quality-migrate [--check] [--expected-curated <n>] [--expected-long-tail <n>]',
        '  context --canonical-id <id>',
        '  candidate render --spec <json> [--noWrite]',
        '  audit [--candidate <path>] [--tier <candidate|curated>] [--type <type> ...] [--set <json>] [--require-evidence] [--require-code] [--noWrite]',
        '  promote --canonical-id <id> --candidate <path> --evidence <path> [--noWrite]',
        '  demote --canonical-id <id> --evidence <path> [--noWrite]',
        '  demote-missing-evidence --canonical-id <id> [--noWrite]',
        '  human-review --canonical-id <id> --evidence <path> --review <json> [--noWrite]',
        '  type-audit [--check] [--noWrite]',
        '  queue check [--noWrite]',
        '',
        'Options:',
        '  --strict     Validate ready answer content sections and TODO placeholders',
        '  --noWrite    Do not write run manifests for read-only commands',
        '  --noManifest Do not write the run manifest',
    ].join('\n'));
}

function expectedCount(options, dashedKey, camelKey, fallback) {
    const raw = options[dashedKey] ?? options[camelKey] ?? fallback;
    if (raw === undefined || raw === null) return null;
    const value = Number(raw);
    if (!Number.isInteger(value) || value < 0) throw new Error(`${dashedKey} must be a non-negative integer`);
    return value;
}

function planQualityMigration(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const expectedCurated = expectedCount(options, 'expected-curated', 'expectedCurated', root === DEFAULT_ROOT ? 100 : null);
    const expectedLongTail = expectedCount(options, 'expected-long-tail', 'expectedLongTail', root === DEFAULT_ROOT ? 9160 : null);
    const rows = [];
    const errors = [];
    let curatedCount = 0;
    let longTailCount = 0;

    for (const filePath of listAnswerFiles({ answersDir: paths.answersDir })) {
        const answer = readAnswerFile(filePath);
        const metadata = answer.metadata;
        let targetMetadata;
        let classification;
        if (metadata.quality_tier === 'long_tail_baseline') {
            classification = 'long_tail_baseline';
            longTailCount += 1;
            targetMetadata = { ...metadata, status: 'needs_update' };
        } else if (metadata.quality_tier === 'curated' || metadata.quality_tier === 'curated_audit_failed') {
            classification = 'curated';
            curatedCount += 1;
            targetMetadata = metadata;
        } else if (!metadata.quality_tier && metadata.status === 'ready' && !metadata.generator_version) {
            classification = 'curated';
            curatedCount += 1;
            targetMetadata = { ...metadata, quality_tier: 'curated' };
        } else {
            errors.push({
                file: path.relative(root, filePath),
                canonical_id: metadata.canonical_id,
                error: 'ambiguous_quality_tier',
                quality_tier: metadata.quality_tier || null,
                status: metadata.status || null,
                generator_version: metadata.generator_version || null,
            });
            continue;
        }
        const changed = JSON.stringify(targetMetadata) !== JSON.stringify(metadata);
        rows.push({
            file: path.relative(root, filePath),
            canonical_id: metadata.canonical_id,
            classification,
            from_status: metadata.status,
            to_status: targetMetadata.status,
            from_quality_tier: metadata.quality_tier || null,
            to_quality_tier: targetMetadata.quality_tier,
            changed,
            filePath,
            targetMetadata,
        });
    }

    const scopeErrors = [];
    if (expectedCurated !== null && curatedCount !== expectedCurated) {
        scopeErrors.push({ error: 'curated_scope_mismatch', expected: expectedCurated, actual: curatedCount });
    }
    if (expectedLongTail !== null && longTailCount !== expectedLongTail) {
        scopeErrors.push({ error: 'long_tail_scope_mismatch', expected: expectedLongTail, actual: longTailCount });
    }
    errors.push(...scopeErrors);
    return {
        root,
        rows,
        result: {
            schema_version: 'answer_quality_migration.v1',
            ok: errors.length === 0,
            dry_run: true,
            answer_count: rows.length,
            curated_count: curatedCount,
            long_tail_baseline_count: longTailCount,
            changed_count: rows.filter((row) => row.changed).length,
            unchanged_count: rows.filter((row) => !row.changed).length,
            error_count: errors.length,
            errors,
            changes: rows.filter((row) => row.changed).slice(0, 20).map(({ filePath, targetMetadata, ...row }) => row),
        },
    };
}

function runQualityMigrate(options = {}) {
    const plan = planQualityMigration(options);
    const dryRun = Boolean(options.noWrite || options.check);
    if (plan.result.ok && !dryRun) {
        for (const row of plan.rows) {
            if (row.changed) writeAnswerMetadata(row.filePath, row.targetMetadata);
        }
    }
    return {
        ...plan.result,
        dry_run: dryRun,
        migrated: plan.result.ok && !dryRun,
    };
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
        date: defaultDate(options),
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
                date: defaultDate(options),
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
    const statuses = new Map();
    const errors = [];
    const files = [];
    for (const filePath of listAnswerFiles({ answersDir: paths.answersDir })) {
        const relativeFile = path.relative(root, filePath);
        try {
            const answer = readAnswerFile(filePath);
            const expectedId = path.basename(filePath, '.md');
            if (answer.metadata.schema_version !== 'answer.v1') {
                errors.push({ file: relativeFile, error: 'invalid_schema_version' });
            }
            if (answer.metadata.canonical_id !== expectedId) {
                errors.push({ file: relativeFile, error: 'filename_metadata_mismatch', canonical_id: answer.metadata.canonical_id, expected_id: expectedId });
            }
            if (!canonicalIds.has(answer.metadata.canonical_id)) {
                errors.push({ file: relativeFile, error: 'unknown_canonical_id', canonical_id: answer.metadata.canonical_id });
            }
            if (!['draft', 'ready', 'needs_update'].includes(answer.metadata.status)) {
                errors.push({ file: relativeFile, error: 'invalid_status', status: answer.metadata.status });
            }
            const status = answer.metadata.status || 'draft';
            statuses.set(answer.metadata.canonical_id, status);
            if (options.strict) {
                for (const issue of validateAnswerContent(answer)) {
                    errors.push({ file: relativeFile, ...issue });
                }
            }
            files.push({ file: relativeFile, canonical_id: answer.metadata.canonical_id, status });
        } catch (error) {
            errors.push({ file: relativeFile, error: error.message });
        }
    }

    if (options.strict) {
        for (const record of records) {
            if (record.answer_status !== 'ready') continue;
            const actualStatus = statuses.get(record.canonical_id) || 'missing';
            if (actualStatus !== 'ready') {
                errors.push({
                    file: null,
                    error: 'ready_status_without_ready_file',
                    canonical_id: record.canonical_id,
                    expected_status: 'ready',
                    actual_status: actualStatus,
                });
            }
        }
    }

    return {
        schema_version: 'answer_validate_report.v1',
        ok: errors.length === 0,
        strict: Boolean(options.strict),
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
        else if (command === 'quality-migrate') result = runQualityMigrate(options);
        else if (command === 'context') result = buildAnswerContext(options);
        else if (command === 'candidate' && options._[0] === 'render') result = renderCandidate(options);
        else if (command === 'audit') result = runAnswerAudit(options);
        else if (command === 'promote') result = atomicPromote(options);
        else if (command === 'demote') result = atomicDemote(options);
        else if (command === 'demote-missing-evidence') result = atomicDemoteMissingEvidence(options);
        else if (command === 'human-review') result = recordHumanReview(options);
        else if (command === 'type-audit') result = runAnswerTypeAudit(options);
        else if (command === 'queue' && options._[0] === 'check') result = runAnswerQueue({ ...options, check: true, noWrite: true });
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
    planQualityMigration,
    runQualityMigrate,
    buildAnswerContext,
    renderCandidate,
    runAnswerAudit,
    atomicPromote,
    atomicDemote,
    atomicDemoteMissingEvidence,
    recordHumanReview,
    main,
};
