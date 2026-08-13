'use strict';

const {
    createPrepareCanonicalizeQuestionGroupUseCase,
} = require('./prepare-canonicalize-question-group');
const {
    createCanonicalizeQuestionGroupMutationPlan,
} = require('./plan-canonicalize-question-group-mutation');

/**
 * Application orchestration for producing an executable-shaped, but still
 * side-effect-free, canonicalize MutationPlan from a resolved
 * CanonicalizationPlan.
 *
 * Callers provide only the resolved plan. Current Canonical/Question state,
 * ownership facts, projected records, and opaque revisions are always loaded
 * or derived inside Application so an Interface cannot forge mutation evidence.
 */
function createPlanCanonicalizeQuestionGroupMutationUseCase(dependencies = {}) {
    const prepareCanonicalizeQuestionGroup = createPrepareCanonicalizeQuestionGroupUseCase(dependencies);

    return async function planCanonicalizeQuestionGroupMutationUseCase(input = {}) {
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

        const preparation = await prepareCanonicalizeQuestionGroup({
            plan: input.plan,
        });
        const mutationPlan = createCanonicalizeQuestionGroupMutationPlan(preparation);

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
    createPlanCanonicalizeQuestionGroupMutationUseCase,
};
