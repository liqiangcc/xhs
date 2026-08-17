'use strict';

const path = require('path');
const { readJson } = require('../../../scripts/lib/io');

const DEFAULT_STRATEGY_PATH = path.resolve(__dirname, '..', '..', '..', 'config', 'review_strategy.json');

function createFileReviewStrategyReaderAdapter(options = {}) {
    const strategyPath = options.strategyPath || DEFAULT_STRATEGY_PATH;

    return {
        read() {
            return readJson(strategyPath);
        },
    };
}

module.exports = {
    DEFAULT_STRATEGY_PATH,
    createFileReviewStrategyReaderAdapter,
};
