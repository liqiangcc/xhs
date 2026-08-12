'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalRepository is a read-oriented outbound port.
 *
 * get(canonicalId) should return null or a snapshot shaped like:
 *   { record, revision }
 * where revision is an opaque adapter-owned concurrency token. Application may
 * compare/pass the token but must not interpret its format.
 */
function assertCanonicalRepository(repository) {
    return assertPort(repository, 'CanonicalRepository', ['get']);
}

module.exports = {
    assertCanonicalRepository,
};
