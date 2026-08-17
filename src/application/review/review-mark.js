'use strict';

const {
    assertCanonicalCatalogRepository,
} = require('../../ports/repositories/canonical-catalog-repository');
const {
    assertReviewMutationGateway,
} = require('../../ports/repositories/review-mutation-gateway');
const { ensureProgressItems } = require('../../domain/review/progress-policy');
const { applyReviewResult } = require('../../domain/review/review-result-policy');
const {
    normalizeReviewMarkInput,
    createReviewSessionEvent,
} = require('../../domain/review/review-mark-policy');

function createReviewMarkUseCase(dependencies = {}) {
    const canonicalCatalogRepository = assertCanonicalCatalogRepository(
        dependencies.canonicalCatalogRepository,
    );
    const mutationGateway = assertReviewMutationGateway(dependencies.mutationGateway);

    return function reviewMark(input = {}) {
        const canonicalId = input.canonical_id;
        const result = input.result;
        if (!canonicalId || !result) {
            throw new Error(
                'Usage: review mark --canonical-id <id> --result <again|hard|good|easy>',
            );
        }
        if (!input.date || typeof input.date !== 'string') {
            throw new Error('review date is required');
        }

        const canonicalRecords = canonicalCatalogRepository.list();
        if (!canonicalRecords.some((record) => record.canonical_id === canonicalId)) {
            throw new Error(`Canonical not found: ${canonicalId}`);
        }

        const mark = normalizeReviewMarkInput(input);
        const snapshot = mutationGateway.snapshot({ date: input.date });
        const progress = ensureProgressItems(snapshot.progress, canonicalRecords, input.date);
        const current = (progress.items || [])
            .find((item) => item.canonical_id === canonicalId);
        const updated = applyReviewResult(current, result, input.date);
        const nextProgress = {
            ...progress,
            updated_at: input.date,
            items: (progress.items || []).map((item) =>
                item.canonical_id === canonicalId ? updated : item
            ),
        };
        const sessionEvent = createReviewSessionEvent({
            canonical_id: canonicalId,
            result,
            progress: updated,
            date: input.date,
            mark,
        });

        const dryRun = input.write_mutation === false;
        let sessionPath = null;
        if (!dryRun) {
            const committed = mutationGateway.commit({
                schema_version: 'review_mutation.v1',
                expected_revision: snapshot.revision,
                date: input.date,
                progress: nextProgress,
                session_event: sessionEvent,
            });
            sessionPath = committed.session_path;
        }

        return {
            schema_version: 'review_mark_result.v1',
            ok: true,
            dry_run: dryRun,
            canonical_id: canonicalId,
            result,
            progress: updated,
            session_event: sessionEvent,
            session_path: sessionPath,
        };
    };
}

module.exports = {
    createReviewMarkUseCase,
};
