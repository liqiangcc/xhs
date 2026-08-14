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

test('legacy canonical accept inventory matches the fully retired repository-local state', () => {
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
        'fully_retired_repository_local_with_unobservable_external_risk',
    );
    assert.deepEqual(inventory.active_blockers, []);
    assert.deepEqual(inventory.runtime_compatibility, []);
    assert.deepEqual(inventory.test_support_compatibility, []);
    assert.deepEqual(inventory.checked_in_legacy_data, []);
    assert.equal(inventory.summary.active_manual_procedure_blocker_count, 0);
    assert.equal(inventory.summary.observable_github_search_completed, true);
    assert.equal(inventory.summary.observable_github_external_consumer_count, 0);
    assert.equal(inventory.summary.external_consumers_fully_observable, false);
    assert.equal(inventory.summary.interface_runtime_removed, true);
    assert.equal(inventory.summary.production_composition_root_accept_removed, true);
    assert.equal(inventory.summary.accept_application_removed, true);
    assert.equal(inventory.summary.legacy_candidate_repository_layer_removed, true);
    assert.equal(inventory.summary.legacy_candidate_cas_bridge_removed, true);
    assert.equal(inventory.summary.accept_mutation_operation_removed, true);
    assert.equal(inventory.summary.in_memory_candidate_test_support_removed, true);
    assert.equal(inventory.summary.legacy_manifest_path_removed, true);
    assert.equal(inventory.summary.checked_in_legacy_manifest_removed, true);
    assert.equal(inventory.summary.legacy_accept_repository_local_fully_retired, true);
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

test('legacy Accept execution and mutation contracts remain removed', () => {
    const canonicalCli = read('scripts/commands/canonical.js');
    const topLevelCli = read('scripts/xhs.js');
    const bootstrap = read('src/bootstrap/create-application.js');
    const canonicalRepositories = read('src/infrastructure/filesystem/canonical-repositories.js');
    const mutationPlan = read('src/application/canonical/mutation-plan.js');

    assert.doesNotMatch(canonicalCli, /function runAccept/);
    assert.doesNotMatch(canonicalCli, /canonical-accept-presenter/);
    assert.doesNotMatch(canonicalCli, /command === ['"]accept['"]/);
    assert.doesNotMatch(topLevelCli, /canonical accept/);
    assert.doesNotMatch(bootstrap, /createAcceptCanonicalUseCase/);
    assert.doesNotMatch(bootstrap, /createFsLegacyCanonicalCandidateRepository/);
    const app = require('../src/bootstrap/create-application').createApplication({ root: ROOT });
    assert.equal('accept' in app.canonical, false);

    for (const relativePath of [
        'src/interfaces/cli/canonical-accept-presenter.js',
        'src/application/canonical/accept-canonical.js',
        'src/ports/repositories/legacy-canonical-candidate-repository.js',
        'src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js',
        'src/ports/repositories/canonical-candidate-repository.js',
        'src/infrastructure/filesystem/canonical-candidate-repositories.js',
        'src/infrastructure/filesystem/legacy-canonical-candidate-revision.js',
    ]) {
        assert.equal(fs.existsSync(path.join(ROOT, relativePath)), false, relativePath);
    }

    assert.doesNotMatch(canonicalRepositories, /legacy-canonical-candidate-revision/);
    assert.doesNotMatch(canonicalRepositories, /legacy-canonical-candidate-repositories/);
    assert.doesNotMatch(canonicalRepositories, /canonical-candidate:/);
    assert.doesNotMatch(mutationPlan, /['"]accept['"]/);
    assert.match(mutationPlan, /['"]merge['"]/);
    assert.match(mutationPlan, /['"]split['"]/);
    assert.match(mutationPlan, /['"]canonicalize['"]/);
});

test('final legacy candidate filesystem path and checked-in manifest are removed', () => {
    const canonicalPathsSource = read('src/infrastructure/filesystem/canonical-paths.js');
    const paths = require('../src/infrastructure/filesystem/canonical-paths').createCanonicalFsPaths(ROOT);

    assert.doesNotMatch(canonicalPathsSource, /legacyCandidateManifest/);
    assert.doesNotMatch(canonicalPathsSource, /candidateManifest/);
    assert.doesNotMatch(canonicalPathsSource, /canonical_candidates\.json/);
    assert.equal(Object.prototype.hasOwnProperty.call(paths, 'legacyCandidateManifest'), false);
    assert.equal(Object.prototype.hasOwnProperty.call(paths, 'candidateManifest'), false);
    assert.equal(
        fs.existsSync(path.join(ROOT, 'data', 'manifests', 'canonical', 'canonical_candidates.json')),
        false,
    );
});

test('content-building execution no longer routes new relations through legacy Accept', () => {
    const contentGoals = read('docs/refactor/08_content_building_goals.md');

    assert.match(contentGoals, /canonical suggest/);
    assert.match(contentGoals, /dedup decide/);
    assert.match(contentGoals, /dedup apply/);
    assert.match(contentGoals, /10_current_dedup_canonical_operations\.md/);
    assert.doesNotMatch(contentGoals, /canonical accept \/ merge \/ split/);
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

test('filesystem Canonical revision router no longer accepts legacy candidate resources', () => {
    const canonicalRepositories = read('src/infrastructure/filesystem/canonical-repositories.js');
    const { revisionForResource } = require('../src/infrastructure/filesystem/canonical-repositories');
    const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');

    assert.doesNotMatch(canonicalRepositories, /canonical-candidate:/);
    assert.doesNotMatch(canonicalRepositories, /legacy-canonical-candidate-revision/);
    assert.throws(
        () => revisionForResource(createCanonicalFsPaths(ROOT), 'canonical-candidate:retired'),
        /Unsupported filesystem canonical resource/,
    );
});

test('in-memory Canonical adapter no longer carries legacy candidate test support', () => {
    const inventory = JSON.parse(fs.readFileSync(INVENTORY_PATH, 'utf8'));
    assert.deepEqual(inventory.test_support_compatibility, []);

    const adapter = read('src/infrastructure/in-memory/canonical-adapters.js');
    for (const retired of [
        /canonical-candidate:/,
        /canonicalCandidateRepository/,
        /candidateResource/,
        /upsertCandidate/,
        /seed\.candidates/,
        /\bcandidates:\s*\[\.\.\.candidates/,
    ]) {
        assert.doesNotMatch(adapter, retired);
    }

    assert.match(adapter, /canonicalRepository/);
    assert.match(adapter, /questionBindingRepository/);
    assert.match(adapter, /mutationStore/);
    assert.match(adapter, /upsertCanonical/);
    assert.match(adapter, /replaceQuestionBindings/);
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
