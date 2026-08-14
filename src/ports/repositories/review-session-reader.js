'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewSessionReader exposes parsed ReviewSession sources for integrity/query
 * use cases. Each entry carries an opaque source label plus either a parsed
 * session or a parse_error fact. Filesystem paths remain adapter-owned details.
 */
function assertReviewSessionReader(reader) {
    return assertPort(reader, 'ReviewSessionReader', ['list']);
}

module.exports = {
    assertReviewSessionReader,
};
