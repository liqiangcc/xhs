'use strict';

const { mergeCanonical } = require('../../domain/canonical/merge-policy');
const { createCanonicalMutationPlan } = require('./mutation-plan');
const { planCanonicalReviewMigration } = require('./review-migration-plan');
const { assertCanonicalRepository } = require('../../ports/repositories/canonical-repository');
const { assertQuestionBindingRepository } = require('../../ports/repositories/question-binding-repository');
const { assertReviewRepository } = require('../../ports/repositories/review-repository');
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

function assertReviewSnapshot(snapshot) {
    assertSnapshot(snapshot, 'review merge', 'target_items');
    if (!Array.isArray(snapshot.target_items)) {
        throw new Error('review merge snapshot target_items must be an array');
    }
    if (!Array.isArray(snapshot.source_items)) {
        throw new Error('review merge snapshot source_items must be an array');
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

function assertPostCommitState(targetId, sourceId, movedQuestionIds, targetSnapshot, sourceSnapshot, sourceBindings, targetBindings) {
    if (!targetSnapshot?.record || targetSnapshot.record.canonical_id !== targetId) {
        throw new Error(`Post-commit validation failed: target canonical ${targetId} is missing`);
    }
    if (sourceSnapshot !== null) {
        throw new Error(`Post-commit validation failed: source canonical ${sourceId} still exists`);
    }
    if ((sourceBindings?.bindings || []).length) {
        throw new Error(`Post-commit validation failed: source canonical ${sourceId} still owns question bindings`);
    }

    const targetQuestionIds = new Set(targetSnapshot.record.question_ids || []);
    const targetBindingQuestionIds = new Set((targetBindings?.bindings || []).map((binding) => binding.question_id));
    for (const questionId of movedQuestionIds) {
        if (!targetQuestionIds.has(questionId)) {
            throw new Error(`Post-commit validation failed: target canonical is missing question ${questionId}`);
        }
        if (!targetBindingQuestionIds.has(questionId)) {
            throw new Error(`Post-commit validation failed: target bindings are missing question ${questionId}`);
        }
    }
}

function createMergeCanonicalUseCase(dependencies = {}) {
    const canonicalRepository = assertCanonicalRepository(dependencies.canonicalRepository);
    const questionBindingRepository = assertQuestionBindingRepository(dependencies.questionBindingRepository);
    const reviewRepository = assertReviewRepository(dependencies.reviewRepository);
    const mutationStore = assertCanonicalMutationStore(dependencies.mutationStore);
    const clock = dependencies.clock || (() => new Date().toISOString());

    if (typeof clock !== 'function') throw new Error('clock must be a function');

    return async function mergeCanonicalUseCase(input = {}) {
        const targetId = input.target;
        const sourceId = input.source;
        const reason = input.reason;
        if (!targetId || !sourceId || !reason) {
            throw new Error('target, source, and reason are required');
        }
        if (targetId === sourceId) throw new Error('target and source must be different');

        const [targetSnapshot, sourceSnapshot, targetBindingSnapshot, sourceBindingSnapshot, reviewSnapshot] = await Promise.all([
            canonicalRepository.get(targetId),
            canonicalRepository.get(sourceId),
            questionBindingRepository.findByCanonical(targetId),
            questionBindingRepository.findByCanonical(sourceId),
            reviewRepository.loadMergeState(targetId, sourceId),
        ]);

        if (!targetSnapshot) throw new Error(`Target canonical not found: ${targetId}`);
        if (!sourceSnapshot) throw new Error(`Source canonical not found: ${sourceId}`);
        assertSnapshot(targetSnapshot, 'target canonical', 'record');
        assertSnapshot(sourceSnapshot, 'source canonical', 'record');
        assertSnapshot(targetBindingSnapshot, 'target question bindings', 'bindings');
        assertSnapshot(sourceBindingSnapshot, 'source question bindings', 'bindings');
        assertReviewSnapshot(reviewSnapshot);

        const merged = mergeCanonical(targetSnapshot.record, sourceSnapshot.record);
        const movedQuestionIds = uniqueSorted(sourceSnapshot.record.question_ids);
        const mergedAt = clock();
        const reviewMigration = planCanonicalReviewMigration({
            targetCanonicalId: targetId,
            sourceCanonicalId: sourceId,
            targetItems: reviewSnapshot.target_items,
            sourceItems: reviewSnapshot.source_items,
            updatedAtFallback: String(mergedAt).slice(0, 10),
        });
        const plan = createCanonicalMutationPlan({
            operation: 'merge',
            expected_revisions: [
                expectedRevision(targetSnapshot),
                expectedRevision(sourceSnapshot),
                expectedRevision(targetBindingSnapshot),
                expectedRevision(sourceBindingSnapshot),
                expectedRevision(reviewSnapshot),
            ],
            changes: {
                canonical_upserts: [merged],
                canonical_removals: [sourceId],
                question_rebindings: movedQuestionIds.map((questionId) => ({
                    question_id: questionId,
                    from_canonical_id: sourceId,
                    to_canonical_id: targetId,
                })),
                review_migrations: [reviewMigration],
                answer_invalidations: [{
                    canonical_id: targetId,
                    reason: 'canonical_merge',
                    source_canonical_id: sourceId,
                }],
                answer_archives: [{
                    canonical_id: sourceId,
                    target_canonical_id: targetId,
                    reason: 'canonical_merge',
                }],
                rebuild_indexes: true,
                history_entry: {
                    schema_version: 'canonical_merge.v1',
                    merged_at: mergedAt,
                    target: targetId,
                    source: sourceId,
                    reason,
                    moved_question_ids: movedQuestionIds,
                },
            },
        });

        const preflightResult = await mutationStore.preflight(plan);
        const commitResult = await mutationStore.commit(plan, preflightResult);

        const [postTarget, postSource, postSourceBindings, postTargetBindings] = await Promise.all([
            canonicalRepository.get(targetId),
            canonicalRepository.get(sourceId),
            questionBindingRepository.findByCanonical(sourceId),
            questionBindingRepository.findByCanonical(targetId),
        ]);
        assertPostCommitState(
            targetId,
            sourceId,
            movedQuestionIds,
            postTarget,
            postSource,
            postSourceBindings,
            postTargetBindings,
        );

        return {
            ok: true,
            target: targetId,
            source: sourceId,
            reason,
            moved_question_ids: movedQuestionIds,
            plan,
            commit: commitResult || null,
        };
    };
}

module.exports = {
    createMergeCanonicalUseCase,
};
