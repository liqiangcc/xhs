'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalIdentityRepository exposes identity-state snapshots for optimistic
 * create-if-absent checks.
 *
 * inspect(canonicalId) always returns:
 *   { record: object|null, resource, revision }
 *
 * Unlike CanonicalRepository.get(), an absent Canonical still has an opaque
 * adapter-owned revision. Application can carry that revision into a
 * MutationPlan so preflight rejects a concurrent create of the same id.
 */
function assertCanonicalIdentityRepository(repository) {
    return assertPort(
        repository,
        'CanonicalIdentityRepository',
        ['inspect'],
    );
}

module.exports = {
    assertCanonicalIdentityRepository,
};
