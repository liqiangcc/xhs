'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalRepository is a read-oriented outbound port.
 *
 * get(canonicalId) should return null or a snapshot shaped like:
 *   { record, resource, revision }
 * where resource/revision are opaque adapter-owned concurrency tokens.
 * Application may carry them into a MutationPlan but must not interpret their
 * format or derive filesystem/database details from them.
 */
function assertCanonicalRepository(repository) {
    return assertPort(repository, 'CanonicalRepository', ['get']);
}

module.exports = {
    assertCanonicalRepository,
};
