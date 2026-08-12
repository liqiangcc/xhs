'use strict';

const { acceptCanonicalCandidate } = require('../../domain/canonical/accept-policy');
const { refreshCanonicalFromQuestions } = require('../../domain/canonical/refresh-policy');
const { createCanonicalMutationPlan } = require('./mutation-plan');
const { assertCanonicalCandidateRepository } = require('../../ports/repositories/canonical-candidate-repository');
const { assertCanonicalIdentityRepository } = require('../../ports/repositories/canonical-identity-repository');
const { assertCanonicalQuestionOwnershipRepository } = require('../../ports/repositories/canonical-question-ownership-repository');
const { assertQuestionBindingRepository } = require('../../ports/repositories/question-binding-repository');
const { assertCanonicalMutationStore } = require('../../ports/canonical-mutation-store');

function assertSnapshot(snapshot, label, valueKey) {
    if (!snapshot || typeof snapshot !== 'object') {
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

function uniqueSorted(values) {
    return [...new Set(values || [])].sort((a, b) => String(a).localeCompare(String(b)));
}

function assertCandidateConflicts(
    candidateQuestionIds,
    canonicalId,
    questionSnapshotsById,
    ownershipSnapshotsById,
) {
    for (const questionId of candidateQuestionIds) {
        const bindings = questionSnapshotsById.get(questionId)?.bindings || [];
        const bindingConflict = bindings.find(
            (binding) => binding.canonical_id && binding.canonical_id !== canonicalId,
        );
        if (bindingConflict) {
            throw new Error(`Question ${questionId} already belongs to ${bindingConflict.canonical_id}`);
        }

        const ownerConflict = (ownershipSnapshotsById.get(questionId)?.canonical_ids || [])
            .find((ownerId) => ownerId !== canonicalId);
        if (ownerConflict) {
            throw new Error(`Question ${questionId} already belongs to ${ownerConflict}`);
        }
    }
}

function createAcceptCanonicalUseCase(dependencies = {}) {
    const candidateRepository = assertCanonicalCandidateRepository(dependencies.candidateRepository);
    const canonicalIdentityRepository = assertCanonicalIdentityRepository(dependencies.canonicalIdentityRepository);
    const canonicalQuestionOwnershipRepository = assertCanonicalQuestionOwnershipRepository(
        dependencies.canonicalQuestionOwnershipRepository,
    );
    const questionBindingRepository = assertQuestionBindingRepository(dependencies.questionBindingRepository);
    const mutationStore = assertCanonicalMutationStore(dependencies.mutationStore);
    const taxonomy = dependencies.taxonomy;

    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }

    return async function acceptCanonicalUseCase(input = {}) {
        const candidateId = input.candidate_id;
        const canonicalId = input.canonical_id;
        const title = input.title;
        if (!candidateId || !canonicalId) {
            throw new Error('candidate_id and canonical_id are required');
        }

        const [candidateSnapshot, targetIdentity] = await Promise.all([
            candidateRepository.get(candidateId),
            canonicalIdentityRepository.inspect(canonicalId),
        ]);
        if (!candidateSnapshot) throw new Error(`Candidate not found: ${candidateId}`);
        assertSnapshot(candidateSnapshot, 'canonical candidate', 'candidate');
        assertSnapshot(targetIdentity, 'target canonical identity', 'record');
        if (candidateSnapshot.candidate.candidate_id !== candidateId) {
            throw new Error(`Candidate snapshot id mismatch: expected ${candidateId}`);
        }

        const candidateQuestionIds = uniqueSorted(candidateSnapshot.candidate.question_ids);
        const refreshQuestionIds = uniqueSorted([
            ...(targetIdentity.record?.question_ids || []),
            ...candidateQuestionIds,
        ]);

        const questionSnapshots = await Promise.all(
            refreshQuestionIds.map((questionId) => questionBindingRepository.findByQuestionId(questionId)),
        );
        questionSnapshots.forEach((snapshot, index) => {
            assertSnapshot(snapshot, `question ${refreshQuestionIds[index]} bindings`, 'bindings');
            if (!Array.isArray(snapshot.bindings)) {
                throw new Error(`question ${refreshQuestionIds[index]} snapshot bindings must be an array`);
            }
        });

        const ownershipSnapshots = await Promise.all(
            candidateQuestionIds.map(
                (questionId) => canonicalQuestionOwnershipRepository.findOwners(questionId),
            ),
        );
        ownershipSnapshots.forEach((snapshot, index) => {
            assertSnapshot(snapshot, `question ${candidateQuestionIds[index]} ownership`, 'canonical_ids');
            if (!Array.isArray(snapshot.canonical_ids)) {
                throw new Error(`question ${candidateQuestionIds[index]} ownership canonical_ids must be an array`);
            }
        });

        const questionSnapshotsById = new Map(
            refreshQuestionIds.map((questionId, index) => [questionId, questionSnapshots[index]]),
        );
        const ownershipSnapshotsById = new Map(
            candidateQuestionIds.map((questionId, index) => [questionId, ownershipSnapshots[index]]),
        );
        assertCandidateConflicts(
            candidateQuestionIds,
            canonicalId,
            questionSnapshotsById,
            ownershipSnapshotsById,
        );

        const accepted = acceptCanonicalCandidate(
            targetIdentity.record,
            candidateSnapshot.candidate,
            canonicalId,
            title ? { title } : {},
        );
        const refreshRows = refreshQuestionIds.flatMap(
            (questionId) => questionSnapshotsById.get(questionId)?.bindings || [],
        );
        const refreshed = refreshCanonicalFromQuestions(accepted, refreshRows, taxonomy);

        const assignments = candidateQuestionIds
            .filter((questionId) => (questionSnapshotsById.get(questionId)?.bindings || [])
                .some((binding) => binding.canonical_id == null))
            .map((questionId) => ({
                question_id: questionId,
                from_canonical_id: null,
                to_canonical_id: canonicalId,
            }));

        const plan = createCanonicalMutationPlan({
            operation: 'accept',
            expected_revisions: [
                expectedRevision(candidateSnapshot),
                expectedRevision(targetIdentity),
                ...questionSnapshots.map(expectedRevision),
                ...ownershipSnapshots.map(expectedRevision),
            ],
            changes: {
                canonical_upserts: [refreshed],
                canonical_removals: [],
                question_rebindings: assignments,
                review_migrations: [],
                answer_invalidations: [],
                answer_archives: [],
                rebuild_indexes: true,
                history_entry: null,
            },
        });

        const preflightResult = await mutationStore.preflight(plan);
        const commitResult = await mutationStore.commit(plan, preflightResult);

        const [postTarget, ...postCandidateQuestions] = await Promise.all([
            canonicalIdentityRepository.inspect(canonicalId),
            ...candidateQuestionIds.map(
                (questionId) => questionBindingRepository.findByQuestionId(questionId),
            ),
        ]);
        assertSnapshot(postTarget, 'post-commit target canonical', 'record');
        if (!postTarget.record) {
            throw new Error(`Post-commit validation failed: canonical ${canonicalId} is missing`);
        }
        for (const questionId of candidateQuestionIds) {
            if (!(postTarget.record.question_ids || []).includes(questionId)) {
                throw new Error(
                    `Post-commit validation failed: canonical ${canonicalId} is missing question ${questionId}`,
                );
            }
        }

        let updatedQuestionRows = 0;
        postCandidateQuestions.forEach((snapshot, index) => {
            const questionId = candidateQuestionIds[index];
            assertSnapshot(snapshot, `post-commit question ${questionId} bindings`, 'bindings');
            for (const binding of snapshot.bindings || []) {
                if (binding.canonical_id !== canonicalId) {
                    throw new Error(
                        `Post-commit validation failed: question ${questionId} is owned by ${binding.canonical_id}`,
                    );
                }
                updatedQuestionRows += 1;
            }
        });

        return {
            ok: true,
            canonical_id: canonicalId,
            accepted_candidate_id: candidateId,
            question_ids: candidateQuestionIds,
            updated_question_rows: updatedQuestionRows,
            canonical_count: commitResult?.canonical_count ?? null,
            plan,
            commit: commitResult || null,
        };
    };
}

module.exports = {
    createAcceptCanonicalUseCase,
};
