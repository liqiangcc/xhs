#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { computeQuestionId } = require('../lib/hash');
const { loadSchema, validateJsonlFile, validateRecord } = require('../lib/schema');
const { loadQuestions } = require('../lib/question_store');
const {
    loadTaxonomy,
    validateDomain,
    validateQuestionType,
    validateCognitiveDepth,
} = require('../lib/taxonomy');
const { writeJson } = require('../lib/io');
const { writeRunManifest } = require('../lib/run_manifest');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        reviewProgress: path.join(root, 'review', 'progress.json'),
        qualityDir: path.join(root, 'data', 'manifests', 'quality'),
        questionSchema: path.join(root, 'schemas', 'question.schema.json'),
        canonicalQuestionSchema: path.join(root, 'schemas', 'canonical_question.schema.json'),
        reviewProgressSchema: path.join(root, 'schemas', 'review_progress.schema.json'),
    };
}

function ensureQuestionsFile(questionsPath) {
    if (!fs.existsSync(questionsPath)) {
        throw new Error(`questions.jsonl not found: ${questionsPath}. Run migrate build-questions first.`);
    }
}

function location(question, index) {
    return {
        line: index + 1,
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
        original_question: question.original_question,
    };
}

function runSchemaValidation(options = {}) {
    const root = options.root || DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const questionsPath = options.questionsPath || paths.questions;
    ensureQuestionsFile(questionsPath);

    const questionSchema = loadSchema(options.schemaPath || paths.questionSchema);
    const results = [validateJsonlFile(questionsPath, questionSchema)];
    if (fs.existsSync(paths.canonicalQuestions)) {
        const canonicalSchema = loadSchema(paths.canonicalQuestionSchema);
        results.push(validateJsonlFile(paths.canonicalQuestions, canonicalSchema));
    }
    if (fs.existsSync(paths.reviewProgress)) {
        const progressSchema = loadSchema(paths.reviewProgressSchema);
        const progress = JSON.parse(fs.readFileSync(paths.reviewProgress, 'utf8'));
        const errors = validateRecord(progress, progressSchema);
        results.push({
            file: paths.reviewProgress,
            count: Array.isArray(progress.items) ? progress.items.length : 0,
            error_count: errors.length,
            errors: errors.map((error) => ({ line: null, ...error })),
        });
    }
    const errors = [];
    for (const result of results) {
        for (const error of result.errors) {
            errors.push({
                file: path.relative(root, result.file),
                ...error,
            });
        }
    }
    const report = {
        schema_version: 'validate_schema_report.v1',
        ok: errors.length === 0,
        checked_file: path.relative(root, questionsPath),
        checked_files: results.map((result) => ({
            file: path.relative(root, result.file),
            record_count: result.count,
            error_count: result.error_count,
        })),
        record_count: results[0].count,
        error_count: errors.length,
        errors,
    };
    writeJson(path.join(paths.qualityDir, 'validate_schema_report.json'), report);
    return report;
}

function runHashValidation(options = {}) {
    const root = options.root || DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const questionsPath = options.questionsPath || paths.questions;
    ensureQuestionsFile(questionsPath);

    const questions = loadQuestions({ filePath: questionsPath });
    const mismatches = [];
    const missing = [];
    questions.forEach((question, index) => {
        if (!question.question_id || !question.original_question) {
            missing.push(location(question, index));
            return;
        }
        const computed = computeQuestionId(question.original_question);
        if (computed !== question.question_id) {
            mismatches.push({
                ...location(question, index),
                computed_question_id: computed,
            });
        }
    });

    const report = {
        schema_version: 'validate_hash_report.v1',
        ok: missing.length === 0 && mismatches.length === 0,
        checked_file: path.relative(root, questionsPath),
        record_count: questions.length,
        missing_count: missing.length,
        mismatch_count: mismatches.length,
        missing,
        mismatches,
    };
    writeJson(path.join(paths.qualityDir, 'validate_hash_report.json'), report);
    return report;
}

function pushTaxonomyIssue(collection, question, index, field, result) {
    collection.push({
        ...location(question, index),
        field,
        value: result.value,
        normalized_value: result.normalized_value,
        reason: result.reason,
    });
}

function countBy(items, keyFn, limit = 100) {
    const counts = {};
    for (const item of items) {
        const key = keyFn(item);
        counts[key] = (counts[key] || 0) + 1;
    }
    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh'))
        .slice(0, limit)
        .map(([value, count]) => ({ value, count }));
}

function runTaxonomyValidation(options = {}) {
    const root = options.root || DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const questionsPath = options.questionsPath || paths.questions;
    ensureQuestionsFile(questionsPath);

    const taxonomy = loadTaxonomy(options.taxonomyPath);
    const questions = loadQuestions({ filePath: questionsPath });
    const legacyAliases = [];
    const unknown = [];
    const canonicalCounts = {
        domain: 0,
        question_type: 0,
        cognitive_depth: 0,
    };

    questions.forEach((question, index) => {
        const domain = validateDomain(question.domain, taxonomy);
        if (!domain.valid) pushTaxonomyIssue(unknown, question, index, 'domain', {
            value: question.domain,
            normalized_value: domain.normalized_domain,
            reason: domain.reason,
        });
        else if (domain.reason !== 'canonical') pushTaxonomyIssue(legacyAliases, question, index, 'domain', {
            value: question.domain,
            normalized_value: domain.normalized_domain,
            reason: domain.reason,
        });
        else canonicalCounts.domain++;

        const type = validateQuestionType(question.question_type, taxonomy);
        if (!type.valid) pushTaxonomyIssue(unknown, question, index, 'question_type', type);
        else if (type.reason !== 'canonical') pushTaxonomyIssue(legacyAliases, question, index, 'question_type', type);
        else canonicalCounts.question_type++;

        const depth = validateCognitiveDepth(question.cognitive_depth, taxonomy);
        if (!depth.valid) pushTaxonomyIssue(unknown, question, index, 'cognitive_depth', depth);
        else if (depth.reason !== 'canonical') pushTaxonomyIssue(legacyAliases, question, index, 'cognitive_depth', depth);
        else canonicalCounts.cognitive_depth++;
    });

    const report = {
        schema_version: 'validate_taxonomy_report.v1',
        ok: true,
        strict_ok: unknown.length === 0 && legacyAliases.length === 0,
        checked_file: path.relative(root, questionsPath),
        taxonomy_version: taxonomy.schema_version,
        record_count: questions.length,
        canonical_counts: canonicalCounts,
        legacy_alias_count: legacyAliases.length,
        unknown_count: unknown.length,
        legacy_aliases: legacyAliases,
        unknown,
    };
    writeJson(path.join(paths.qualityDir, 'validate_taxonomy_report.json'), report);

    const summary = {
        schema_version: 'validate_taxonomy_summary_report.v1',
        ok: true,
        strict_ok: report.strict_ok,
        checked_file: report.checked_file,
        taxonomy_version: report.taxonomy_version,
        record_count: report.record_count,
        legacy_alias_count: report.legacy_alias_count,
        unknown_count: report.unknown_count,
        top_unknown: countBy(unknown, (item) => `${item.field}: ${JSON.stringify(item.value)}`, 100),
        top_legacy_aliases: countBy(legacyAliases, (item) => `${item.field}: ${item.reason}: ${JSON.stringify(item.value)} -> ${JSON.stringify(item.normalized_value)}`, 100),
        reason_counts: countBy([...legacyAliases, ...unknown], (item) => `${item.field}: ${item.reason}`, 50),
    };
    writeJson(path.join(paths.qualityDir, 'validate_taxonomy_summary_report.json'), summary);
    return report;
}

function runAll(options = {}) {
    const schema = runSchemaValidation(options);
    const taxonomy = runTaxonomyValidation(options);
    const hash = runHashValidation(options);
    return {
        schema_version: 'validate_all_report.v1',
        ok: schema.ok && hash.ok,
        schema: {
            ok: schema.ok,
            error_count: schema.error_count,
        },
        taxonomy: {
            ok: taxonomy.ok,
            strict_ok: taxonomy.strict_ok,
            legacy_alias_count: taxonomy.legacy_alias_count,
            unknown_count: taxonomy.unknown_count,
        },
        hash: {
            ok: hash.ok,
            mismatch_count: hash.mismatch_count,
            missing_count: hash.missing_count,
        },
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const options = {};
    const target = args[0] || 'all';
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (arg === '--root') options.root = path.resolve(args[++index]);
        else if (arg === '--questions') options.questionsPath = path.resolve(args[++index]);
        else if (arg === '--schema') options.schemaPath = path.resolve(args[++index]);
        else if (arg === '--taxonomy') options.taxonomyPath = path.resolve(args[++index]);
        else if (arg === '--help' || arg === 'help') options.help = true;
    }
    return { target, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js validate <schema|taxonomy|hash|all>',
        '',
        'Options:',
        '  --questions <path>  Override questions.jsonl path',
        '  --schema <path>     Override question schema path',
        '  --taxonomy <path>   Override taxonomy path',
        '  --root <path>       Override repository root',
    ].join('\n'));
}

function runTarget(target, options = {}) {
    if (target === 'schema') return runSchemaValidation(options);
    if (target === 'taxonomy') return runTaxonomyValidation(options);
    if (target === 'hash') return runHashValidation(options);
    if (target === 'all') return runAll(options);
    throw new Error(`Unknown validate target: ${target}`);
}

function main(argv = process.argv) {
    const { target, options } = parseArgs(argv);
    if (options.help || target === 'help') {
        printHelp();
        return 0;
    }

    try {
        const report = runTarget(target, options);
        writeRunManifest(options.root || DEFAULT_ROOT, `validate_${target}`, report, options);
        console.log(JSON.stringify(report, null, 2));
        return report.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    runSchemaValidation,
    runTaxonomyValidation,
    runHashValidation,
    runAll,
    runTarget,
    main,
};
