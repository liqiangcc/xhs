'use strict';

const {
    assertCanonicalCatalogRepository,
} = require('../../ports/repositories/canonical-catalog-repository');
const {
    assertQuestionCatalogRepository,
} = require('../../ports/repositories/question-catalog-repository');
const {
    assertReviewProgressReader,
} = require('../../ports/repositories/review-progress-reader');
const {
    assertReviewProgressWriter,
} = require('../../ports/repositories/review-progress-writer');
const {
    assertReviewIssueLinkReader,
} = require('../../ports/repositories/review-issue-link-reader');
const {
    assertReviewStrategyProvider,
} = require('../../ports/services/review-strategy-provider');
const {
    ensureProgressItems,
    isDue,
} = require('../../domain/review/progress-policy');
const { rankReviewRows } = require('../../domain/review/ranking-policy');
const { createReviewQueueRows } = require('./review-queue-rows');

function createReviewTodayUseCase(dependencies = {}) {
    const canonicalCatalogRepository = assertCanonicalCatalogRepository(
        dependencies.canonicalCatalogRepository,
    );
    const questionCatalogRepository = assertQuestionCatalogRepository(
        dependencies.questionCatalogRepository,
    );
    const progressReader = assertReviewProgressReader(dependencies.progressReader);
    const progressWriter = assertReviewProgressWriter(dependencies.progressWriter);
    const issueLinkReader = assertReviewIssueLinkReader(dependencies.issueLinkReader);
    const strategyProvider = assertReviewStrategyProvider(dependencies.strategyProvider);

    return function reviewToday(input = {}) {
        if (!input.date || typeof input.date !== 'string') {
            throw new Error('review date is required');
        }

        const canonicalRecords = canonicalCatalogRepository.list();
        const questionRows = questionCatalogRepository.list();
        const loadedProgress = progressReader.load();
        const progress = ensureProgressItems(loadedProgress, canonicalRecords, input.date);

        if (input.write_progress !== false) {
            progressWriter.write(progress);
        }

        const issueLinks = input.with_issues
            ? (issueLinkReader.load().items || [])
            : [];
        const strategy = strategyProvider.load();
        const rows = createReviewQueueRows(canonicalRecords, progress, {
            questions: questionRows,
            issueLinks,
            includeIssues: Boolean(input.with_issues),
        });
        const dueRows = rankReviewRows(
            rows.filter((row) => isDue(row.progress, input.date)),
            { strategy, date: input.date },
        );
        const limit = Number(input.limit || 20);
        const selected = dueRows.slice(0, limit);

        return {
            schema_version: 'review_today.v1',
            date: input.date,
            total_due_count: dueRows.length,
            returned_count: selected.length,
            rows: selected,
        };
    };
}

module.exports = {
    createReviewTodayUseCase,
};
