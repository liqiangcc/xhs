'use strict';

const { addDays } = require('../../domain/review/progress-policy');
const { rankReviewRows } = require('../../domain/review/ranking-policy');
const { createReviewQueueStateCoordinator } = require('./review-queue-state-coordinator');

function createReviewNextUseCase(dependencies = {}) {
    const buildReviewQueueState = createReviewQueueStateCoordinator(dependencies);

    return function reviewNext(input = {}) {
        const state = buildReviewQueueState(input);
        const days = Number(input.days || 7);
        const maxDate = addDays(input.date, days);
        const rows = rankReviewRows(
            state.rows.filter((row) =>
                !row.progress.next_review_at || row.progress.next_review_at <= maxDate
            ),
            { strategy: state.strategy, date: input.date },
        ).slice(0, Number(input.limit || 20));

        return {
            schema_version: 'review_next.v1',
            date: input.date,
            days,
            returned_count: rows.length,
            rows,
        };
    };
}

module.exports = {
    createReviewNextUseCase,
};
