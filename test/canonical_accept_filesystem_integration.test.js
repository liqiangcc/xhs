'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const {
    createFsCanonicalRepositories,
} = require('../src/infrastructure/filesystem/canonical-repositories');
const {
    createFsLegacyCanonicalCandidateRepository,
} = require('../src/infrastructure/filesystem/legacy-canonical-candidate-repositories');
const { writeJson, writeJsonl } = require('../scripts/lib/io');

function candidate(overrides = {}) {
    return {
        candidate_id: 'cand_accept',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？', 'Redis 单线程为什么快？'],
        question_ids: ['q1', 'q2'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团', '字节'],
        frequency: 2,
        review_priority: 'P2',
        ...overrides,
    };
}

function question(questionId, index, canonicalId = null, company = '美团', originalQuestion = null) {
    return {
        question_id: questionId,
        original_question: originalQuestion || `question ${questionId}`,
        source_note_id: `note_${index}`,
        source_question_index: index,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

function canonical(canonicalId, questionIds, overrides = {}) {
    return {
        canonical_id: canonicalId,
        canonical_title: canonicalId,
        aliases: [canonicalId],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['并发公司'],
        frequency: questionIds.length,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function createFixture() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-legacy-candidate-fs-'));
    const paths = createCanonicalFsPaths(root);
    writeJsonl(paths.canonicalQuestions, []);
    writeJsonl(paths.questions, [
        question('q1', 1, null, '美团', 'Redis 为什么快？'),
        question('q2', 2, null, '字节', 'Redis 单线程为什么快？'),
        question('q2', 3, null, '阿里', 'Redis 单线程为何高效？'),
    ]);
    writeJson(paths.legacyCandidateManifest, {
        schema_version: 'canonical_candidates.v1',
        candidates: [candidate()],
    });
    return { root, paths };
}

function cleanup(fixture) {
    fs.rmSync(fixture.root, { recursive: true, force: true });
}

test('legacy filesystem candidate and ownership snapshots use semantic opaque revisions', async () => {
    const fixture = createFixture();
    try {
        const candidateRepository = createFsLegacyCanonicalCandidateRepository({
            root: fixture.root,
            paths: fixture.paths,
        });
        const { canonicalQuestionOwnershipRepository } = createFsCanonicalRepositories({
            root: fixture.root,
            paths: fixture.paths,
        });

        const candidateBefore = await candidateRepository.get('cand_accept');
        const ownershipBefore = await canonicalQuestionOwnershipRepository.findOwners('q1');
        assert.equal(candidateBefore.resource, 'canonical-candidate:cand_accept');
        assert.deepEqual(ownershipBefore.canonical_ids, []);

        writeJson(fixture.paths.legacyCandidateManifest, {
            schema_version: 'canonical_candidates.v1',
            generated_at: 'unrelated manifest metadata',
            candidates: [candidate()],
        });
        const candidateMetadataOnly = await candidateRepository.get('cand_accept');
        assert.equal(candidateMetadataOnly.revision, candidateBefore.revision);

        writeJson(fixture.paths.legacyCandidateManifest, {
            schema_version: 'canonical_candidates.v1',
            candidates: [candidate({ aliases: ['concurrent candidate edit'] })],
        });
        const candidateAfter = await candidateRepository.get('cand_accept');
        assert.notEqual(candidateAfter.revision, candidateBefore.revision);

        writeJsonl(fixture.paths.canonicalQuestions, [canonical('cq_other', ['q1'])]);
        const ownershipAfter = await canonicalQuestionOwnershipRepository.findOwners('q1');
        assert.deepEqual(ownershipAfter.canonical_ids, ['cq_other']);
        assert.notEqual(ownershipAfter.revision, ownershipBefore.revision);
    } finally {
        cleanup(fixture);
    }
});
