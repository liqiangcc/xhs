'use strict';

const crypto = require('crypto');
const { readJson, stableStringify } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function clone(value) {
    return structuredClone(value);
}

function candidateResource(candidateId) {
    return `canonical-candidate:${candidateId}`;
}

function hashValue(value) {
    return crypto.createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function readCandidateManifest(paths) {
    return readJson(paths.candidateManifest, {
        schema_version: 'canonical_candidates.v1',
        candidates: [],
    });
}

function findCandidate(paths, candidateId) {
    const manifest = readCandidateManifest(paths);
    return (manifest.candidates || []).find((item) => item.candidate_id === candidateId) || null;
}

function revisionForCandidateResource(paths, resource) {
    if (!String(resource).startsWith('canonical-candidate:')) {
        throw new Error(`Unsupported filesystem canonical candidate resource: ${resource}`);
    }
    const candidateId = String(resource).slice('canonical-candidate:'.length);
    return hashValue(findCandidate(paths, candidateId));
}

function createFsCanonicalCandidateRepository(options = {}) {
    if (!options.root) throw new Error('Filesystem canonical candidate repository root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        async get(candidateId) {
            const candidate = findCandidate(paths, candidateId);
            if (!candidate) return null;
            const resource = candidateResource(candidateId);
            return {
                candidate: clone(candidate),
                resource,
                revision: revisionForCandidateResource(paths, resource),
            };
        },
    };
}

module.exports = {
    candidateResource,
    revisionForCandidateResource,
    createFsCanonicalCandidateRepository,
};
