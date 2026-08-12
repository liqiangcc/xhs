'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { createApplication } = require('../src/bootstrap/create-application');
const { createAcceptCanonicalUseCase } = require('../src/application/canonical/accept-canonical');
const { loadTaxonomy } = require('../src/infrastructure/config/taxonomy-provider');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const {
    createFsCanonicalRepositories,
} = require('../src/infrastructure/filesystem/canonical-repositories');
const {
    createFsCanonicalCandidateRepository,
} = require('../src/infrastructure/filesystem/canonical-candidate-repositories');
const {
    createFsCanonicalMutationStore,
} = require('../src/infrastructure/filesystem/fs-canonical-mutation-store');
const { readJson, readJsonl, writeJson, writeJsonl } = require('../scripts/lib/io');
const { getIndexPaths } = require('../scripts/lib/index_store');

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
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-app-fs-accept-'));
    const paths = createCanonicalFsPaths(root);
    writeJsonl(paths.canonicalQuestions, []);
    writeJsonl(paths.questions, [
        question('q1', 1, null, '美团', 'Redis 为什么快？'),
        question('q2', 2, null, '字节', 'Redis 单线程为什么快？'),
        question('q2', 3, null, '阿里', 'Redis 单线程为何高效？'),
    ]);
    writeJson(paths.candidateManifest, {
        schema_version: 'canonical_candidates.v1',
        candidates: [candidate()],
    });
    return { root, paths };
}

function createFilesystemUseCase(fixture, mutationStoreOverride = null) {
    const {
        canonicalRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
    } = createFsCanonicalRepositories({ root: fixture.root, paths: fixture.paths });
    const candidateRepository = createFsCanonicalCandidateRepository({
        root: fixture.root,
        paths: fixture.paths,
    });
    const mutationStore = mutationStoreOverride || createFsCanonicalMutationStore({
        root: fixture.root,
        paths: fixture.paths,
    });

    return createAcceptCanonicalUseCase({
        candidateRepository,
        canonicalIdentityRepository: canonicalRepository,
        canonicalQuestionOwnershipRepository,
        questionBindingRepository,
        mutationStore,
        taxonomy: loadTaxonomy(),
    });
}

function cleanup(fixture) {
    fs.rmSync(fixture.root, { recursive: true, force: true });
}

test('filesystem candidate and ownership snapshots change only when their semantic resources change', async () => {
    const fixture = createFixture();
    try {
        const candidateRepository = createFsCanonicalCandidateRepository({
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

        writeJson(fixture.paths.candidateManifest, {
            schema_version: 'canonical_candidates.v1',
            generated_at: 'unrelated manifest metadata',
            candidates: [candidate()],
        });
        const candidateMetadataOnly = await candidateRepository.get('cand_accept');
        assert.equal(candidateMetadataOnly.revision, candidateBefore.revision);

        writeJson(fixture.paths.candidateManifest, {
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

test('composition root runs accept through real filesystem adapters and rebuilds indexes', async () => {
    const fixture = createFixture();
    try {
        const app = createApplication({ root: fixture.root });
        const result = await app.canonical.accept({
            candidate_id: 'cand_accept',
            canonical_id: 'cq_redis_fast',
        });

        assert.equal(result.ok, true);
        assert.equal(result.canonical_count, 1);
        assert.equal(result.updated_question_rows, 3);
        assert.equal(result.commit.committed, true);
        assert.equal(result.commit.recoverable, true);
        assert.deepEqual(
            result.plan.expected_revisions.map((item) => item.resource),
            [
                'canonical-candidate:cand_accept',
                'canonical:cq_redis_fast',
                'question-bindings-by-question:q1',
                'question-bindings-by-question:q2',
                'canonical-ownership-by-question:q1',
                'canonical-ownership-by-question:q2',
            ],
        );

        const records = readJsonl(fixture.paths.canonicalQuestions, []);
        assert.equal(records.length, 1);
        assert.equal(records[0].canonical_id, 'cq_redis_fast');
        assert.deepEqual(records[0].question_ids, ['q1', 'q2']);
        assert.equal(records[0].frequency, 3);
        assert.deepEqual(
            records[0].companies,
            ['美团', '字节', '阿里'].sort((a, b) => a.localeCompare(b, 'zh')),
        );

        const rows = readJsonl(fixture.paths.questions, []);
        assert.equal(rows.every((row) => row.canonical_id === 'cq_redis_fast'), true);

        const hotspot = readJson(getIndexPaths(fixture.paths.indexDir).hotspot);
        assert.equal(hotspot.total_hotspots, 1);
        assert.equal(hotspot.entries[0].canonical_id, 'cq_redis_fast');
        assert.equal(hotspot.entries[0].frequency, 3);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture);
    }
});

test('filesystem preflight rejects a candidate changed after accept planning', async () => {
    const fixture = createFixture();
    try {
        const realStore = createFsCanonicalMutationStore({ root: fixture.root, paths: fixture.paths });
        const mutationStore = {
            ...realStore,
            async preflight(plan) {
                writeJson(fixture.paths.candidateManifest, {
                    schema_version: 'canonical_candidates.v1',
                    candidates: [candidate({ aliases: ['concurrent candidate edit'] })],
                });
                return realStore.preflight(plan);
            },
        };
        const accept = createFilesystemUseCase(fixture, mutationStore);

        await assert.rejects(
            accept({ candidate_id: 'cand_accept', canonical_id: 'cq_redis_fast' }),
            /Revision mismatch for canonical-candidate:cand_accept/,
        );
        assert.deepEqual(readJsonl(fixture.paths.canonicalQuestions, []), []);
        assert.equal(readJsonl(fixture.paths.questions, []).every((row) => row.canonical_id === null), true);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture);
    }
});

test('filesystem preflight rejects a canonical ownership race after accept planning', async () => {
    const fixture = createFixture();
    try {
        const realStore = createFsCanonicalMutationStore({ root: fixture.root, paths: fixture.paths });
        const mutationStore = {
            ...realStore,
            async preflight(plan) {
                writeJsonl(fixture.paths.canonicalQuestions, [canonical('cq_other', ['q1'])]);
                return realStore.preflight(plan);
            },
        };
        const accept = createFilesystemUseCase(fixture, mutationStore);

        await assert.rejects(
            accept({ candidate_id: 'cand_accept', canonical_id: 'cq_redis_fast' }),
            /Revision mismatch for canonical-ownership-by-question:q1/,
        );
        const records = readJsonl(fixture.paths.canonicalQuestions, []);
        assert.deepEqual(records.map((record) => record.canonical_id), ['cq_other']);
        assert.equal(readJsonl(fixture.paths.questions, []).every((row) => row.canonical_id === null), true);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture);
    }
});
