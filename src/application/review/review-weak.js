'use strict';

const { isWeakReviewProgress } = require('../../domain/review/weak-policy');
const { rankReviewRows } = require('../../domain/review/ranking-policy');
const { createReviewQueueStateCoordinator } = require('./review-queue-state-coordinator');

function createReviewWeakUseCase(dependencies = {}) {
    const buildReviewQueueState = createReviewQueueStateCoordinator(dependencies);

    return function reviewWeak(input = {}) {
        const state = buildReviewQueueState(input);
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
