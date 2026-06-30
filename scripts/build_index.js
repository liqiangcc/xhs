#!/usr/bin/env node
'use strict';

const path = require('path');
const { loadQuestions } = require('./lib/question_store');
const { buildIndexes, writeIndexes, checkIndexes } = require('./lib/index_store');

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
    const indexDir = options.indexDir || path.join(root, 'data', 'indexes');
    const questions = loadQuestions({ filePath: questionsPath });
    const indexes = buildIndexes(questions);

    if (options.check) {
        const check = checkIndexes(indexes, indexDir);
        if (!check.ok) {
            console.error(JSON.stringify({
                ok: false,
                changed_files: check.diffs.map((filePath) => path.relative(root, filePath)),
            }, null, 2));
            return 1;
        }
        console.log(JSON.stringify({
            ok: true,
            question_count: questions.length,
            entity_keys: indexes.entity.total_keys,
            company_keys: indexes.company.total_keys,
            domain_l1_keys: indexes.domain.total_l1_keys,
            hotspots: indexes.hotspot.total_hotspots,
        }, null, 2));
        return 0;
    }

    writeIndexes(indexes, indexDir);
    console.log(JSON.stringify({
        ok: true,
        question_count: questions.length,
        entity_keys: indexes.entity.total_keys,
        company_keys: indexes.company.total_keys,
        domain_l1_keys: indexes.domain.total_l1_keys,
        domain_l2_keys: indexes.domain.total_l2_keys,
        hotspots: indexes.hotspot.total_hotspots,
    }, null, 2));
    return 0;
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    main,
};
