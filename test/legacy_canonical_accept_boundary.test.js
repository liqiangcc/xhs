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

test('canonical accept is no longer exposed by the Interface layer', () => {
    const canonicalCli = source('scripts/commands/canonical.js');
    const topLevelCli = source('scripts/xhs.js');

    assert.doesNotMatch(canonicalCli, /canonical-accept-presenter/);
    assert.doesNotMatch(canonicalCli, /function runAccept/);
    assert.doesNotMatch(canonicalCli, /command === ['"]accept['"]/);
    assert.doesNotMatch(canonicalCli, /runAccept,/);
    assert.doesNotMatch(canonicalCli, /suggest\|accept/);
    assert.doesNotMatch(topLevelCli, /canonical accept/);
    assert.equal(fs.existsSync(path.join(ROOT, 'src', 'interfaces', 'cli', 'canonical-accept-presenter.js')), false);
});

test('legacy Accept Application and candidate repository layer are removed while CAS compatibility remains explicit', () => {
    const bootstrap = source('src/bootstrap/create-application.js');
    const canonicalRepositories = source('src/infrastructure/filesystem/canonical-repositories.js');
    const casHelper = source('src/infrastructure/filesystem/legacy-canonical-candidate-revision.js');
    const mutationPlan = source('src/application/canonical/mutation-plan.js');

    assert.doesNotMatch(bootstrap, /createAcceptCanonicalUseCase/);
    assert.doesNotMatch(bootstrap, /legacy-canonical-candidate-repositories/);
    assert.doesNotMatch(bootstrap, /createFsLegacyCanonicalCandidateRepository/);
    assert.doesNotMatch(bootstrap, /legacyCandidateRepository/);
    assert.doesNotMatch(bootstrap, /\baccept\s*,/);

    for (const relativePath of [
        'src/application/canonical/accept-canonical.js',
        'src/ports/repositories/legacy-canonical-candidate-repository.js',
        'src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js',
        'src/ports/repositories/canonical-candidate-repository.js',
        'src/infrastructure/filesystem/canonical-candidate-repositories.js',
    ]) {
        assert.equal(fs.existsSync(path.join(ROOT, relativePath)), false, relativePath);
    }

    assert.match(canonicalRepositories, /legacy-canonical-candidate-revision/);
    assert.doesNotMatch(canonicalRepositories, /legacy-canonical-candidate-repositories/);
    assert.match(canonicalRepositories, /canonical-candidate:/);
    assert.match(casHelper, /revisionForLegacyCandidateResource/);
    assert.doesNotMatch(casHelper, /createFsLegacyCanonicalCandidateRepository/);
    assert.match(mutationPlan, /['"]accept['"]/);
});

test('canonical_candidates.v1 knowledge is confined to the remaining CAS compatibility helper', () => {
    const srcRoot = path.join(ROOT, 'src');
    const allowed = new Set([
        'src/infrastructure/filesystem/legacy-canonical-candidate-revision.js',
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
