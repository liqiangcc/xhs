'use strict';

const {
    createQuestionGroupCanonicalizationPreparationCoordinator,
} = require('./question-group-canonicalization-preparation-coordinator');
const {
    createQuestionGroupCanonicalizationMutationPlan,
} = require('./question-group-canonicalization-mutation-plan');

/**
 * Application orchestration for producing an executable-shaped, but still
 * side-effect-free, CanonicalMutationPlan from a resolved CanonicalizationPlan.
 */
function createPlanQuestionGroupCanonicalizationMutationUseCase(dependencies = {}) {
    const prepareQuestionGroupCanonicalizationMutation =
        createQuestionGroupCanonicalizationPreparationCoordinator(dependencies);

    return async function planQuestionGroupCanonicalizationMutation(input = {}) {
        for (const forbidden of [
            'preparation',
            'canonical_snapshot',
            'question_rows',
            'ownership_snapshots',
            'projected_record',
            'expected_revisions',
            'planned_question_binding_states',
            'mutation_plan',
        ]) {
            if (Object.hasOwn(input, forbidden)) {
                throw new Error('Canonical mutation planning state is controlled by Application');
            }
        }

        const preparation = await prepareQuestionGroupCanonicalizationMutation({
            plan: input.plan,
        });
        const mutationPlan = createQuestionGroupCanonicalizationMutationPlan(preparation);

        return {
            ok: true,
            relation_candidate_key: preparation.relation_candidate_key,
            canonical_id: preparation.canonical_id,
            plan: preparation.plan,
            projected_record: preparation.projected_record,
            expected_revisions: preparation.expected_revisions,
            question_ids: preparation.question_ids,
            mutation_plan: mutationPlan,
        };
    };
}

module.exports = {
    createPlanQuestionGroupCanonicalizationMutationUseCase,
};
