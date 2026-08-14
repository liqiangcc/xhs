'use strict';

const { assertPort } = require('../port-contract');

/**
 * @deprecated Compatibility-only Port for historical/manual canonical_candidates.v1.
 * Current Dedup Suggest/Decide/Apply flows MUST NOT depend on this Port.
 * New candidate/review capabilities belong to RelationCandidate repositories.
 *
 * get(candidateId) returns null when missing, otherwise:
 *   { candidate, resource, revision }
 */
function assertLegacyCanonicalCandidateRepository(repository) {
    return assertPort(
        repository,
        'LegacyCanonicalCandidateRepository',
        ['get'],
    );
}

module.exports = {
    assertLegacyCanonicalCandidateRepository,
};
