'use strict';

const { assertPort } = require('../port-contract');

/**
 * LegacyCanonicalCandidateRepository is a compatibility-only read Port for
 * historical `canonical_candidates.v1` manifests consumed by `canonical accept`.
 *
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
