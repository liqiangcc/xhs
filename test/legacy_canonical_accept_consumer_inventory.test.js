'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');
const INVENTORY_PATH = path.join(
    ROOT,
    'docs',
    'refactor',
    '11_legacy_canonical_accept_consumer_inventory.json',
);

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

function listFiles(target) {
    const absolute = path.join(ROOT, target);
    if (!fs.existsSync(absolute)) return [];
    const stat = fs.statSync(absolute);
    if (stat.isFile()) return [target];

    const out = [];
    for (const entry of fs.readdirSync(absolute, { withFileTypes: true })) {
        const relative = path.join(target, entry.name).split(path.sep).join('/');
        if (entry.isDirectory()) out.push(...listFiles(relative));
        else if (entry.isFile()) out.push(relative);
    }
    return out;
}

function inventoryPaths(inventory) {
    return new Set([
        ...inventory.active_blockers.map((item) => item.path),
        ...inventory.runtime_compatibility.map((item) => item.path),
        ...inventory.compatibility_aliases.map((item) => item.path),
        ...inventory.checked_in_legacy_data.map((item) => item.path),
        ...inventory.current_policy_references,
        ...inventory.historical_references,
    ]);
}

function carriesStrongLegacyMarker(body) {
    const markers = [
        'canonical_candidates.v1',
        'canonical_candidates.json',
        'canonical accept',
        'LegacyCanonicalCandidateRepository',
        'legacyCandidateRepository',
        'canonical-candidate:',
        '--candidate-id',
        'accepted_candidate_id',
    ];
    return markers.some((marker) => body.includes(marker));
}

test('legacy canonical accept inventory matches repository-local runtime and documentation references', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const classified = inventoryPaths(inventory);
    const scanTargets = [
        'README.md',
        'AGENTS.md',
        '.github',
        '.agents',
        'scripts',
        'src',
        'docs/refactor',
        'docs/adr',
        'review/plans',
        'data/manifests/canonical',
    ];
    const ignored = new Set([
        'docs/refactor/11_legacy_canonical_accept_consumer_inventory.json',
        'docs/refactor/11_legacy_canonical_accept_consumer_inventory.md',
    ]);
    const observed = [];

    for (const target of scanTargets) {
        for (const relativePath of listFiles(target)) {
            if (ignored.has(relativePath)) continue;
            if (!/\.(?:js|md|json|ya?ml)$/.test(relativePath)) continue;
            const body = read(relativePath);
            if (carriesStrongLegacyMarker(body)) observed.push(relativePath);
        }
    }

    const unclassified = observed.filter((relativePath) => !classified.has(relativePath));
    assert.deepEqual(
        unclassified,
        [],
        `Unclassified legacy canonical accept references: ${unclassified.join(', ')}`,
    );

    assert.equal(inventory.retirement_status, 'blocked_by_active_documentation');
    assert.deepEqual(
        inventory.active_blockers.map((item) => item.path),
        ['docs/refactor/08_content_building_goals.md'],
    );
});

test('checked-in legacy canonical candidate manifest is an empty historical snapshot', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const item = inventory.checked_in_legacy_data.find(
        (entry) => entry.path === 'data/manifests/canonical/canonical_candidates.json',
    );
    assert.ok(item);

    const manifest = JSON.parse(read(item.path));
    assert.equal(manifest.schema_version, 'canonical_candidates.v1');
    assert.equal(manifest.candidate_count, 0);
    assert.deepEqual(manifest.candidates, []);
    assert.equal(item.candidate_count, manifest.candidate_count);
    assert.equal(item.state, 'empty_historical_snapshot');
});

test('legacy runtime concurrency bridge is explicit and current Suggest automation cannot regenerate it', () => {
    const canonicalRepositories = read('src/infrastructure/filesystem/canonical-repositories.js');
    const canonicalCli = read('scripts/commands/canonical.js');
    const workflow = read('.github/workflows/xhs-manage.yml');

    assert.match(canonicalRepositories, /legacy-canonical-candidate-repositories/);
    assert.match(canonicalRepositories, /Legacy compatibility only/);
    assert.doesNotMatch(
        canonicalRepositories,
        /require\(['"]\.\/canonical-candidate-repositories['"]\)/,
    );

    assert.doesNotMatch(canonicalCli, /canonical_candidates\.json/);
    assert.doesNotMatch(workflow, /data\/manifests\/canonical\/canonical_candidates\.json/);
    assert.match(workflow, /data\/manifests\/dedup\/relation_candidate_queues\.json/);
});

test('generic candidate_id in canonical boundary audit is not treated as legacy Accept input', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const boundaryAudit = inventory.unrelated_candidate_id_models.find(
        (item) => item.path === 'scripts/content/audit_canonical_boundaries.js',
    );
    assert.ok(boundaryAudit);

    const source = read(boundaryAudit.path);
    assert.match(source, /canonical_boundary_candidate\.v1/);
    assert.match(source, /candidate_id/);
    assert.doesNotMatch(source, /canonical_candidates\.v1/);
    assert.doesNotMatch(source, /canonical accept/);
});
