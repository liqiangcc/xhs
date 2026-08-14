'use strict';

const { isDue } = require('../../domain/review/progress-policy');
const { rankReviewRows } = require('../../domain/review/ranking-policy');
const { createReviewQueueStateLoader } = require('./review-queue-state');

function createReviewTodayUseCase(dependencies = {}) {
    const loadReviewQueueState = createReviewQueueStateLoader(dependencies);

    return function reviewToday(input = {}) {
        const state = loadReviewQueueState(input);
        const dueRows = rankReviewRows(
            state.rows.filter((row) => isDue(row.progress, input.date)),
            { strategy: state.strategy, date: input.date },
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
