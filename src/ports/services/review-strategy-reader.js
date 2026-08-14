'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewStrategyReader supplies the declarative review_strategy.v1 weights.
 * Domain owns how those weights are interpreted.
 */
function assertReviewStrategyReader(reader) {
    return assertPort(reader, 'ReviewStrategyReader', ['read']);
}

module.exports = {
    assertReviewStrategyReader,
};
