'use strict';

function assertUseCase(value, label) {
    if (typeof value !== 'function') throw new Error(`${label} use case is required`);
    return value;
}

function createApplyRelationDecisionUseCase(dependencies = {}) {
    const prepareRelationApply = assertUseCase(
        dependencies.prepareRelationApply,
        'PrepareRelationApply',
    );
    const resolveQuestionGroupCanonicalization = assertUseCase(
        dependencies.resolveQuestionGroupCanonicalization,
        'ResolveQuestionGroupCanonicalization',
    );
    const executeQuestionGroupCanonicalization = assertUseCase(
        dependencies.executeQuestionGroupCanonicalization,
        'ExecuteQuestionGroupCanonicalization',
    );

    return async function applyRelationDecisionUseCase(input = {}) {
        const relationCandidateKey = String(input.relation_candidate_key || '').trim();
        if (!relationCandidateKey) throw new Error('relation_candidate_key is required');

        for (const forbidden of [
            'decision',
            'source_revisions',
            'expected_revisions',
            'intent',
            'canonicalization_plan',
            'mutation_plan',
            'preflight',
            'commit',
        ]) {
            if (Object.hasOwn(input, forbidden)) {
                throw new Error('Relation decision apply state is controlled by Application');
            }
        }

        const prepareInput = {
            relation_candidate_key: relationCandidateKey,
        };
        if (Object.hasOwn(input, 'canonical_id')) prepareInput.canonical_id = input.canonical_id;
        if (Object.hasOwn(input, 'canonical_title')) prepareInput.canonical_title = input.canonical_title;

        // Re-load the persisted explicit Decision and re-check its Dedup source
        // revisions immediately inside the same Application workflow that will
        // resolve and execute Canonical mutation.
        const prepared = await prepareRelationApply(prepareInput);
        const intent = prepared.intent;
        if (!intent || typeof intent !== 'object') {
            throw new Error('PrepareRelationApply must return an intent');
        }

        if (intent.apply_required !== true) {
            return {
                ok: true,
                applied: false,
                relation_candidate_key: relationCandidateKey,
                relation: prepared.relation,
                reason_code: intent.reason_code || 'apply_not_required',
                decision_snapshot: prepared.decision_snapshot,
                current_source_revisions: prepared.current_source_revisions,
            };
        }

        if (intent.intent_kind !== 'canonicalize_question_group') {
            throw new Error(`Unsupported relation apply intent kind: ${intent.intent_kind}`);
        }
        if (intent.intent_state !== 'ready') {
            throw new Error(
                `Relation apply intent is not ready: ${intent.intent_state}; required inputs: ${(intent.required_inputs || []).join(', ')}`,
            );
        }

        const canonicalization = await resolveQuestionGroupCanonicalization({ intent });
        const execution = await executeQuestionGroupCanonicalization({ plan: canonicalization.plan });

        return {
            ok: true,
            applied: true,
            relation_candidate_key: relationCandidateKey,
            relation: prepared.relation,
            canonical_id: execution.canonical_id,
            canonical_resolution: canonicalization.resolution,
            question_ids: execution.question_ids,
            updated_question_rows: execution.updated_question_rows,
            canonical_count: execution.canonical_count,
            decision_snapshot: prepared.decision_snapshot,
            current_source_revisions: prepared.current_source_revisions,
            commit: execution.commit,
        };
    };
}

module.exports = {
    createApplyRelationDecisionUseCase,
};
