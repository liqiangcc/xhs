'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewProgressWriter persists an already-decided ReviewProgress store.
 * It does not initialize missing items or choose whether a write should occur.
 */
function assertReviewProgressWriter(writer) {
    return assertPort(writer, 'ReviewProgressWriter', ['write']);
}

module.exports = {
    assertReviewProgressWriter,
};
