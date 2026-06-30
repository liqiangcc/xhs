#!/usr/bin/env node
'use strict';

const path = require('path');
const { loadQuestions } = require('./lib/question_store');
const { loadCanonicalQuestions } = require('./lib/canonical_store');
const { buildIndexes, writeIndexes, checkIndexes } = require('./lib/index_store');
const { writeRunManifest } = require('./lib/run_manifest');
const { applyGlobalBooleanOption } = require('./lib/cli_options');

const DEFAULT_ROOT = path.resolve(__dirname, '..');

function parseArgs(argv) {
    const args = argv.slice(2);
    const options = { check: false };
    for (let index = 0; index < args.length; index++) {
        const arg = args[index];
        if (arg === '--check' || arg === 'check') options.check = true;
        else if (arg === '--root') options.root = path.resolve(args[++index]);
        else if (arg === '--questions') options.questionsPath = path.resolve(args[++index]);
        else if (arg === '--index-dir') options.indexDir = path.resolve(args[++index]);
        else if (arg.startsWith('--') && applyGlobalBooleanOption(options, arg.replace(/^--/, ''))) continue;
        else if (arg === '--help' || arg === 'help') options.help = true;
    }
    return options;
}

function printHelp() {
    console.log([
        'Usage: node scripts/build_index.js [--check]',
        '',
        'Options:',
        '  --check             Regenerate in memory and fail if index files differ',
        '  --questions <path>  Override questions.jsonl path',
        '  --index-dir <path>  Override output index directory',
        '  --root <path>       Override repository root',
        '  --noWrite           Do not write run manifests',
        '  --noManifest        Do not write the run manifest',
    ].join('\n'));
}

function main(argv = process.argv) {
    const options = parseArgs(argv);
    if (options.help) {
        printHelp();
        return 0;
    }

    const root = options.root || DEFAULT_ROOT;
    const questionsPath = options.questionsPath || path.join(root, 'data', 'questions', 'questions.jsonl');
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const indexDir = options.indexDir || path.join(root, 'data', 'indexes');
    const questions = loadQuestions({ filePath: questionsPath });
    const canonicalQuestions = loadCanonicalQuestions({ filePath: canonicalPath });
    const indexes = buildIndexes(questions, { canonicalQuestions });

    if (options.check) {
        const check = checkIndexes(indexes, indexDir);
        if (!check.ok) {
            console.error(JSON.stringify({
                ok: false,
                changed_files: check.diffs.map((filePath) => path.relative(root, filePath)),
            }, null, 2));
            return 1;
        }
        const result = {
            ok: true,
            question_count: questions.length,
            entity_keys: indexes.entity.total_keys,
            company_keys: indexes.company.total_keys,
            domain_l1_keys: indexes.domain.total_l1_keys,
            hotspots: indexes.hotspot.total_hotspots,
        };
        writeRunManifest(root, 'index_check', result, options);
        console.log(JSON.stringify(result, null, 2));
        return 0;
    }

    writeIndexes(indexes, indexDir);
    const result = {
        ok: true,
        question_count: questions.length,
        entity_keys: indexes.entity.total_keys,
        company_keys: indexes.company.total_keys,
        domain_l1_keys: indexes.domain.total_l1_keys,
        domain_l2_keys: indexes.domain.total_l2_keys,
        hotspots: indexes.hotspot.total_hotspots,
    };
    writeRunManifest(root, 'index_build', result, options);
    console.log(JSON.stringify(result, null, 2));
    return 0;
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    main,
};
