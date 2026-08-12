'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalCandidateRepository exposes immutable candidate snapshots used by
 * the Accept application use case.
 *
 * get(candidateId) returns null when missing, otherwise:
 *   { candidate, resource, revision }
 *
 * The revision is adapter-owned and lets Application reject a candidate that
 * changed between planning and mutation preflight.
 */
function assertCanonicalCandidateRepository(repository) {
    return assertPort(
        repository,
        'CanonicalCandidateRepository',
        ['get'],
    );
}

module.exports = {
    assertCanonicalCandidateRepository,
};
