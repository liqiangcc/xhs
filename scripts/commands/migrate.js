'use strict';

const fs = require('fs');
const path = require('path');
const { main: buildQuestionsMain } = require('../migrate/build_questions_from_tagged');
const { readJson } = require('../lib/io');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function loadRegistry(root) {
    return readJson(path.join(root, 'config', 'migrations.json'), { migrations: [] });
}

function runStatus(options = {}) {
    const root = options.root || DEFAULT_ROOT;
    const registry = loadRegistry(root);
    const migrations = (registry.migrations || []).map((migration) => {
        const missingOutputs = (migration.outputs || []).filter((output) => !fs.existsSync(path.join(root, output)));
        return {
            id: migration.id,
            description: migration.description,
            applied: missingOutputs.length === 0,
            missing_outputs: missingOutputs,
        };
    });
    return {
        schema_version: 'migration_status.v1',
        ok: true,
        migration_count: migrations.length,
        migrations,
    };
}

function runMigration(root, id, options = {}) {
    if (id !== '001_build_questions') {
        throw new Error(`Unknown migration id: ${id}`);
    }
    const args = ['node', 'scripts/migrate/build_questions_from_tagged.js', '--root', root];
    if (options.check) args.push('--check');
    if (options.noWrite) args.push('--noWrite');
    if (options.noManifest) args.push('--noManifest');
    return buildQuestionsMain(args);
}

function parseOptions(args) {
    const options = {};
    for (let index = 0; index < args.length; index++) {
        if (args[index] === '--root') options.root = path.resolve(args[++index]);
        else if (args[index] === '--id') options.id = args[++index];
        else if (args[index] === '--check') options.check = true;
        else if (args[index].startsWith('--') && applyGlobalBooleanOption(options, args[index].replace(/^--/, ''))) continue;
    }
    return options;
}

function main(argv = process.argv) {
    const args = argv.slice(2);
    const subcommand = args[0];
    const options = parseOptions(args);
    const root = options.root || DEFAULT_ROOT;
    if (subcommand === 'build-questions') {
        return buildQuestionsMain(['node', 'scripts/migrate/build_questions_from_tagged.js', ...args.slice(1)]);
    }
    if (subcommand === 'status') {
        const result = runStatus({ root });
        writeRunManifest(root, 'migrate_status', result, options);
        console.log(JSON.stringify(result, null, 2));
        return 0;
    }
    if (subcommand === 'run') {
        const id = options.id || args[1];
        if (id === 'all') {
            const registry = loadRegistry(root);
            for (const migration of registry.migrations || []) {
                const code = runMigration(root, migration.id, { check: options.check });
                if (code !== 0) return code;
            }
            const result = {
                schema_version: 'migration_run_result.v1',
                ok: true,
                ran: (registry.migrations || []).map((migration) => migration.id),
                check: Boolean(options.check),
            };
            writeRunManifest(root, 'migrate_run_all', result, options);
            console.log(JSON.stringify(result, null, 2));
            return 0;
        }
        const code = runMigration(root, id, { check: options.check });
        const result = {
            schema_version: 'migration_run_result.v1',
            ok: code === 0,
            ran: [id],
            check: Boolean(options.check),
        };
        writeRunManifest(root, `migrate_run_${id}`, result, options);
        return code;
    }
    console.error('Usage: node scripts/xhs.js migrate <build-questions|status|run> [--check]');
    return 1;
}

module.exports = {
    runStatus,
    runMigration,
    main,
};
