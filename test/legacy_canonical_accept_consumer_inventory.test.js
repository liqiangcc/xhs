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
const ACTIVE_ROOT_TASK = 'tasks/TASK-20260711-0313-long-tail-answer-quality.md';

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
        ...inventory.test_support_compatibility.map((item) => item.path),
        ...inventory.compatibility_aliases.map((item) => item.path),
        ...inventory.shared_current_dependencies.map((item) => item.path),
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
        'package.json',
        '.github',
        '.agents',
        'tasks',
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

    assert.equal(
        inventory.retirement_status,
        'ready_for_runtime_removal_with_unobservable_external_risk',
    );
    assert.deepEqual(inventory.active_blockers, []);
    assert.equal(inventory.summary.active_manual_procedure_blocker_count, 0);
    assert.equal(inventory.summary.observable_github_search_completed, true);
    assert.equal(inventory.summary.observable_github_external_consumer_count, 0);
    assert.equal(inventory.summary.external_consumers_fully_observable, false);
    assert.equal(inventory.summary.source_deprecation_marked, true);
});

test('recorded GitHub consumer search distinguishes observable zero matches from unobservable external risk', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const search = inventory.external_consumer_search;

    assert.equal(search.result, 'no_observable_project_specific_external_consumers');
    assert.equal(search.checked_at, '2026-08-14');
    assert.ok(search.queries.length >= 5);
    assert.ok(search.queries.every((item) => item.external_match_count === 0));
    assert.equal(search.generic_name_collision.query, 'canonical_candidates.json');
    assert.equal(search.generic_name_collision.external_matches_exist, true);
    assert.ok(search.limitations.some((item) => /local shell scripts/i.test(item)));
    assert.ok(search.limitations.some((item) => /does not prove absolute absence/i.test(item)));
});

test('legacy Accept entry points are source-deprecated without adding runtime warning behavior', () => {
    const canonicalCli = read('scripts/commands/canonical.js');
    const acceptApplication = read('src/application/canonical/accept-canonical.js');
    const legacyPort = read('src/ports/repositories/legacy-canonical-candidate-repository.js');
    const presenter = read('src/interfaces/cli/canonical-accept-presenter.js');

    assert.match(canonicalCli, /@deprecated[\s\S]*async function runAccept/);
    assert.match(acceptApplication, /@deprecated[\s\S]*function createAcceptCanonicalUseCase/);
    assert.match(legacyPort, /@deprecated[\s\S]*function assertLegacyCanonicalCandidateRepository/);
    assert.match(presenter, /@deprecated[\s\S]*function presentCanonicalAcceptResult/);

    assert.doesNotMatch(canonicalCli, /console\.warn/);
    assert.doesNotMatch(acceptApplication, /console\.warn/);
    assert.doesNotMatch(legacyPort, /console\.warn/);
    assert.doesNotMatch(presenter, /console\.warn/);
});

test('content-building execution no longer routes new relations through legacy Accept', () => {
    const contentGoals = read('docs/refactor/08_content_building_goals.md');

    assert.match(contentGoals, /canonical suggest/);
    assert.match(contentGoals, /dedup decide/);
    assert.match(contentGoals, /dedup apply/);
    assert.match(contentGoals, /10_current_dedup_canonical_operations\.md/);
    assert.doesNotMatch(contentGoals, /canonical accept \/ merge \/ split/);
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

test('active package scripts, workflows, and in-progress root task do not depend on legacy Accept', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const packageJson = read('package.json');
    const rootTask = read(ACTIVE_ROOT_TASK);
    const workflowDir = path.join(ROOT, '.github', 'workflows');

    assert.doesNotMatch(packageJson, /canonical accept|canonical_candidates(?:\.v1|\.json)/);
    assert.match(rootTask, /Status:\s*`in_progress`/);
    assert.doesNotMatch(rootTask, /canonical accept|canonical_candidates(?:\.v1|\.json)/);

    for (const name of fs.readdirSync(workflowDir).filter((item) => /\.ya?ml$/.test(item))) {
        const workflow = fs.readFileSync(path.join(workflowDir, name), 'utf8');
        assert.doesNotMatch(workflow, /canonical accept/);
        assert.doesNotMatch(workflow, /data\/manifests\/canonical\/canonical_candidates\.json/);
    }

    assert.equal(inventory.summary.package_scripts_invoke_legacy_accept, false);
    assert.equal(inventory.summary.in_progress_root_task_invokes_legacy_accept, false);
    assert.equal(inventory.summary.github_actions_generates_legacy_manifest, false);
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

test('in-memory canonical candidate support is classified as test compatibility, not production wiring', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const item = inventory.test_support_compatibility.find(
        (entry) => entry.path === 'src/infrastructure/in-memory/canonical-adapters.js',
    );
    assert.ok(item);

    const adapter = read(item.path);
    const bootstrap = read('src/bootstrap/create-application.js');
    assert.match(adapter, /canonical-candidate:/);
    assert.match(adapter, /canonicalCandidateRepository/);
    assert.doesNotMatch(bootstrap, /in-memory\/canonical-adapters/);
});

test('shared accept policy remains current Canonicalization SSOT and is not a legacy deletion target', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    const policy = inventory.shared_current_dependencies.find(
        (entry) => entry.path === 'src/domain/canonical/accept-policy.js',
    );
    const projection = inventory.shared_current_dependencies.find(
        (entry) => entry.path === 'src/domain/canonical/question-group-projection-policy.js',
    );
    assert.ok(policy);
    assert.ok(projection);

    assert.match(read(policy.path), /function acceptCanonicalCandidate/);
    assert.match(
        read(projection.path),
        /require\(['"]\.\/accept-policy['"]\)/,
    );
    assert.match(read(projection.path), /acceptCanonicalCandidate\(/);
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
