'use strict';

const fs = require('fs');
const path = require('path');
const { loadQuestions } = require('../lib/question_store');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { listAnswerFiles, readAnswerFile } = require('../lib/answer_store');
const { loadProgress, isDue, todayString } = require('../lib/review_store');
const { loadIssueLinks } = require('../lib/issue_store');
const { buildIndexes, checkIndexes } = require('../lib/index_store');
const { writeJson, ensureDir } = require('../lib/io');
const { writeRunManifest } = require('../lib/run_manifest');
const { runTaxonomyValidation } = require('./validate');
const { runCheck: runCanonicalCheck } = require('./canonical');
const { runValidate: runAnswerValidate } = require('./answer');
const { applyGlobalBooleanOption } = require('../lib/cli_options');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';

function defaultPaths(root) {
    return {
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        indexDir: path.join(root, 'data', 'indexes'),
        answersDir: path.join(root, 'review', 'answers'),
        progressPath: path.join(root, 'review', 'progress.json'),
        issueLinksPath: path.join(root, 'review', 'issue_links.json'),
        jsonReport: path.join(root, 'data', 'manifests', 'reports', 'quality_report.json'),
        markdownReport: path.join(root, 'review', 'plans', 'quality_report.md'),
    };
}

function countBy(items, keyFn) {
    const counts = {};
    for (const item of items || []) {
        const key = keyFn(item) || 'unknown';
        counts[key] = (counts[key] || 0) + 1;
    }
    return Object.fromEntries(Object.entries(counts).sort((a, b) => a[0].localeCompare(b[0], 'zh')));
}

function topItems(items, keyFn, limit = 20) {
    return Object.entries(countBy(items, keyFn))
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh'))
        .slice(0, limit)
        .map(([value, count]) => ({ value, count }));
}

function readAnswers(root, paths) {
    const rows = [];
    const errors = [];
    for (const filePath of listAnswerFiles({ answersDir: paths.answersDir })) {
        try {
            const answer = readAnswerFile(filePath);
            rows.push({
                file: path.relative(root, filePath),
                canonical_id: answer.metadata.canonical_id,
                status: answer.metadata.status || 'draft',
                updated_at: answer.metadata.updated_at || null,
            });
        } catch (error) {
            errors.push({
                file: path.relative(root, filePath),
                error: error.message,
            });
        }
    }
    return { rows, errors };
}

function buildQualityReport(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const date = options.date || DEFAULT_DATE;
    const questions = loadQuestions({ filePath: paths.questions });
    const canonicalRecords = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const progress = loadProgress({ progressPath: paths.progressPath, date });
    const issueLinks = loadIssueLinks({ filePath: paths.issueLinksPath, date });
    const answers = readAnswers(root, paths);

    const validQuestions = questions.filter((question) => question.is_valid_for_library);
    const assignedQuestions = questions.filter((question) => question.canonical_id);
    const p0Canonical = canonicalRecords.filter((record) => record.review_priority === 'P0');
    const p0MissingAnswers = p0Canonical.filter((record) => (record.answer_status || 'missing') === 'missing');
    const reviewItems = progress.items || [];
    const dueItems = reviewItems.filter((item) => isDue(item, date));
    const indexes = buildIndexes(questions, { canonicalQuestions: canonicalRecords });
    const indexCheck = checkIndexes(indexes, paths.indexDir);
    const taxonomy = runTaxonomyValidation({ root, noWrite: true });
    const canonical = runCanonicalCheck({ root, noWrite: true });
    const answerValidation = runAnswerValidate({ root });

    return {
        schema_version: 'quality_report.v1',
        ok: indexCheck.ok && taxonomy.unknown_count === 0 && canonical.ok && answerValidation.ok,
        generated_at: date,
        questions: {
            total_count: questions.length,
            valid_count: validQuestions.length,
            invalid_count: questions.length - validQuestions.length,
            assigned_question_rows: assignedQuestions.length,
            domain_l1_top: topItems(questions, (question) => question.domain?.l1 || '其他', 10),
        },
        canonical: {
            record_count: canonicalRecords.length,
            assigned_question_rows: canonical.assigned_question_rows,
            p0_count: p0Canonical.length,
            p0_missing_answer_count: p0MissingAnswers.length,
            answer_status_counts: countBy(canonicalRecords, (record) => record.answer_status || 'missing'),
            priority_counts: countBy(canonicalRecords, (record) => record.review_priority || 'P2'),
            missing_p0: p0MissingAnswers.map((record) => ({
                canonical_id: record.canonical_id,
                canonical_title: record.canonical_title,
                frequency: record.frequency,
                primary_domain: record.primary_domain,
            })),
            check: {
                ok: canonical.ok,
                duplicate_question_id_count: canonical.duplicate_question_id_count,
                missing_question_id_count: canonical.missing_question_id_count,
                binding_mismatch_count: canonical.binding_mismatch_count,
                orphan_binding_count: canonical.orphan_binding_count,
                unlisted_binding_count: canonical.unlisted_binding_count,
                suspected_duplicate_count: canonical.suspected_duplicate_count,
            },
        },
        answers: {
            answer_count: answers.rows.length,
            status_counts: countBy(answers.rows, (answer) => answer.status),
            validation_ok: answerValidation.ok,
            validation_error_count: answerValidation.error_count,
            read_error_count: answers.errors.length,
            read_errors: answers.errors,
        },
        review: {
            progress_count: reviewItems.length,
            status_counts: countBy(reviewItems, (item) => item.status || 'new'),
            due_count: dueItems.length,
            reviewed_count: reviewItems.filter((item) => Number(item.review_count || 0) > 0).length,
            weak_count: reviewItems.filter((item) => item.status === 'weak' || Number(item.mistake_count || 0) > 0).length,
            mastered_count: reviewItems.filter((item) => item.status === 'mastered').length,
        },
        taxonomy: {
            ok: taxonomy.ok,
            strict_ok: taxonomy.strict_ok,
            legacy_alias_count: taxonomy.legacy_alias_count,
            unknown_count: taxonomy.unknown_count,
            top_legacy_aliases: topItems(taxonomy.legacy_aliases || [], (item) =>
                `${item.field}: ${item.reason}: ${JSON.stringify(item.value)} -> ${JSON.stringify(item.normalized_value)}`,
                20
            ),
            top_unknown: topItems(taxonomy.unknown || [], (item) =>
                `${item.field}: ${JSON.stringify(item.value)}`,
                20
            ),
        },
        indexes: {
            ok: indexCheck.ok,
            changed_files: indexCheck.diffs.map((filePath) => path.relative(root, filePath)),
            entity_keys: indexes.entity.total_keys,
            company_keys: indexes.company.total_keys,
            domain_l1_keys: indexes.domain.total_l1_keys,
            domain_l2_keys: indexes.domain.total_l2_keys,
            hotspot_count: indexes.hotspot.total_hotspots,
        },
        issues: {
            link_count: issueLinks.items.length,
            linked_ready_count: issueLinks.items.filter((item) => item.answer_status === 'ready').length,
            linked_p0_count: issueLinks.items.filter((item) => item.priority === 'P0' || (item.labels || []).includes('priority:P0')).length,
        },
        next_actions: recommendNextActions({
            p0MissingAnswers,
            canonicalRecords,
            assignedQuestions,
            taxonomy,
            reviewItems,
        }),
    };
}

function recommendNextActions(context) {
    const actions = [];
    if (context.p0MissingAnswers.length) {
        actions.push({
            priority: 'P0',
            action: 'answer missing --priority P0',
            reason: `${context.p0MissingAnswers.length} P0 canonical answers are still missing`,
        });
    }
    if (context.assignedQuestions.length < 200) {
        actions.push({
            priority: 'P0',
            action: 'canonical suggest --hotspot --limit 50',
            reason: `assigned question rows are ${context.assignedQuestions.length}, below the 200 row near-term target`,
        });
    }
    if (context.taxonomy.legacy_alias_count > 0) {
        actions.push({
            priority: 'P1',
            action: 'review top taxonomy legacy aliases',
            reason: `${context.taxonomy.legacy_alias_count} taxonomy legacy aliases remain`,
        });
    }
    if (!context.reviewItems.some((item) => Number(item.review_count || 0) > 0)) {
        actions.push({
            priority: 'P1',
            action: 'review today / review mark',
            reason: 'review progress has not recorded real usage yet',
        });
    }
    return actions;
}

function renderMarkdown(report) {
    const lines = [
        '# Quality Report',
        '',
        `Generated: ${report.generated_at}`,
        '',
        `Overall: ${report.ok ? 'OK' : 'NEEDS ATTENTION'}`,
        '',
        '## Summary',
        '',
        '| Area | Metric | Value |',
        '|---|---:|---:|',
        `| Questions | total | ${report.questions.total_count} |`,
        `| Questions | valid | ${report.questions.valid_count} |`,
        `| Canonical | records | ${report.canonical.record_count} |`,
        `| Canonical | assigned rows | ${report.canonical.assigned_question_rows} |`,
        `| Answers | files | ${report.answers.answer_count} |`,
        `| Answers | P0 missing | ${report.canonical.p0_missing_answer_count} |`,
        `| Review | progress records | ${report.review.progress_count} |`,
        `| Review | reviewed | ${report.review.reviewed_count} |`,
        `| Taxonomy | legacy aliases | ${report.taxonomy.legacy_alias_count} |`,
        `| Indexes | changed files | ${report.indexes.changed_files.length} |`,
        '',
        '## P0 Missing Answers',
        '',
        '| canonical_id | frequency | domain | title |',
        '|---|---:|---|---|',
        ...report.canonical.missing_p0.map((item) =>
            `| ${item.canonical_id} | ${item.frequency || 0} | ${item.primary_domain?.l1 || ''}/${item.primary_domain?.l2 || ''} | ${item.canonical_title} |`
        ),
        '',
        '## Next Actions',
        '',
        '| priority | action | reason |',
        '|---|---|---|',
        ...report.next_actions.map((item) => `| ${item.priority} | ${item.action} | ${item.reason} |`),
        '',
        '## Taxonomy Legacy Aliases',
        '',
        '| value | count |',
        '|---|---:|',
        ...report.taxonomy.top_legacy_aliases.slice(0, 20).map((item) => `| ${item.value.replace(/\|/g, '\\|')} | ${item.count} |`),
        '',
    ];
    return `${lines.join('\n')}\n`;
}

function writeReports(report, options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    writeJson(paths.jsonReport, report);
    ensureDir(path.dirname(paths.markdownReport));
    fs.writeFileSync(paths.markdownReport, renderMarkdown(report), 'utf8');
    return {
        json_report: path.relative(root, paths.jsonReport),
        markdown_report: path.relative(root, paths.markdownReport),
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = {};
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (arg === '--root') options.root = path.resolve(args[++index]);
        else if (arg === '--date') options.date = args[++index];
        else if (arg.startsWith('--') && applyGlobalBooleanOption(options, arg.replace(/^--/, ''))) continue;
        else if (arg === '--help' || arg === 'help') options.help = true;
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js report <quality> [options]',
        '',
        'Commands:',
        '  quality      Summarize questions, canonical, answers, review, taxonomy, indexes, and issues',
        '',
        'Options:',
        '  --root <path>  Override repository root',
        '  --date <date>  Override report date',
        '  --noWrite      Print only; do not write report files or run manifest',
        '  --noManifest   Do not write the run manifest',
    ].join('\n'));
}

function main(argv = process.argv) {
    const { command, options } = parseArgs(argv);
    if (!command || command === 'help' || options.help) {
        printHelp();
        return 0;
    }
    try {
        if (command !== 'quality') throw new Error(`Unknown report command: ${command}`);
        const report = buildQualityReport(options);
        const output = options.noWrite ? null : writeReports(report, options);
        const result = {
            ...report,
            output,
        };
        writeRunManifest(options.root ? path.resolve(options.root) : DEFAULT_ROOT, 'report_quality', result, options);
        console.log(JSON.stringify(result, null, 2));
        return result.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    buildQualityReport,
    renderMarkdown,
    writeReports,
    main,
};
