#!/usr/bin/env node
/**
 * Check whether analysis files already exist under review/ans.
 *
 * Usage:
 *   node scripts/check_existing_analyses.js --id <question_id>
 *   node scripts/check_existing_analyses.js --ids <id1,id2,id3>
 *
 * Stdout always prints JSON for easy agent consumption.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const ANS_DIR = path.resolve(__dirname, '..', 'review', 'ans');

function parseArgs(argv) {
    const args = argv.slice(2);
    const opts = {};

    for (let index = 0; index < args.length; index++) {
        const current = args[index];
        if (!current.startsWith('--')) {
            continue;
        }
        const key = current.slice(2);
        const value = args[index + 1];
        opts[key] = value;
        index++;
    }

    return opts;
}

function normalizeIds(opts) {
    if (opts.id) {
        return [String(opts.id).trim()].filter(Boolean);
    }

    if (opts.ids) {
        return String(opts.ids)
            .split(',')
            .map(id => id.trim())
            .filter(Boolean);
    }

    return [];
}

function buildFilePath(questionId) {
    return path.join(ANS_DIR, `analysis_${questionId}.md`);
}

function main() {
    const opts = parseArgs(process.argv);
    const questionIds = normalizeIds(opts);

    if (questionIds.length === 0) {
        console.error('Usage: node scripts/check_existing_analyses.js --id <question_id> | --ids <id1,id2,id3>');
        process.exit(1);
    }

    const results = questionIds.map(questionId => {
        const filePath = buildFilePath(questionId);
        const exists = fs.existsSync(filePath);
        return {
            question_id: questionId,
            exists,
            path: path.relative(path.resolve(__dirname, '..'), filePath).replace(/\\/g, '/'),
        };
    });

    const existing = results.filter(item => item.exists).map(item => item.question_id);
    const missing = results.filter(item => !item.exists).map(item => item.question_id);

    console.log(JSON.stringify({
        total: results.length,
        existing_count: existing.length,
        missing_count: missing.length,
        existing,
        missing,
        results,
    }, null, 2));
}

main();
