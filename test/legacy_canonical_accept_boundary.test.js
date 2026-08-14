'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

function source(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

function listJavaScriptFiles(dir) {
    if (!fs.existsSync(dir)) return [];
    const out = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) out.push(...listJavaScriptFiles(fullPath));
        else if (entry.isFile() && entry.name.endsWith('.js')) out.push(fullPath);
    }
    return out.sort();
}

test('current Suggest interfaces and Actions cannot regenerate legacy canonical candidate manifests', () => {
    const canonicalCli = source('scripts/commands/canonical.js');
    const workflow = source('.github/workflows/xhs-manage.yml');

    assert.doesNotMatch(canonicalCli, /canonical_candidates\.v1/);
    assert.doesNotMatch(canonicalCli, /canonical_candidates\.json/);
    assert.doesNotMatch(canonicalCli, /candidateManifest/);
    assert.doesNotMatch(canonicalCli, /buildCandidate/);
    assert.doesNotMatch(canonicalCli, /suggestFromHotspot/);

    assert.match(workflow, /data\/manifests\/dedup\/relation_candidate_queues\.json/);
    assert.match(workflow, /dedup-relation-candidates/);
    assert.doesNotMatch(workflow, /data\/manifests\/canonical\/canonical_candidates\.json/);
    assert.doesNotMatch(workflow, /name:\s*canonical-candidates/);
});

test('Production Root and Accept name historical candidate input as legacy compatibility', () => {
    const bootstrap = source('src/bootstrap/create-application.js');
    const accept = source('src/application/canonical/accept-canonical.js');
    const oldPort = source('src/ports/repositories/canonical-candidate-repository.js');
    const oldAdapter = source('src/infrastructure/filesystem/canonical-candidate-repositories.js');

    assert.match(bootstrap, /legacy-canonical-candidate-repositories/);
    assert.match(bootstrap, /createFsLegacyCanonicalCandidateRepository/);
    assert.match(bootstrap, /legacyCandidateRepository/);
    assert.doesNotMatch(
        bootstrap,
        /require\(['"]\.\.\/infrastructure\/filesystem\/canonical-candidate-repositories['"]\)/,
    );

    assert.match(accept, /legacy-canonical-candidate-repository/);
    assert.match(accept, /assertLegacyCanonicalCandidateRepository/);
    assert.match(accept, /dependencies\.legacyCandidateRepository/);

    assert.match(oldPort, /Deprecated compatibility re-export/);
    assert.match(oldPort, /legacy-canonical-candidate-repository/);
    assert.match(oldAdapter, /Deprecated compatibility re-export/);
    assert.match(oldAdapter, /legacy-canonical-candidate-repositories/);
});

test('canonical_candidates.v1 knowledge is confined to explicit compatibility source modules', () => {
    const srcRoot = path.join(ROOT, 'src');
    const allowed = new Set([
        'src/ports/repositories/legacy-canonical-candidate-repository.js',
        'src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js',
    ]);
    const offenders = [];

    for (const filePath of listJavaScriptFiles(srcRoot)) {
        const body = fs.readFileSync(filePath, 'utf8');
        if (!body.includes('canonical_candidates.v1')) continue;
        const relative = path.relative(ROOT, filePath).split(path.sep).join('/');
        if (!allowed.has(relative)) offenders.push(relative);
    }

    assert.deepEqual(offenders, []);
});

test('legacy filesystem path is explicit while the old candidateManifest name remains alias-only', () => {
    const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
    const paths = createCanonicalFsPaths('/tmp/xhs-legacy-boundary');

    assert.equal(paths.legacyCandidateManifest, paths.candidateManifest);
    assert.match(paths.legacyCandidateManifest, /canonical_candidates\.json$/);
});
