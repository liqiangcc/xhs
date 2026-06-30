'use strict';

const path = require('path');
const { writeJson } = require('./io');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';

function safeName(value) {
    return String(value || 'command')
        .toLowerCase()
        .replace(/[^a-z0-9_\-]+/g, '_')
        .replace(/^_+|_+$/g, '') || 'command';
}

function writeRunManifest(root, command, result, options = {}) {
    if (options.noManifest) return null;
    const repoRoot = root || DEFAULT_ROOT;
    const filePath = path.join(repoRoot, 'data', 'manifests', 'runs', `latest_${safeName(command)}.json`);
    const manifest = {
        schema_version: 'pipeline_run_manifest.v1',
        generated_at: options.date || DEFAULT_DATE,
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
