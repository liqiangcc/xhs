'use strict';

const path = require('path');
const { readJson } = require('../../../scripts/lib/io');

function createReviewStrategyProvider(options = {}) {
    if (!options.root) throw new Error('Review strategy provider root is required');
    const strategyPath = options.strategyPath || path.join(options.root, 'config', 'review_strategy.json');

    return {
        load() {
            return readJson(strategyPath);
        },
    };
}

module.exports = {
    createReviewStrategyProvider,
};
