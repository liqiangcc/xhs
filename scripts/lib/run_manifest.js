'use strict';

const path = require('path');
const { writeJson } = require('./io');
const { defaultDate } = require('./date');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function safeName(value) {
    return String(value || 'command')
        .toLowerCase()
        .replace(/[^a-z0-9_\-]+/g, '_')
        .replace(/^_+|_+$/g, '') || 'command';
}

function writeRunManifest(root, command, result, options = {}) {
    if (options.noWrite || options.noManifest) return null;
    const repoRoot = root || DEFAULT_ROOT;
    const filePath = path.join(repoRoot, 'data', 'manifests', 'runs', `latest_${safeName(command)}.json`);
    const manifest = {
        schema_version: 'pipeline_run_manifest.v1',
        generated_at: defaultDate(options),
        command,
        ok: result?.ok !== false,
        result,
    };
    writeJson(filePath, manifest);
    return filePath;
}

module.exports = {
    writeRunManifest,
};
