#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { computeQuestionId } = require('../lib/hash');
const {
    ensureDir,
    listJsonFiles,
    readJson,
    stablePrettyStringify,
    stableStringify,
    writeJson,
    writeJsonl,
} = require('../lib/io');
const {
    loadCanonicalQuestions,
    buildQuestionToCanonicalMap,
} = require('../lib/canonical_store');
const { writeRunManifest } = require('../lib/run_manifest');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_BUILD_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';

function stringValue(value, fallback = '未知') {
    if (value === undefined || value === null || value === '') return fallback;
    return String(value);
}

function normalizeArray(value) {
    if (!Array.isArray(value)) return [];
    return value
        .filter((item) => item !== undefined && item !== null && String(item).trim() !== '')
        .map((item) => String(item));
}

function compareRecords(a, b) {
    return stableStringify(a).localeCompare(stableStringify(b), 'zh');
}

function addCount(map, key) {
    const value = String(key || '');
    map[value] = (map[value] || 0) + 1;
}

function buildQuestionRecord(note, question, sourceQuestionIndex, canonicalByQuestionId = new Map()) {
    const originalQuestion = String(question.original_question);
    const questionId = computeQuestionId(originalQuestion);
    return {
        question_id: questionId,
        original_question: originalQuestion,
        source_note_id: stringValue(note.note_id),
        source_question_index: sourceQuestionIndex,
        company: stringValue(note.company),
        position: stringValue(note.position),
        round: stringValue(note.round, '未注明'),
        level: stringValue(note.level),
        year: stringValue(note.year),
        date: stringValue(note.date),
        domain: {
            l1: stringValue(question.domain?.l1, '其他'),
            l2: stringValue(question.domain?.l2, '其他'),
        },
        question_type: stringValue(question.question_type, '其他'),
        cognitive_depth: stringValue(question.cognitive_depth, 'N_A'),
        tech_entities: normalizeArray(question.tech_entities),
        business_context: normalizeArray(question.business_context),
        is_valid_for_library: question.is_valid_for_library === true,
        canonical_id: canonicalByQuestionId.get(questionId) || null,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    };
}

function buildSourceRecord(question, buildDate) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
        company: question.company,
        position: question.position,
        round: question.round,
        level: question.level,
        year: question.year,
        source_weight: 1,
        created_at: buildDate,
    };
}

function buildSourceNoteRecord(note, sourceNoteId, taggedQuestions, migratedCount, buildDate) {
    const isEmpty = taggedQuestions.length === 0;
    return {
        note_id: sourceNoteId,
        source: stringValue(note.source, '小红书'),
        company: stringValue(note.company),
        position: stringValue(note.position),
        round: stringValue(note.round, '未注明'),
        level: stringValue(note.level),
        year: stringValue(note.year),
        date: stringValue(note.date),
        status: isEmpty ? 'skipped_invalid' : 'tagged_ready',
        status_reason: isEmpty ? 'empty tagged_questions' : null,
        question_count: migratedCount,
        raw_tagged_question_count: taggedQuestions.length,
        schema_version: 'source_note.v1',
        created_at: buildDate,
        updated_at: buildDate,
    };
}

function buildQuestionsFromTagged(options = {}) {
    const root = options.root || DEFAULT_ROOT;
    const taggedDir = options.taggedDir || path.join(root, 'note_tagged');
    const buildDate = options.buildDate || DEFAULT_BUILD_DATE;
    const canonicalPath = options.canonicalPath || path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const canonicalByQuestionId = buildQuestionToCanonicalMap(loadCanonicalQuestions({ filePath: canonicalPath }));

    const questions = [];
    const questionSources = [];
    const sourceNotes = [];
    const oldHashMismatches = [];
    const skippedQuestions = [];
    const missingFields = {};
    const duplicateTracker = {};
    const malformedFiles = [];
    const taxonomyCounts = {
        domain_l1: {},
        domain_l2: {},
        question_type: {},
        cognitive_depth: {},
    };

    let totalTaggedQuestions = 0;
    let validQuestions = 0;
    let invalidQuestions = 0;
    let emptyNotes = 0;

    for (const filePath of listJsonFiles(taggedDir)) {
        const fileName = path.basename(filePath);
        const sourceNoteId = path.basename(fileName, '.json');
        let note;
        try {
            note = readJson(filePath);
        } catch (error) {
            malformedFiles.push({
                file: path.relative(root, filePath),
                error: error.message,
            });
            continue;
        }

        if (!note.note_id) note.note_id = sourceNoteId;
        const taggedQuestions = Array.isArray(note.tagged_questions) ? note.tagged_questions : [];
        if (taggedQuestions.length === 0) emptyNotes++;
        totalTaggedQuestions += taggedQuestions.length;

        let migratedInNote = 0;
        taggedQuestions.forEach((question, sourceQuestionIndex) => {
            const location = {
                source_note_id: stringValue(note.note_id, sourceNoteId),
                source_question_index: sourceQuestionIndex,
                file: path.relative(root, filePath),
            };

            if (!question || typeof question !== 'object') {
                skippedQuestions.push({
                    ...location,
                    reason: 'question is not an object',
                });
                return;
            }

            if (!question.original_question) {
                addCount(missingFields, 'original_question');
                skippedQuestions.push({
                    ...location,
                    legacy_question_id: question.question_id || null,
                    reason: 'missing original_question',
                });
                return;
            }

            for (const field of ['question_id', 'domain', 'question_type', 'cognitive_depth', 'tech_entities', 'is_valid_for_library']) {
                if (!(field in question)) addCount(missingFields, field);
            }

            const record = buildQuestionRecord(note, question, sourceQuestionIndex, canonicalByQuestionId);
            const legacyQuestionId = question.question_id || null;
            if (!legacyQuestionId) {
                addCount(missingFields, 'question_id');
            } else if (legacyQuestionId !== record.question_id) {
                oldHashMismatches.push({
                    ...location,
                    legacy_question_id: legacyQuestionId,
                    computed_question_id: record.question_id,
                    original_question: record.original_question,
                });
            }

            if (record.is_valid_for_library) validQuestions++;
            else invalidQuestions++;

            addCount(taxonomyCounts.domain_l1, record.domain.l1);
            addCount(taxonomyCounts.domain_l2, record.domain.l2);
            addCount(taxonomyCounts.question_type, record.question_type);
            addCount(taxonomyCounts.cognitive_depth, record.cognitive_depth);

            questions.push(record);
            questionSources.push(buildSourceRecord(record, buildDate));
            duplicateTracker[record.question_id] = (duplicateTracker[record.question_id] || 0) + 1;
            migratedInNote++;
        });

        sourceNotes.push(buildSourceNoteRecord(note, stringValue(note.note_id, sourceNoteId), taggedQuestions, migratedInNote, buildDate));
    }

    questions.sort((a, b) =>
        a.source_note_id.localeCompare(b.source_note_id, 'zh')
        || a.source_question_index - b.source_question_index
        || a.question_id.localeCompare(b.question_id)
    );
    questionSources.sort(compareRecords);
    sourceNotes.sort((a, b) => a.note_id.localeCompare(b.note_id, 'zh'));
    oldHashMismatches.sort(compareRecords);
    skippedQuestions.sort(compareRecords);

    const duplicateQuestionIds = Object.entries(duplicateTracker)
        .filter(([, count]) => count > 1)
        .map(([questionId, count]) => ({ question_id: questionId, occurrence_count: count }))
        .sort((a, b) => b.occurrence_count - a.occurrence_count || a.question_id.localeCompare(b.question_id));

    const report = {
        schema_version: 'build_questions_report.v1',
        taxonomy_version: 'taxonomy.v1',
        build_date: buildDate,
        input: {
            tagged_dir: path.relative(root, taggedDir) || '.',
            source_file_count: sourceNotes.length + malformedFiles.length,
        },
        output: {
            questions_path: 'data/questions/questions.jsonl',
            question_sources_path: 'data/questions/question_sources.jsonl',
            source_notes_path: 'data/sources/notes.jsonl',
            question_count: questions.length,
            question_source_count: questionSources.length,
            source_note_count: sourceNotes.length,
        },
        counts: {
            total_tagged_questions: totalTaggedQuestions,
            migrated_questions: questions.length,
            skipped_questions: skippedQuestions.length,
            valid_questions: validQuestions,
            invalid_questions: invalidQuestions,
            empty_notes: emptyNotes,
            malformed_files: malformedFiles.length,
            old_hash_mismatches: oldHashMismatches.length,
            duplicate_question_ids: duplicateQuestionIds.length,
        },
        missing_fields: missingFields,
        taxonomy_counts: taxonomyCounts,
        malformed_files: malformedFiles,
        skipped_questions: skippedQuestions,
        old_hash_mismatches: oldHashMismatches,
        duplicate_question_ids: duplicateQuestionIds,
    };

    return {
        questions,
        questionSources,
        sourceNotes,
        report,
    };
}

function outputPaths(root) {
    return {
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        questionSources: path.join(root, 'data', 'questions', 'question_sources.jsonl'),
        sourceNotes: path.join(root, 'data', 'sources', 'notes.jsonl'),
        report: path.join(root, 'data', 'manifests', 'quality', 'build_questions_report.json'),
    };
}

function renderOutputs(result) {
    return {
        questions: result.questions.map(stableStringify).join('\n') + (result.questions.length ? '\n' : ''),
        questionSources: result.questionSources.map(stableStringify).join('\n') + (result.questionSources.length ? '\n' : ''),
        sourceNotes: result.sourceNotes.map(stableStringify).join('\n') + (result.sourceNotes.length ? '\n' : ''),
        report: stablePrettyStringify(result.report),
    };
}

function writeOutputs(root, result) {
    const paths = outputPaths(root);
    ensureDir(path.dirname(paths.questions));
    ensureDir(path.dirname(paths.sourceNotes));
    ensureDir(path.dirname(paths.report));
    writeJsonl(paths.questions, result.questions);
    writeJsonl(paths.questionSources, result.questionSources);
    writeJsonl(paths.sourceNotes, result.sourceNotes);
    writeJson(paths.report, result.report);
    return paths;
}

function checkOutputs(root, result) {
    const paths = outputPaths(root);
    const rendered = renderOutputs(result);
    const files = [
        ['questions', paths.questions],
        ['questionSources', paths.questionSources],
        ['sourceNotes', paths.sourceNotes],
        ['report', paths.report],
    ];
    const diffs = [];
    for (const [key, filePath] of files) {
        const actual = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : null;
        if (actual !== rendered[key]) {
            diffs.push(path.relative(root, filePath));
        }
    }
    return {
        ok: diffs.length === 0,
        diffs,
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const options = { check: false };
    for (let index = 0; index < args.length; index++) {
        const arg = args[index];
        if (arg === '--check') options.check = true;
        else if (arg === '--tagged-dir') options.taggedDir = path.resolve(args[++index]);
        else if (arg === '--root') options.root = path.resolve(args[++index]);
        else if (arg === '--build-date') options.buildDate = args[++index];
        else if (arg === '--help' || arg === 'help') options.help = true;
    }
    return options;
}

function printHelp() {
    console.log([
        'Usage: node scripts/migrate/build_questions_from_tagged.js [--check]',
        '',
        'Options:',
        '  --check              Regenerate in memory and fail if data outputs differ',
        '  --tagged-dir <path>  Override note_tagged input directory',
        '  --root <path>        Override repository root',
        '  --build-date <date>  Stable created_at/updated_at value',
    ].join('\n'));
}

function main(argv = process.argv) {
    const options = parseArgs(argv);
    if (options.help) {
        printHelp();
        return 0;
    }

    const root = options.root || DEFAULT_ROOT;
    const result = buildQuestionsFromTagged(options);

    if (options.check) {
        const check = checkOutputs(root, result);
        if (!check.ok) {
            console.error(JSON.stringify({ ok: false, changed_files: check.diffs }, null, 2));
            return 1;
        }
        const summary = {
            ok: true,
            question_count: result.questions.length,
            source_note_count: result.sourceNotes.length,
            quality_report: 'data/manifests/quality/build_questions_report.json',
        };
        writeRunManifest(root, 'migrate_build_questions_check', summary, options);
        console.log(JSON.stringify(summary, null, 2));
        return 0;
    }

    writeOutputs(root, result);
    const summary = {
        ok: true,
        question_count: result.questions.length,
        question_source_count: result.questionSources.length,
        source_note_count: result.sourceNotes.length,
        skipped_questions: result.report.counts.skipped_questions,
        old_hash_mismatches: result.report.counts.old_hash_mismatches,
        quality_report: 'data/manifests/quality/build_questions_report.json',
    };
    writeRunManifest(root, 'migrate_build_questions', summary, options);
    console.log(JSON.stringify(summary, null, 2));
    return 0;
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    buildQuestionsFromTagged,
    writeOutputs,
    checkOutputs,
    outputPaths,
    main,
};
