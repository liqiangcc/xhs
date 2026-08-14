'use strict';

const crypto = require('crypto');
const { readJson, stableStringify } = require('../../../scripts/lib/io');

function hashValue(value) {
    return crypto.createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function revisionForLegacyCandidateResource(paths, resource) {
    if (!String(resource).startsWith('canonical-candidate:')) {
        throw new Error(`Unsupported filesystem canonical candidate resource: ${resource}`);
    }
    const candidateId = String(resource).slice('canonical-candidate:'.length);
    const manifest = readJson(paths.legacyCandidateManifest || paths.candidateManifest, {
        schema_version: 'canonical_candidates.v1',
        candidates: [],
    });
    const candidate = (manifest.candidates || [])
        .find((item) => item.candidate_id === candidateId) || null;
    return hashValue(candidate);
}

module.exports = {
    revisionForLegacyCandidateResource,
};
