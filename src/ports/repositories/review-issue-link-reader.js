'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewIssueLinkReader exposes optional Review issue-link facts.
 * It does not decide whether callers requested issue enrichment.
 */
function assertReviewIssueLinkReader(reader) {
    return assertPort(reader, 'ReviewIssueLinkReader', ['load']);
}

module.exports = {
    assertReviewIssueLinkReader,
};
