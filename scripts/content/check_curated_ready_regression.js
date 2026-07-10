#!/usr/bin/env node
'use strict';

const path = require('path');
const { listAnswerFiles, readAnswerFile } = require('../lib/answer_store');
const { readJson, writeJson } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

function parseArgs(argv) {
    const options = { noWrite: false };
    for (let index = 2; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--noWrite' || arg === '--check') options.noWrite = true;
        else if (arg === '--write-floor') options.writeFloor = true;
        else if (arg === '--reason') options.reason = argv[++index];
        else if (arg === '--root') options.root = path.resolve(argv[++index]);
        else throw new Error(`Unknown option: ${arg}`);
    }
    return options;
}

function curatedReadyCount(root) {
    return listAnswerFiles({ answersDir: path.join(root, 'review', 'answers') })
        .map(readAnswerFile)
        .filter((answer) => answer.metadata.status === 'ready' && answer.metadata.quality_tier === 'curated')
        .length;
}

function main(argv = process.argv) {
    try {
        const options = parseArgs(argv);
        const root = options.root || ROOT;
        const floorPath = path.join(root, 'data', 'manifests', 'quality', 'curated_ready_floor.json');
        const current = curatedReadyCount(root);
        if (options.writeFloor) {
            if (!options.reason) throw new Error('--write-floor requires --reason');
            const value = { schema_version: 'curated_ready_floor.v1', curated_ready_floor: current, established_at: '2026-07-11', reason: options.reason };
            if (!options.noWrite) writeJson(floorPath, value);
            console.log(JSON.stringify({ ok: true, wrote: !options.noWrite, ...value }, null, 2));
            return 0;
        }
        const baseline = readJson(floorPath);
        const report = { schema_version: 'curated_ready_regression.v1', ok: current >= baseline.curated_ready_floor, current_curated_ready: current, floor: baseline.curated_ready_floor, floor_reason: baseline.reason };
        console.log(JSON.stringify(report, null, 2));
        return report.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) process.exitCode = main();

module.exports = { curatedReadyCount, main };
