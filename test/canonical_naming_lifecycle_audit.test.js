'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('Canonical naming audit freezes four distinct lifecycle responsibilities before rename', () => {
    const resolveStage = read('src/application/canonical/plan-canonicalize-question-group.js');
    const prepareStage = read('src/application/canonical/prepare-canonicalize-question-group.js');
    const planMutationUseCase = read('src/application/canonical/plan-canonicalize-question-group-mutation-use-case.js');
    const mutationPlanFactory = read('src/application/canonical/plan-canonicalize-question-group-mutation.js');
    const executeStage = read('src/application/canonical/canonicalize-question-group.js');

    assert.match(resolveStage, /canonicalization_plan\.v1/);
    assert.match(resolveStage, /mutation_authorized:\s*false/);
    assert.match(resolveStage, /canonicalIdentityRepository\.inspect/);
    assert.doesNotMatch(resolveStage, /mutationStore\.preflight|mutationStore\.commit/);

    assert.match(prepareStage, /CanonicalIdentityRepository/);
    assert.match(prepareStage, /QuestionBindingRepository/);
    assert.match(prepareStage, /CanonicalQuestionOwnershipRepository/);
    assert.match(prepareStage, /projectCanonicalQuestionGroup/);
    assert.match(prepareStage, /expected_revisions/);
    assert.doesNotMatch(prepareStage, /mutationStore\.preflight|mutationStore\.commit/);

    assert.match(planMutationUseCase, /createPrepareCanonicalizeQuestionGroupUseCase/);
    assert.match(planMutationUseCase, /createCanonicalizeQuestionGroupMutationPlan/);
    assert.match(mutationPlanFactory, /createCanonicalMutationPlan/);
    assert.match(mutationPlanFactory, /operation:\s*'canonicalize'/);
    assert.doesNotMatch(mutationPlanFactory, /mutationStore\.preflight|mutationStore\.commit/);

    assert.match(executeStage, /mutationStore\.preflight/);
    assert.match(executeStage, /mutationStore\.commit/);
    assert.match(executeStage, /validateCanonicalizationCommit/);
});

test('Canonical naming audit keeps CanonicalizationPlan separate from CanonicalMutationPlan', () => {
    const audit = read('docs/refactor/15_canonical_naming_lifecycle_audit.md');
    const projectionPolicy = read('src/domain/canonical/question-group-projection-policy.js');
    const mutationPlan = read('src/application/canonical/mutation-plan.js');

    assert.match(projectionPolicy, /canonicalization_plan\.v1/);
    assert.match(projectionPolicy, /mutation_authorized !== false/);
    assert.match(mutationPlan, /canonical_mutation_plan\.v1/);

    assert.match(audit, /CanonicalizationPlan = what the business operation should become/);
    assert.match(audit, /CanonicalMutationPlan = what semantic state transition will be committed/);
    assert.match(audit, /Do not merge these concepts/);
});

test('Canonical naming audit approves one stable Resolve Prepare Plan Execute vocabulary', () => {
    const audit = read('docs/refactor/15_canonical_naming_lifecycle_audit.md');

    assert.match(audit, /Resolve → Prepare → Plan → Execute/);
    assert.match(audit, /ResolveQuestionGroupCanonicalizationUseCase/);
    assert.match(audit, /QuestionGroupCanonicalizationPreparationCoordinator/);
    assert.match(audit, /PlanQuestionGroupCanonicalizationMutationUseCase/);
    assert.match(audit, /ExecuteQuestionGroupCanonicalizationUseCase/);
    assert.match(audit, /createQuestionGroupCanonicalizationMutationPlan/);
});

test('Canonical mutation consistency boundary is classified as a Gateway rather than Store or Repository', () => {
    const audit = read('docs/refactor/15_canonical_naming_lifecycle_audit.md');
    const currentPort = read('src/ports/canonical-mutation-store.js');

    assert.match(currentPort, /\['preflight', 'commit'\]/);
    assert.match(audit, /CanonicalMutationGateway/);
    assert.match(audit, /FileCanonicalMutationGatewayAdapter/);
    assert.match(audit, /Do not rename it to `CanonicalRepository`/);
    assert.match(audit, /atomic\/recoverable consistency boundary/);
});

test('Canonical lifecycle rename is explicitly behavior-free and atomic', () => {
    const audit = read('docs/refactor/15_canonical_naming_lifecycle_audit.md');

    assert.match(audit, /behavior-free atomic rename/);
    assert.match(audit, /canonicalization_plan\.v1/);
    assert.match(audit, /canonical_mutation_plan\.v1/);
    assert.match(audit, /Do not retain compatibility aliases/);
    assert.match(audit, /Public Application keys move in the same atomic slice/);
});
