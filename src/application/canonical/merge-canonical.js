'use strict';

const { mergeCanonical } = require('../../domain/canonical/merge-policy');
const { refreshCanonicalFromQuestions } = require('../../domain/canonical/refresh-policy');
const { createCanonicalMutationPlan } = require('./mutation-plan');
const { planCanonicalReviewMigration } = require('./review-migration-plan');
const { planCanonicalAnswerMerge } = require('./answer-merge-plan');
const { assertCanonicalRepository } = require('../../ports/repositories/canonical-repository');
const { assertQuestionBindingRepository } = require('../../ports/repositories/question-binding-repository');
const { assertReviewRepository } = require('../../ports/repositories/review-repository');
const { assertAnswerRepository } = require('../../ports/repositories/answer-repository');
const { assertCanonicalMutationGateway } = require('../../ports/canonical-mutation-gateway');
const { assertCanonicalIntegrityChecker } = require('../../ports/services/canonical-integrity-checker');

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
    if (!Number.isInteger(snapshot.source_session_event_count) || snapshot.source_session_event_count < 0) {
        throw new Error('review merge snapshot source_session_event_count must be a non-negative integer');
    }
    return snapshot;
}

function assertAnswerSnapshot(snapshot) {
    assertSnapshot(snapshot, 'answer merge', 'target_answer');
    if (!Object.prototype.hasOwnProperty.call(snapshot, 'source_answer')) {
        throw new Error('answer merge snapshot source_answer is required');
    }
    if (typeof snapshot.source_archive_exists !== 'boolean') {
        throw new Error('answer merge snapshot source_archive_exists must be a boolean');
    }
    return snapshot;
}

function assertIntegrityReport(report) {
    if (!report || typeof report !== 'object') {
        throw new Error('canonical integrity report is required');
    }
    if (report.schema_version !== 'canonical_quality_report.v1') {
        throw new Error('canonical integrity report schema_version must be canonical_quality_report.v1');
    }
    if (typeof report.ok !== 'boolean') {
        throw new Error('canonical integrity report ok must be a boolean');
    }
    return report;
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

function normalizeExpectedQuestionIds(value, label) {
    if (value === undefined) return null;
    if (!Array.isArray(value)) {
        throw new Error(`${label} must be an array when provided`);
    }
    const normalized = uniqueSorted(value.map((questionId) => String(questionId || '').trim()));
    if (normalized.some((questionId) => !questionId) || normalized.length !== value.length) {
        throw new Error(`${label} must contain unique non-empty Question ids`);
    }
    return normalized;
}

function assertReviewedMergeScope(input, targetRecord, sourceRecord) {
    const expectedSourceQuestionIds = normalizeExpectedQuestionIds(
        input.expected_source_question_ids,
        'expected_source_question_ids',
    );
    const expectedTargetReviewedQuestionIds = normalizeExpectedQuestionIds(
        input.expected_target_reviewed_question_ids,
        'expected_target_reviewed_question_ids',
    );

    if (expectedSourceQuestionIds !== null) {
        const currentSourceQuestionIds = uniqueSorted(sourceRecord.question_ids || []);
        if (JSON.stringify(currentSourceQuestionIds) !== JSON.stringify(expectedSourceQuestionIds)) {
            throw new Error(
                `Reviewed Canonical merge source scope changed: expected ${expectedSourceQuestionIds.join(', ') || '(none)'}, current ${currentSourceQuestionIds.join(', ') || '(none)'}`,
            );
        }
    }

    if (expectedTargetReviewedQuestionIds !== null) {
        const currentTargetQuestionIds = new Set(targetRecord.question_ids || []);
        const missingReviewedQuestionIds = expectedTargetReviewedQuestionIds.filter(
            (questionId) => !currentTargetQuestionIds.has(questionId),
        );
        if (missingReviewedQuestionIds.length) {
            throw new Error(
                `Reviewed Canonical merge target scope changed; reviewed Questions no longer belong to target: ${missingReviewedQuestionIds.join(', ')}`,
            );
        }
    }
}

function reviewMigrationSummary(reviewMigration, reviewSnapshot) {
    return {
        source_progress_found: reviewMigration.progress.source_found,
        target_progress_found: reviewMigration.progress.target_found,
        migrated_session_event_count: reviewSnapshot.source_session_event_count,
    };
}

function invalidatedAnswerSummary(answerMerge) {
    if (!answerMerge.target_invalidation) return null;
    return {
        canonical_id: answerMerge.target_invalidation.canonical_id,
        version: answerMerge.target_invalidation.next_metadata.version,
        status: answerMerge.target_invalidation.next_metadata.status,
        quality_tier: answerMerge.target_invalidation.next_metadata.quality_tier,
    };
}

function archivedAnswerSummary(answerMerge) {
    if (!answerMerge.source_archive) return null;
    return {
        canonical_id: answerMerge.source_archive.canonical_id,
        source_answer_status: answerMerge.source_archive.source_answer_status,
        target_canonical_id: answerMerge.source_archive.target_canonical_id,
    };
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
    const answerRepository = assertAnswerRepository(dependencies.answerRepository);
    const mutationGateway = assertCanonicalMutationGateway(dependencies.mutationGateway);
    const integrityChecker = assertCanonicalIntegrityChecker(dependencies.integrityChecker);
    const taxonomy = dependencies.taxonomy;
    const clock = dependencies.clock || (() => new Date().toISOString());

    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }
    if (typeof clock !== 'function') throw new Error('clock must be a function');

    return async function mergeCanonicalUseCase(input = {}) {
        const targetId = input.target;
        const sourceId = input.source;
        const reason = input.reason;
        if (!targetId || !sourceId || !reason) {
            throw new Error('target, source, and reason are required');
        }
        if (targetId === sourceId) throw new Error('target and source must be different');

        const [
            targetSnapshot,
            sourceSnapshot,
            targetBindingSnapshot,
            sourceBindingSnapshot,
            reviewSnapshot,
            answerSnapshot,
        ] = await Promise.all([
            canonicalRepository.get(targetId),
            canonicalRepository.get(sourceId),
            questionBindingRepository.findByCanonical(targetId),
            questionBindingRepository.findByCanonical(sourceId),
            reviewRepository.loadMergeState(targetId, sourceId),
            answerRepository.loadMergeState(targetId, sourceId),
        ]);

        if (!targetSnapshot) throw new Error(`Target canonical not found: ${targetId}`);
        if (!sourceSnapshot) throw new Error(`Source canonical not found: ${sourceId}`);
        assertSnapshot(targetSnapshot, 'target canonical', 'record');
        assertSnapshot(sourceSnapshot, 'source canonical', 'record');
        assertSnapshot(targetBindingSnapshot, 'target question bindings', 'bindings');
        assertSnapshot(sourceBindingSnapshot, 'source question bindings', 'bindings');
        assertReviewSnapshot(reviewSnapshot);
        assertAnswerSnapshot(answerSnapshot);
        assertReviewedMergeScope(input, targetSnapshot.record, sourceSnapshot.record);

        const merged = mergeCanonical(targetSnapshot.record, sourceSnapshot.record);
        const mergedQuestionIds = uniqueSorted(merged.question_ids);
        const questionSnapshots = await Promise.all(
            mergedQuestionIds.map((questionId) => questionBindingRepository.findByQuestionId(questionId)),
        );
        questionSnapshots.forEach((snapshot, index) => {
            assertSnapshot(snapshot, `question ${mergedQuestionIds[index]} bindings`, 'bindings');
            if (!Array.isArray(snapshot.bindings)) {
                throw new Error(`question ${mergedQuestionIds[index]} snapshot bindings must be an array`);
            }
        });
        const mergedQuestionRows = questionSnapshots.flatMap((snapshot) => snapshot.bindings);
        const refreshedMerged = refreshCanonicalFromQuestions(merged, mergedQuestionRows, taxonomy);
        const movedQuestionIds = uniqueSorted(sourceSnapshot.record.question_ids);
        const mergedAt = clock();
        const mergedDate = String(mergedAt).slice(0, 10);
        const reviewMigration = planCanonicalReviewMigration({
            targetCanonicalId: targetId,
            sourceCanonicalId: sourceId,
            targetItems: reviewSnapshot.target_items,
            sourceItems: reviewSnapshot.source_items,
            updatedAtFallback: mergedDate,
        });
        const answerMerge = planCanonicalAnswerMerge({
            targetCanonicalId: targetId,
            sourceCanonicalId: sourceId,
            targetAnswer: answerSnapshot.target_answer,
            sourceAnswer: answerSnapshot.source_answer,
            sourceArchiveExists: answerSnapshot.source_archive_exists,
            updatedAt: mergedDate,
        });
        const reviewSummary = reviewMigrationSummary(reviewMigration, reviewSnapshot);
        const invalidatedTargetAnswer = invalidatedAnswerSummary(answerMerge);
        const archivedSourceAnswer = archivedAnswerSummary(answerMerge);
        const plan = createCanonicalMutationPlan({
            operation: 'merge',
            expected_revisions: [
                expectedRevision(targetSnapshot),
                expectedRevision(sourceSnapshot),
                expectedRevision(targetBindingSnapshot),
                expectedRevision(sourceBindingSnapshot),
                expectedRevision(reviewSnapshot),
                expectedRevision(answerSnapshot),
                ...questionSnapshots.map(expectedRevision),
            ],
            changes: {
                canonical_upserts: [refreshedMerged],
                canonical_removals: [sourceId],
                question_rebindings: movedQuestionIds.map((questionId) => ({
                    question_id: questionId,
                    from_canonical_id: sourceId,
                    to_canonical_id: targetId,
                })),
                review_migrations: [reviewMigration],
                answer_invalidations: answerMerge.target_invalidation
                    ? [answerMerge.target_invalidation]
                    : [],
                answer_archives: answerMerge.source_archive
                    ? [answerMerge.source_archive]
                    : [],
                rebuild_indexes: true,
                history_entry: {
                    schema_version: 'canonical_merge.v1',
                    merged_at: mergedAt,
                    target: targetId,
                    source: sourceId,
                    reason,
                    moved_question_ids: movedQuestionIds,
                    review_migration: reviewSummary,
                    invalidated_target_answer: invalidatedTargetAnswer,
                    archived_source_answer: archivedSourceAnswer,
                },
            },
        });

        const preflightResult = await mutationGateway.preflight(plan);
        const commitResult = await mutationGateway.commit(plan, preflightResult);

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
        const integrity = assertIntegrityReport(await integrityChecker.check());

        return {
            ok: integrity.ok,
            target: targetId,
            source: sourceId,
            reason,
            canonical_count: commitResult?.canonical_count ?? null,
            moved_question_ids: movedQuestionIds,
            assigned_question_rows: (postTargetBindings?.bindings || []).length,
            review_migration: reviewSummary,
            invalidated_target_answer: invalidatedTargetAnswer,
            archived_source_answer: archivedSourceAnswer,
            integrity,
            plan,
            commit: commitResult || null,
        };
    };
}

module.exports = {
    createMergeCanonicalUseCase,
};
