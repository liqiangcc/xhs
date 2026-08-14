'use strict';

const { isDeepStrictEqual } = require('node:util');
const {
    createPlanQuestionGroupCanonicalizationMutationUseCase,
} = require('./plan-question-group-canonicalization-mutation');
const {
    assertCanonicalIdentityRepository,
} = require('../../ports/repositories/canonical-identity-repository');
const {
    assertQuestionBindingRepository,
} = require('../../ports/repositories/question-binding-repository');
const {
    assertCanonicalQuestionOwnershipRepository,
} = require('../../ports/repositories/canonical-question-ownership-repository');
const { assertCanonicalMutationGateway } = require('../../ports/canonical-mutation-gateway');

function assertSnapshot(snapshot, label, valueKey) {
    if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
        throw new Error(`${label} snapshot is required`);
    }
    if (!snapshot.resource || typeof snapshot.resource !== 'string') {
        throw new Error(`${label} snapshot resource is required`);
    }
    if (!snapshot.revision || typeof snapshot.revision !== 'string') {
        throw new Error(`${label} snapshot revision is required`);
    }
    if (!(valueKey in snapshot)) {
        throw new Error(`${label} snapshot ${valueKey} is required`);
    }
    return snapshot;
}

async function validateCanonicalizationCommit({
    canonicalId,
    projectedRecord,
    questionIds,
    canonicalIdentityRepository,
    questionBindingRepository,
    canonicalQuestionOwnershipRepository,
}) {
    const target = assertSnapshot(
        await canonicalIdentityRepository.inspect(canonicalId),
        'post-commit Canonical target',
        'record',
    );
    if (!target.record) {
        throw new Error(`Post-commit validation failed: Canonical ${canonicalId} is missing`);
    }
    if (!isDeepStrictEqual(target.record, projectedRecord)) {
        throw new Error(`Post-commit validation failed: Canonical ${canonicalId} does not match projection`);
    }

    let updatedQuestionRows = 0;
    for (const questionId of questionIds) {
        const [bindingSnapshot, ownershipSnapshot] = await Promise.all([
            questionBindingRepository.findByQuestionId(questionId),
            canonicalQuestionOwnershipRepository.findOwners(questionId),
        ]);
        assertSnapshot(bindingSnapshot, `post-commit question ${questionId} bindings`, 'bindings');
        assertSnapshot(ownershipSnapshot, `post-commit question ${questionId} ownership`, 'canonical_ids');
        if (!Array.isArray(bindingSnapshot.bindings) || bindingSnapshot.bindings.length === 0) {
            throw new Error(`Post-commit validation failed: question ${questionId} has no bindings`);
        }
        for (const binding of bindingSnapshot.bindings) {
            if (binding.canonical_id !== canonicalId) {
                throw new Error(
                    `Post-commit validation failed: question ${questionId} is owned by ${binding.canonical_id}`,
                );
            }
            updatedQuestionRows += 1;
        }
        const owners = [...new Set(ownershipSnapshot.canonical_ids || [])].sort();
        if (owners.length !== 1 || owners[0] !== canonicalId) {
            throw new Error(
                `Post-commit validation failed: question ${questionId} Canonical ownership is ${owners.join(',') || 'empty'}`,
            );
        }
    }

    return {
        canonical_snapshot: target,
        updated_question_rows: updatedQuestionRows,
    };
}

/**
 * Execute one already-resolved CanonicalizationPlan through the shared
 * Canonical mutation consistency boundary. Fresh mutation evidence and the
 * CanonicalMutationPlan are rebuilt immediately before preflight/commit.
 */
function createExecuteQuestionGroupCanonicalizationUseCase(dependencies = {}) {
    const canonicalIdentityRepository = assertCanonicalIdentityRepository(
        dependencies.canonicalIdentityRepository,
    );
    const questionBindingRepository = assertQuestionBindingRepository(
        dependencies.questionBindingRepository,
    );
    const canonicalQuestionOwnershipRepository = assertCanonicalQuestionOwnershipRepository(
        dependencies.canonicalQuestionOwnershipRepository,
    );
    const mutationGateway = assertCanonicalMutationGateway(dependencies.mutationGateway);

    const planMutation = createPlanQuestionGroupCanonicalizationMutationUseCase({
        canonicalIdentityRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
        taxonomy: dependencies.taxonomy,
    });

    return async function executeQuestionGroupCanonicalization(input = {}) {
        for (const forbidden of [
            'preparation',
            'projected_record',
            'expected_revisions',
            'planned_question_binding_states',
            'mutation_plan',
            'preflight',
            'commit',
        ]) {
            if (Object.hasOwn(input, forbidden)) {
                throw new Error('Canonical execution state is controlled by Application');
            }
        }

        const planned = await planMutation({ plan: input.plan });
        const mutationPlan = planned.mutation_plan;
        const preflightResult = await mutationGateway.preflight(mutationPlan);
        const commitResult = await mutationGateway.commit(mutationPlan, preflightResult);
        const validation = await validateCanonicalizationCommit({
            canonicalId: planned.canonical_id,
            projectedRecord: planned.projected_record,
            questionIds: planned.question_ids,
            canonicalIdentityRepository,
            questionBindingRepository,
            canonicalQuestionOwnershipRepository,
        });

        return {
            ok: true,
            relation_candidate_key: planned.relation_candidate_key,
            canonical_id: planned.canonical_id,
            question_ids: planned.question_ids,
            updated_question_rows: validation.updated_question_rows,
            canonical_count: commitResult?.canonical_count ?? null,
            plan: planned.plan,
            mutation_plan: mutationPlan,
            commit: commitResult || null,
        };
    };
}

module.exports = {
    createExecuteQuestionGroupCanonicalizationUseCase,
    validateCanonicalizationCommit,
};
