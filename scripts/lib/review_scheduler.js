'use strict';

const path = require('path');
const { readJson } = require('./io');
const { todayString } = require('./review_store');
const {
    scoreReviewRow: scoreReviewRowPolicy,
    rankReviewRows: rankReviewRowsPolicy,
} = require('../../src/domain/review/ranking-policy');

const DEFAULT_STRATEGY_PATH = path.resolve(__dirname, '..', '..', 'config', 'review_strategy.json');

function loadReviewStrategy(options = {}) {
    return readJson(options.strategyPath || DEFAULT_STRATEGY_PATH);
}

function scoreReviewRow(row, options = {}) {
    return scoreReviewRowPolicy(row, {
        strategy: options.strategy || loadReviewStrategy(options),
        date: todayString(options),
    });
}

function rankReviewRows(rows, options = {}) {
    return rankReviewRowsPolicy(rows, {
        strategy: options.strategy || loadReviewStrategy(options),
        date: todayString(options),
    });
}

module.exports = {
    DEFAULT_STRATEGY_PATH,
    loadReviewStrategy,
    scoreReviewRow,
    rankReviewRows,
};
