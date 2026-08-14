'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewStrategyProvider supplies the declarative review_strategy.v1 weights.
 * Domain owns how those weights are interpreted.
 */
function assertReviewStrategyProvider(provider) {
    return assertPort(provider, 'ReviewStrategyProvider', ['load']);
}

module.exports = {
    assertReviewStrategyProvider,
};
