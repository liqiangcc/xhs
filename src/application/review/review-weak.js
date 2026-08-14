'use strict';

const { isWeakReviewProgress } = require('../../domain/review/weak-policy');
const { rankReviewRows } = require('../../domain/review/ranking-policy');
const { createReviewQueueStateLoader } = require('./review-queue-state');

function createReviewWeakUseCase(dependencies = {}) {
    const loadReviewQueueState = createReviewQueueStateLoader(dependencies);

    return function reviewWeak(input = {}) {
        const state = loadReviewQueueState(input);
        const rows = rankReviewRows(
            state.rows.filter((row) => isWeakReviewProgress(row.progress)),
            { strategy: state.strategy, date: input.date },
        ).slice(0, Number(input.limit || 20));

        return {
            schema_version: 'review_weak.v1',
            returned_count: rows.length,
            rows,
        };
    };
}

module.exports = {
    createReviewWeakUseCase,
};
