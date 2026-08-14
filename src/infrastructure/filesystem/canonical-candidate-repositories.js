'use strict';

// Deprecated compatibility re-export. New production wiring must import
// `legacy-canonical-candidate-repositories` explicitly so historical
// canonical_candidates.v1 input cannot be mistaken for the current Dedup
// RelationCandidate model.
const {
    candidateResource,
    revisionForCandidateResource,
    createFsLegacyCanonicalCandidateRepository,
} = require('./legacy-canonical-candidate-repositories');

module.exports = {
    candidateResource,
    revisionForCandidateResource,
    createFsCanonicalCandidateRepository: createFsLegacyCanonicalCandidateRepository,
};
