'use strict';

const {
    decideReviewedCanonicalConsolidation,
} = require('../../domain/canonical/reviewed-consolidation-policy');
const {
    assertCanonicalRepository,
} = require('../../ports/repositories/canonical-repository');
const {
    assertCanonicalQuestionOwnershipRepository,
} = require('../../ports/repositories/canonical-question-ownership-repository');

function assertOwnershipSnapshot(snapshot, questionId) {
    if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
        throw new Error(`Question ${questionId} ownership snapshot is required`);
    }
    if (!snapshot.resource || typeof snapshot.resource !== 'string') {
        throw new Error(`Question ${questionId} ownership resource is required`);
    }
    if (!snapshot.revision || typeof snapshot.revision !== 'string') {
        throw new Error(`Question ${questionId} ownership revision is required`);
    }
    if (!Array.isArray(snapshot.canonical_ids)) {
        throw new Error(`Question ${questionId} ownership canonical_ids must be an array`);
    }
    return snapshot;
}

function createResolveReviewedCanonicalConsolidationUseCase(dependencies = {}) {
    const canonicalRepository = assertCanonicalRepository(dependencies.canonicalRepository);
    const ownershipRepository = assertCanonicalQuestionOwnershipRepository(
        dependencies.canonicalQuestionOwnershipRepository,
    );

    return async function resolveReviewedCanonicalConsolidation(input = {}) {
        const intent = input.intent;
        if (!intent || typeof intent !== 'object' || Array.isArray(intent)) {
            throw new Error('relation apply intent is required');
        }
        const targetCanonicalId = String(intent.canonical_target?.canonical_id || '').trim();
        if (!targetCanonicalId) {
            throw new Error('relation apply intent canonical target is required');
        }
        if (!Array.isArray(intent.question_ids) || intent.question_ids.length === 0) {
            throw new Error('relation apply intent question_ids are required');
        }

        const ownershipSnapshots = await Promise.all(
            intent.question_ids.map(async (questionId) => ({
                question_id: questionId,
                snapshot: assertOwnershipSnapshot(
                    await ownershipRepository.findOwners(questionId),
                    questionId,
                ),
            })),
        );
        const externalCanonicalIds = [...new Set(
            ownershipSnapshots.flatMap(({ snapshot }) => snapshot.canonical_ids)
                .filter((canonicalId) => canonicalId && canonicalId !== targetCanonicalId),
        )].sort((left, right) => String(left).localeCompare(String(right)));

        const [targetSnapshot, ...sourceSnapshots] = await Promise.all([
            canonicalRepository.get(targetCanonicalId),
            ...externalCanonicalIds.map((canonicalId) => canonicalRepository.get(canonicalId)),
        ]);
        const sourceRecords = Object.fromEntries(
            externalCanonicalIds.map((canonicalId, index) => [
                canonicalId,
                sourceSnapshots[index]?.record || null,
            ]),
        );

        return decideReviewedCanonicalConsolidation({
            intent,
            target_record: targetSnapshot?.record || null,
            question_owners: ownershipSnapshots.map(({ question_id, snapshot }) => ({
                question_id,
                canonical_ids: snapshot.canonical_ids,
            })),
            source_records: sourceRecords,
        });
    };
}

module.exports = {
    createResolveReviewedCanonicalConsolidationUseCase,
};
