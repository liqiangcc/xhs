'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewProgressReader exposes the current ReviewProgress store as read-only
 * storage-agnostic facts.
 */
function assertReviewProgressReader(reader) {
    return assertPort(reader, 'ReviewProgressReader', ['load']);
}

module.exports = {
    assertReviewProgressReader,
};
