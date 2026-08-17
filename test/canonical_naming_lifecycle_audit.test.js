'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

function exists(relativePath) {
    return fs.existsSync(path.join(ROOT, relativePath));
}

function listJavaScriptFiles(dir) {
    if (!fs.existsSync(dir)) return [];
    const files = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const filePath = path.join(dir, entry.name);
        if (entry.isDirectory()) files.push(...listJavaScriptFiles(filePath));
        else if (entry.isFile() && entry.name.endsWith('.js')) files.push(filePath);
    }
    return files;
}

test('Canonical lifecycle exposes the completed Resolve Prepare Plan Execute naming', () => {
    const resolveStage = read('src/application/canonical/resolve-question-group-canonicalization.js');
    const prepareStage = read('src/application/canonical/question-group-canonicalization-preparation-coordinator.js');
    const planMutationUseCase = read('src/application/canonical/plan-question-group-canonicalization-mutation.js');
    const mutationPlanFactory = read('src/application/canonical/question-group-canonicalization-mutation-plan.js');
    const executeStage = read('src/application/canonical/execute-question-group-canonicalization.js');

    assert.match(resolveStage, /createResolveQuestionGroupCanonicalizationUseCase/);
    assert.match(resolveStage, /return async function resolveQuestionGroupCanonicalization/);
    assert.match(resolveStage, /canonicalization_plan\.v1/);
    assert.match(resolveStage, /mutation_authorized:\s*false/);

    assert.match(prepareStage, /createQuestionGroupCanonicalizationPreparationCoordinator/);
    assert.match(prepareStage, /prepareQuestionGroupCanonicalizationMutation/);
    assert.match(prepareStage, /projectCanonicalQuestionGroup/);
    assert.match(prepareStage, /expected_revisions/);

    assert.match(planMutationUseCase, /createPlanQuestionGroupCanonicalizationMutationUseCase/);
    assert.match(planMutationUseCase, /createQuestionGroupCanonicalizationPreparationCoordinator/);
    assert.match(planMutationUseCase, /createQuestionGroupCanonicalizationMutationPlan/);
    assert.match(mutationPlanFactory, /createCanonicalMutationPlan/);
    assert.match(mutationPlanFactory, /operation:\s*'canonicalize'/);

    assert.match(executeStage, /createExecuteQuestionGroupCanonicalizationUseCase/);
    assert.match(executeStage, /mutationGateway\.preflight/);
    assert.match(executeStage, /mutationGateway\.commit/);
    assert.match(executeStage, /validateCanonicalizationCommit/);
});

test('CanonicalizationPlan remains separate from CanonicalMutationPlan', () => {
    const audit = read('docs/refactor/15_canonical_naming_lifecycle_audit.md');
    const projectionPolicy = read('src/domain/canonical/question-group-projection-policy.js');
    const mutationPlan = read('src/application/canonical/mutation-plan.js');

    assert.match(projectionPolicy, /canonicalization_plan\.v1/);
    assert.match(projectionPolicy, /mutation_authorized !== false/);
    assert.match(mutationPlan, /canonical_mutation_plan\.v1/);
    assert.match(audit, /CanonicalizationPlan[\s\S]*CanonicalMutationPlan/);
    assert.match(audit, /must remain separate/i);
});

test('Canonical mutation consistency boundary is the Gateway Port and filesystem Adapter', () => {
    const port = read('src/ports/canonical-mutation-gateway.js');
    const adapter = read('src/infrastructure/filesystem/file-canonical-mutation-gateway-adapter.js');

    assert.match(port, /assertCanonicalMutationGateway/);
    assert.match(port, /CanonicalMutationGateway/);
    assert.match(port, /\['preflight', 'commit'\]/);
    assert.match(adapter, /createFileCanonicalMutationGatewayAdapter/);
    assert.match(adapter, /function prepareTransaction/);
    assert.match(adapter, /function recoverPendingTransaction/);
    assert.match(adapter, /status: 'prepared'/);
    assert.match(adapter, /status: 'committed'/);
    assert.doesNotMatch(adapter, /createFsCanonicalMutationStore|FsCanonicalMutationStore|fs-canonical-mutation-store/);
});

test('old Canonical lifecycle files and public names are removed rather than aliased', () => {
    for (const relativePath of [
        'src/application/canonical/plan-canonicalize-question-group.js',
        'src/application/canonical/prepare-canonicalize-question-group.js',
        'src/application/canonical/plan-canonicalize-question-group-mutation-use-case.js',
        'src/application/canonical/plan-canonicalize-question-group-mutation.js',
        'src/application/canonical/canonicalize-question-group.js',
        'src/ports/canonical-mutation-store.js',
        'src/infrastructure/filesystem/fs-canonical-mutation-store.js',
    ]) {
        assert.equal(exists(relativePath), false, `${relativePath} must be removed`);
    }

    const bootstrap = read('src/bootstrap/create-application.js');
    assert.match(bootstrap, /resolveQuestionGroupCanonicalization/);
    assert.match(bootstrap, /planQuestionGroupCanonicalizationMutation/);
    assert.match(bootstrap, /executeQuestionGroupCanonicalization/);
    assert.doesNotMatch(bootstrap, /planQuestionGroup[,\n]|planQuestionGroupMutation|canonicalizeQuestionGroup/);

    const dedupApply = read('src/application/dedup/apply-relation-decision.js');
    assert.match(dedupApply, /resolveQuestionGroupCanonicalization/);
    assert.match(dedupApply, /executeQuestionGroupCanonicalization/);
});

test('active src JavaScript contains no retired lifecycle or CanonicalMutationStore symbols', () => {
    const retired = /createPlanCanonicalizeQuestionGroupUseCase|createPrepareCanonicalizeQuestionGroupUseCase|createPlanCanonicalizeQuestionGroupMutationUseCase|createCanonicalizeQuestionGroupMutationPlan|createCanonicalizeQuestionGroupUseCase|CanonicalMutationStore|createFsCanonicalMutationStore/;
    for (const filePath of listJavaScriptFiles(path.join(ROOT, 'src'))) {
        const body = fs.readFileSync(filePath, 'utf8');
        assert.doesNotMatch(body, retired, `${path.relative(ROOT, filePath)} contains a retired Canonical lifecycle name`);
    }
});

test('Canonical naming audit records the atomic behavior-free rename as completed', () => {
    const audit = read('docs/refactor/15_canonical_naming_lifecycle_audit.md');

    assert.match(audit, /Resolve → Prepare → Plan → Execute/);
    assert.match(audit, /rename status:\s*completed/i);
    assert.match(audit, /behavior-free/i);
    assert.match(audit, /canonicalization_plan\.v1/);
    assert.match(audit, /canonical_mutation_plan\.v1/);
    assert.match(audit, /CanonicalMutationGateway/);
    assert.match(audit, /FileCanonicalMutationGatewayAdapter/);
});
