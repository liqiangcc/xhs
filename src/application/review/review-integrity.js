'use strict';

const {
    assertCanonicalCatalogRepository,
} = require('../../ports/repositories/canonical-catalog-repository');
const {
    assertReviewProgressReader,
} = require('../../ports/repositories/review-progress-reader');
const {
    assertReviewSessionReader,
} = require('../../ports/repositories/review-session-reader');
const { evaluateReviewIntegrity } = require('../../domain/review/integrity-policy');

function createReviewIntegrityUseCase(dependencies = {}) {
    const canonicalCatalogRepository = assertCanonicalCatalogRepository(
        dependencies.canonicalCatalogRepository,
    );
    const progressReader = assertReviewProgressReader(dependencies.progressReader);
    const sessionReader = assertReviewSessionReader(dependencies.sessionReader);

    return function reviewIntegrity() {
        const evaluation = evaluateReviewIntegrity({
            canonical_records: canonicalCatalogRepository.list(),
            progress: progressReader.load(),
            session_sources: sessionReader.list(),
        });

        return {
            schema_version: 'review_integrity.v1',
            ...evaluation,
            stale_session_events: evaluation.stale_session_events.map(({ source, ...event }) => ({
                file: source,
                ...event,
            })),
        };
    };
}

module.exports = {
    createReviewIntegrityUseCase,
};
