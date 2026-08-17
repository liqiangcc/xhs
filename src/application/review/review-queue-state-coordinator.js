'use strict';

const {
    assertCanonicalCatalogRepository,
} = require('../../ports/repositories/canonical-catalog-repository');
const {
    assertQuestionCatalogRepository,
} = require('../../ports/repositories/question-catalog-repository');
const {
    assertReviewProgressRepository,
} = require('../../ports/repositories/review-progress-repository');
const {
    assertReviewIssueLinkReader,
} = require('../../ports/repositories/review-issue-link-reader');
const {
    assertReviewStrategyReader,
} = require('../../ports/services/review-strategy-reader');
const { ensureProgressItems } = require('../../domain/review/progress-policy');
const { createReviewQueueRows } = require('./review-queue-rows');

function createReviewQueueStateCoordinator(dependencies = {}) {
    const canonicalCatalogRepository = assertCanonicalCatalogRepository(
        dependencies.canonicalCatalogRepository,
    );
    const questionCatalogRepository = assertQuestionCatalogRepository(
        dependencies.questionCatalogRepository,
    );
    const progressRepository = assertReviewProgressRepository(
        dependencies.progressRepository,
    );
    const issueLinkReader = assertReviewIssueLinkReader(dependencies.issueLinkReader);
    const strategyReader = assertReviewStrategyReader(dependencies.strategyReader);

    return function buildReviewQueueState(input = {}) {
        if (!input.date || typeof input.date !== 'string') {
            throw new Error('review date is required');
        }

        const canonicalRecords = canonicalCatalogRepository.list();
        const questionRows = questionCatalogRepository.list();
        const snapshot = progressRepository.snapshot({ date: input.date });
        const progress = ensureProgressItems(snapshot.progress, canonicalRecords, input.date);

        if (input.write_progress !== false) {
            progressRepository.save(progress, {
                date: input.date,
                expected_revision: snapshot.revision,
            });
        }

        const issueLinks = input.with_issues
            ? (issueLinkReader.load().items || [])
            : [];
        const strategy = strategyReader.read();
        const rows = createReviewQueueRows(canonicalRecords, progress, {
            questions: questionRows,
            issueLinks,
            includeIssues: Boolean(input.with_issues),
        });

        return {
            progress,
            strategy,
            rows,
        };
    };
}

module.exports = {
    createReviewQueueStateCoordinator,
};
