'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { revisionForResource } = require('../src/infrastructure/filesystem/canonical-repositories');
const { writeJson } = require('../scripts/lib/io');

function candidate(overrides = {}) {
    return {
        candidate_id: 'cand_accept',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？'],
        question_ids: ['q1'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: 1,
        review_priority: 'P2',
        ...overrides,
    };
}

function writeManifest(paths, overrides = {}) {
    writeJson(paths.legacyCandidateManifest, {
        schema_version: 'canonical_candidates.v1',
        candidates: [candidate()],
        ...overrides,
    });
}

test('legacy canonical-candidate CAS revision is semantic without retaining a repository capability', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-legacy-candidate-cas-'));
    try {
        const paths = createCanonicalFsPaths(root);
        const resource = 'canonical-candidate:cand_accept';
        writeManifest(paths);

        const before = revisionForResource(paths, resource);

        writeManifest(paths, { generated_at: 'metadata-only-change' });
        assert.equal(revisionForResource(paths, resource), before);

        writeJson(paths.legacyCandidateManifest, {
            schema_version: 'canonical_candidates.v1',
            candidates: [candidate({ aliases: ['semantic candidate change'] })],
        });
        assert.notEqual(revisionForResource(paths, resource), before);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
