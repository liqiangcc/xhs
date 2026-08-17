'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const { createSplitCanonicalUseCase } = require('../src/application/canonical/split-canonical');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../src/infrastructure/filesystem/canonical-repositories');
const {
    createFileCanonicalMutationGatewayAdapter,
} = require('../src/infrastructure/filesystem/file-canonical-mutation-gateway-adapter');
const { readJsonl, writeJsonl } = require('../scripts/lib/io');

function canonical(id, questionIds, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: questionIds.length,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(questionId, index) {
    return {
        question_id: questionId,
        original_question: `question ${questionId}`,
        source_note_id: `note_${index}`,
        source_question_index: index,
        company: index === 1 ? '美团' : '字节',
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['Redis'],
        is_valid_for_library: true,
        canonical_id: 'cq_source',
    };
}

function passingIntegrityReport() {
    return {
        schema_version: 'canonical_quality_report.v1',
        ok: true,
    };
}

test('filesystem preflight rejects a concurrent create of a split destination id', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-split-absence-race-'));
    const paths = createCanonicalFsPaths(root);
    try {
        writeJsonl(paths.canonicalQuestions, [canonical('cq_source', ['q1', 'q2'])]);
        writeJsonl(paths.questions, [question('q1', 1), question('q2', 2)]);

        const { canonicalRepository, questionBindingRepository } = createFsCanonicalRepositories({
            root,
            paths,
        });
        const fileMutationGateway = createFileCanonicalMutationGatewayAdapter({ root, paths });
        const mutationGateway = {
            ...fileMutationGateway,
            async preflight(plan) {
                const absenceRevision = plan.expected_revisions.find(
                    (item) => item.resource === 'canonical:cq_new',
                );
                assert.ok(absenceRevision);

                const records = readJsonl(paths.canonicalQuestions, []);
                writeJsonl(paths.canonicalQuestions, [
                    ...records,
                    canonical('cq_new', ['q9'], { canonical_title: 'concurrent create' }),
                ]);
                return fileMutationGateway.preflight(plan);
            },
        };
        const split = createSplitCanonicalUseCase({
            canonicalRepository,
            canonicalIdentityRepository: canonicalRepository,
            questionBindingRepository,
            mutationGateway,
            integrityChecker: { async check() { return passingIntegrityReport(); } },
            taxonomy,
        });

        await assert.rejects(
            split({
                source: 'cq_source',
                question_id: 'q2',
                new_canonical_id: 'cq_new',
                title: 'Redis 为什么快？',
            }),
            /Revision mismatch for canonical:cq_new/,
        );

        const records = readJsonl(paths.canonicalQuestions, []);
        const source = records.find((item) => item.canonical_id === 'cq_source');
        const concurrent = records.find((item) => item.canonical_id === 'cq_new');
        assert.ok(concurrent);
        assert.deepEqual(concurrent.question_ids, ['q9']);
        assert.deepEqual(source.question_ids, ['q1', 'q2']);

        const questions = readJsonl(paths.questions, []);
        assert.deepEqual(
            questions.map((item) => [item.question_id, item.canonical_id]),
            [['q1', 'cq_source'], ['q2', 'cq_source']],
        );
        assert.equal(fs.existsSync(paths.journal), false);
        assert.equal(fs.existsSync(paths.lock), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
