'use strict';

const REVIEWED_CONSOLIDATION_RELATIONS = Object.freeze(['same', 'alias']);

function uniqueSorted(values) {
    return [...new Set(values || [])].sort((left, right) => String(left).localeCompare(String(right)));
}

function assertReadyIntent(intent) {
    if (!intent || typeof intent !== 'object' || Array.isArray(intent)) {
        throw new Error('Reviewed consolidation requires relation apply intent');
    }
    if (intent.schema_version !== 'dedup_relation_apply_intent.v1') {
        throw new Error('Reviewed consolidation requires dedup_relation_apply_intent.v1');
    }
    if (intent.intent_kind !== 'canonicalize_question_group' || intent.intent_state !== 'ready') {
        throw new Error('Reviewed consolidation requires ready canonicalization intent');
    }
    if (intent.apply_required !== true) {
        throw new Error('Reviewed consolidation requires apply_required=true');
    }
    if (!REVIEWED_CONSOLIDATION_RELATIONS.includes(intent.relation)) {
        throw new Error(`Unsupported reviewed consolidation relation: ${intent.relation}`);
    }
    if (!intent.canonical_target?.canonical_id) {
        throw new Error('Reviewed consolidation requires canonical target');
    }
    if (!Array.isArray(intent.question_ids) || intent.question_ids.length === 0) {
        throw new Error('Reviewed consolidation requires reviewed question_ids');
    }
    return intent;
}

function normalizeOwnerFacts(questionOwners, reviewedQuestionIds) {
    if (!Array.isArray(questionOwners)) {
        throw new Error('Reviewed consolidation question ownership facts must be an array');
    }
    const byQuestionId = new Map();
    for (const fact of questionOwners) {
        const questionId = String(fact?.question_id || '').trim();
        if (!questionId || !reviewedQuestionIds.includes(questionId)) continue;
        if (byQuestionId.has(questionId)) {
            throw new Error(`Duplicate ownership fact for Question ${questionId}`);
        }
        if (!Array.isArray(fact.canonical_ids)) {
            throw new Error(`Ownership fact canonical_ids are required for Question ${questionId}`);
        }
        const owners = uniqueSorted(fact.canonical_ids.filter(Boolean));
        if (owners.length > 1) {
            throw new Error(`Question ${questionId} belongs to multiple Canonicals: ${owners.join(', ')}`);
        }
        byQuestionId.set(questionId, owners);
    }
    for (const questionId of reviewedQuestionIds) {
        if (!byQuestionId.has(questionId)) {
            throw new Error(`Ownership fact missing for Question ${questionId}`);
        }
    }
    return byQuestionId;
}

function assertReviewedOwnershipMatchesRecords({
    reviewedQuestionIds,
    ownersByQuestion,
    targetCanonicalId,
    targetRecord,
    sourceCanonicalId,
    sourceRecord,
}) {
    const targetQuestionIds = new Set(targetRecord?.question_ids || []);
    const sourceQuestionIds = new Set(sourceRecord?.question_ids || []);

    for (const questionId of reviewedQuestionIds) {
        const owners = ownersByQuestion.get(questionId) || [];
        if (owners.length === 0) {
            throw new Error(
                `Reviewed consolidation cannot combine an unowned Question with an existing source Canonical: ${questionId}`,
            );
        }
        const owner = owners[0];
        if (owner === targetCanonicalId && !targetQuestionIds.has(questionId)) {
            throw new Error(
                `Reviewed consolidation ownership changed while resolving target ${targetCanonicalId}: ${questionId}`,
            );
        }
        if (owner === sourceCanonicalId && !sourceQuestionIds.has(questionId)) {
            throw new Error(
                `Reviewed consolidation ownership changed while resolving source ${sourceCanonicalId}: ${questionId}`,
            );
        }
    }
}

/**
 * Decide whether an explicit same/alias RelationDecision can use ordinary
 * question-group canonicalization or must consolidate an already-existing
 * source Canonical into the reviewed target Canonical.
 *
 * Consolidation is deliberately fail-closed: if the source Canonical contains
 * any Question that was not part of the reviewed RelationCandidate, the whole
 * Canonical may not be merged from this decision. A broader source-first review
 * is required first. Cross-Canonical consolidation also requires at least one
 * reviewed Question to already belong to the chosen target, so a caller cannot
 * attach a fully reviewed source Canonical to an unrelated existing target.
 */
function decideReviewedCanonicalConsolidation(input = {}) {
    const intent = assertReadyIntent(input.intent);
    const targetCanonicalId = String(intent.canonical_target.canonical_id).trim();
    const reviewedQuestionIds = uniqueSorted(intent.question_ids);
    const ownersByQuestion = normalizeOwnerFacts(input.question_owners, reviewedQuestionIds);
    const externalOwners = uniqueSorted(
        reviewedQuestionIds.flatMap((questionId) => ownersByQuestion.get(questionId))
            .filter((canonicalId) => canonicalId !== targetCanonicalId),
    );

    if (externalOwners.length === 0) {
        return Object.freeze({
            schema_version: 'reviewed_canonical_apply_strategy.v1',
            strategy: 'question_group',
            relation_candidate_key: intent.relation_candidate_key,
            relation: intent.relation,
            target_canonical_id: targetCanonicalId,
            reviewed_question_ids: reviewedQuestionIds,
        });
    }
    if (externalOwners.length > 1) {
        throw new Error(
            `Reviewed relation spans multiple non-target Canonicals: ${externalOwners.join(', ')}`,
        );
    }
    if (!input.target_record || input.target_record.canonical_id !== targetCanonicalId) {
        throw new Error(
            `Reviewed Canonical consolidation requires existing target ${targetCanonicalId}`,
        );
    }

    const sourceCanonicalId = externalOwners[0];
    const sourceRecord = input.source_records?.[sourceCanonicalId];
    if (!sourceRecord || sourceRecord.canonical_id !== sourceCanonicalId) {
        throw new Error(`Reviewed consolidation source Canonical not found: ${sourceCanonicalId}`);
    }
    const sourceQuestionIds = uniqueSorted(sourceRecord.question_ids || []);
    if (sourceQuestionIds.length === 0) {
        throw new Error(`Reviewed consolidation source Canonical has no Questions: ${sourceCanonicalId}`);
    }

    assertReviewedOwnershipMatchesRecords({
        reviewedQuestionIds,
        ownersByQuestion,
        targetCanonicalId,
        targetRecord: input.target_record,
        sourceCanonicalId,
        sourceRecord,
    });

    const reviewed = new Set(reviewedQuestionIds);
    const unreviewedSourceQuestionIds = sourceQuestionIds.filter((questionId) => !reviewed.has(questionId));
    if (unreviewedSourceQuestionIds.length) {
        throw new Error(
            `Reviewed consolidation would move unreviewed Questions from ${sourceCanonicalId}: ${unreviewedSourceQuestionIds.join(', ')}`,
        );
    }
    const targetReviewedQuestionIds = reviewedQuestionIds.filter(
        (questionId) => (ownersByQuestion.get(questionId) || [])[0] === targetCanonicalId,
    );
    if (targetReviewedQuestionIds.length === 0) {
        throw new Error(
            `Reviewed consolidation target ${targetCanonicalId} is not represented by any reviewed Question`,
        );
    }

    return Object.freeze({
        schema_version: 'reviewed_canonical_apply_strategy.v1',
        strategy: 'merge_existing_canonical',
        relation_candidate_key: intent.relation_candidate_key,
        relation: intent.relation,
        target_canonical_id: targetCanonicalId,
        source_canonical_id: sourceCanonicalId,
        reviewed_question_ids: reviewedQuestionIds,
        target_reviewed_question_ids: targetReviewedQuestionIds,
        source_question_ids: sourceQuestionIds,
    });
}

module.exports = {
    REVIEWED_CONSOLIDATION_RELATIONS,
    decideReviewedCanonicalConsolidation,
};
