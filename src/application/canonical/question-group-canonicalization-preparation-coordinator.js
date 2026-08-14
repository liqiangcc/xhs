'use strict';

const {
    assertCanonicalIdentityRepository,
} = require('../../ports/repositories/canonical-identity-repository');
const {
    assertQuestionBindingRepository,
} = require('../../ports/repositories/question-binding-repository');
const {
    assertCanonicalQuestionOwnershipRepository,
} = require('../../ports/repositories/canonical-question-ownership-repository');
const {
    assertCanonicalizationPlan,
    projectCanonicalQuestionGroup,
} = require('../../domain/canonical/question-group-projection-policy');

function uniqueSorted(values) {
    return [...new Set(values || [])].sort((left, right) => String(left).localeCompare(String(right)));
}

function sortedCanonicalIds(values) {
    return [...new Set(values || [])].sort((left, right) => {
        if (left == null && right == null) return 0;
        if (left == null) return -1;
        if (right == null) return 1;
        return String(left).localeCompare(String(right));
    });
}

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

function expectedRevision(snapshot) {
    return {
        resource: snapshot.resource,
        revision: snapshot.revision,
    };
}

function assertQuestionSnapshot(snapshot, questionId) {
    assertSnapshot(snapshot, `question ${questionId} bindings`, 'bindings');
    if (!Array.isArray(snapshot.bindings)) {
        throw new Error(`question ${questionId} snapshot bindings must be an array`);
    }
    if (snapshot.bindings.length === 0) {
        throw new Error(`Question rows are missing required question_id: ${questionId}`);
    }
    for (const row of snapshot.bindings) {
        if (row?.question_id !== questionId) {
            throw new Error(`Question ${questionId} snapshot contains mismatched question_id`);
        }
    }
    return snapshot;
}

function assertOwnershipSnapshot(snapshot, questionId) {
    assertSnapshot(snapshot, `question ${questionId} ownership`, 'canonical_ids');
    if (!Array.isArray(snapshot.canonical_ids)) {
        throw new Error(`question ${questionId} ownership canonical_ids must be an array`);
    }
    return snapshot;
}

function assertQuestionMembershipConsistency({
    plan,
    canonicalId,
    existingQuestionIds,
    questionId,
    questionSnapshot,
    ownershipSnapshot,
}) {
    const isExistingMember = existingQuestionIds.has(questionId);
    const owners = uniqueSorted(ownershipSnapshot.canonical_ids);
    const otherOwner = owners.find((ownerId) => ownerId !== canonicalId);
    if (otherOwner) {
        throw new Error(`Question ${questionId} already belongs to ${otherOwner}`);
    }

    const bindingConflict = questionSnapshot.bindings.find(
        (binding) => binding.canonical_id && binding.canonical_id !== canonicalId,
    );
    if (bindingConflict) {
        throw new Error(`Question ${questionId} already belongs to ${bindingConflict.canonical_id}`);
    }

    if (plan.plan_kind === 'create_canonical') {
        if (owners.includes(canonicalId)) {
            throw new Error(`Question ${questionId} references absent Canonical ${canonicalId}`);
        }
        const danglingBinding = questionSnapshot.bindings.find(
            (binding) => binding.canonical_id === canonicalId,
        );
        if (danglingBinding) {
            throw new Error(`Question ${questionId} binds to absent Canonical ${canonicalId}`);
        }
        return;
    }

    if (isExistingMember) {
        if (!owners.includes(canonicalId)) {
            throw new Error(`Existing Canonical ${canonicalId} lost ownership of question ${questionId}`);
        }
        const bindingDrift = questionSnapshot.bindings.find(
            (binding) => binding.canonical_id !== canonicalId,
        );
        if (bindingDrift) {
            throw new Error(`Existing Canonical ${canonicalId} has inconsistent binding for question ${questionId}`);
        }
    }
}

function plannedBindingStates(plan, resultingQuestionIds, questionSnapshots) {
    const snapshotsByQuestionId = new Map(
        resultingQuestionIds.map((questionId, index) => [questionId, questionSnapshots[index]]),
    );
    return uniqueSorted(plan.question_ids).map((questionId) => {
        const snapshot = snapshotsByQuestionId.get(questionId);
        if (!snapshot) throw new Error(`Question snapshot missing for planned question ${questionId}`);
        return {
            question_id: questionId,
            from_canonical_ids: sortedCanonicalIds(
                snapshot.bindings.map((binding) => binding.canonical_id ?? null),
            ),
        };
    });
}

/**
 * Coordinate the current Canonical facts required to project a previously
 * resolved CanonicalizationPlan. This stage validates ownership, preserves
 * opaque revisions for a later mutation boundary, and invokes the pure
 * projection policy without constructing or committing a MutationPlan.
 */
function createQuestionGroupCanonicalizationPreparationCoordinator(dependencies = {}) {
    const canonicalIdentityRepository = assertCanonicalIdentityRepository(
        dependencies.canonicalIdentityRepository,
    );
    const questionBindingRepository = assertQuestionBindingRepository(
        dependencies.questionBindingRepository,
    );
    const canonicalQuestionOwnershipRepository = assertCanonicalQuestionOwnershipRepository(
        dependencies.canonicalQuestionOwnershipRepository,
    );
    const taxonomy = dependencies.taxonomy;

    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }

    return async function prepareQuestionGroupCanonicalizationMutation(input = {}) {
        for (const forbidden of [
            'canonical_snapshot',
            'question_rows',
            'ownership_snapshots',
            'expected_revisions',
            'projected_record',
            'planned_question_binding_states',
        ]) {
            if (Object.hasOwn(input, forbidden)) {
                throw new Error('Canonical preparation state is controlled by Application');
            }
        }

        const plan = assertCanonicalizationPlan(input.plan);
        const canonicalId = String(plan.canonical_target.canonical_id).trim();
        const targetIdentity = assertSnapshot(
            await canonicalIdentityRepository.inspect(canonicalId),
            'Canonical target identity',
            'record',
        );

        if (targetIdentity.resource !== plan.target_identity.resource) {
            throw new Error('Canonical target identity resource changed since planning');
        }
        if (targetIdentity.revision !== plan.target_identity.revision) {
            throw new Error('Canonical target identity revision changed since planning');
        }

        const existingQuestionIds = new Set(targetIdentity.record?.question_ids || []);
        const resultingQuestionIds = uniqueSorted([
            ...existingQuestionIds,
            ...plan.question_ids,
        ]);

        const questionSnapshots = await Promise.all(
            resultingQuestionIds.map((questionId) => questionBindingRepository.findByQuestionId(questionId)),
        );
        const ownershipSnapshots = await Promise.all(
            resultingQuestionIds.map(
                (questionId) => canonicalQuestionOwnershipRepository.findOwners(questionId),
            ),
        );

        const questionRows = [];
        for (let index = 0; index < resultingQuestionIds.length; index += 1) {
            const questionId = resultingQuestionIds[index];
            const questionSnapshot = assertQuestionSnapshot(questionSnapshots[index], questionId);
            const ownershipSnapshot = assertOwnershipSnapshot(ownershipSnapshots[index], questionId);
            assertQuestionMembershipConsistency({
                plan,
                canonicalId,
                existingQuestionIds,
                questionId,
                questionSnapshot,
                ownershipSnapshot,
            });
            questionRows.push(...questionSnapshot.bindings);
        }

        const projectedRecord = projectCanonicalQuestionGroup({
            plan,
            canonical_snapshot: targetIdentity,
            question_rows: questionRows,
            taxonomy,
        });
        const expectedRevisions = [
            expectedRevision(targetIdentity),
            ...questionSnapshots.map(expectedRevision),
            ...ownershipSnapshots.map(expectedRevision),
        ];

        return {
            ok: true,
            relation_candidate_key: plan.relation_candidate_key,
            canonical_id: canonicalId,
            plan,
            projected_record: projectedRecord,
            expected_revisions: expectedRevisions,
            question_ids: resultingQuestionIds,
            planned_question_binding_states: plannedBindingStates(
                plan,
                resultingQuestionIds,
                questionSnapshots,
            ),
        };
    };
}

module.exports = {
    createQuestionGroupCanonicalizationPreparationCoordinator,
    assertQuestionMembershipConsistency,
    plannedBindingStates,
};
