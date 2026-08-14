'use strict';

// Deprecated compatibility re-export. New production code should depend on
// LegacyCanonicalCandidateRepository so `canonical_candidates.v1` cannot be
// confused with the current Dedup RelationCandidate model.
const {
    assertLegacyCanonicalCandidateRepository,
} = require('./legacy-canonical-candidate-repository');

module.exports = {
    assertCanonicalCandidateRepository: assertLegacyCanonicalCandidateRepository,
};
