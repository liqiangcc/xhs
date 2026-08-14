'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { mergeCanonical } = require('../src/domain/canonical/merge-policy');
const { createCanonicalMutationPlan } = require('../src/application/canonical/mutation-plan');
const { planCanonicalReviewMigration } = require('../src/application/canonical/review-migration-plan');
const { planCanonicalAnswerMerge } = require('../src/application/canonical/answer-merge-plan');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../src/infrastructure/filesystem/canonical-repositories');
const { createFsReviewRepository } = require('../src/infrastructure/filesystem/review-repositories');
const { createFsAnswerRepository } = require('../src/infrastructure/filesystem/answer-repositories');
const {
    createFileCanonicalMutationGatewayAdapter,
} = require('../src/infrastructure/filesystem/file-canonical-mutation-gateway-adapter');
const { readAnswerFile } = require('../scripts/lib/answer_store');
const { readJson, readJsonl, writeJson, writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, getIndexPaths, writeIndexes } = require('../scripts/lib/index_store');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: [],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: [],
        frequency: 0,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(questionId, canonicalId, index, company) {
    return {
        question_id: questionId,
        original_question: `question ${questionId}`,
        source_note_id: `note_${index}`,
        source_question_index: index,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['Redis'],
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

function progress(canonicalId, overrides = {}) {
    return {
        canonical_id: canonicalId,
        status: 'learning',
        level: 2,
        review_count: 3,
        last_reviewed_at: '2026-08-01',
        next_review_at: '2026-08-10',
        confidence: 0.7,
        difficulty: 3,
        mistake_count: 0,
        updated_at: '2026-08-01',
        ...overrides,
    };
}

function answerContent(canonicalId, overrides = {}) {
    const metadata = {
        schema_version: 'answer.v1',
        canonical_id: canonicalId,
        version: 1,
        status: 'draft',
        quality_tier: 'long_tail_baseline',
        updated_at: '2026-08-01',
        ...overrides,
    };
    return [
        `<!-- xhs-answer: ${JSON.stringify(metadata)} -->`,
        `# ${canonicalId}`,
        '',
        'answer body',
        '',
    ].join('\n');
}

function createFixture() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-fs-answer-'));
    const paths = createCanonicalFsPaths(root);
    const canonicals = [
        canonical('cq_target', {
            canonical_title: 'Redis 为什么快？',
            aliases: ['Redis 为什么快？'],
            question_ids: ['q1'],
            companies: ['美团'],
            frequency: 1,
            review_priority: 'P1',
        }),
        canonical('cq_source', {
            canonical_title: 'Redis 单线程为什么快？',
            aliases: ['Redis 单线程为什么快？'],
            question_ids: ['q2'],
            companies: ['字节'],
            frequency: 1,
            review_priority: 'P0',
        }),
    ];
    const questions = [
        question('q1', 'cq_target', 1, '美团'),
        question('q2', 'cq_source', 2, '字节'),
    ];

    writeJsonl(paths.canonicalQuestions, canonicals);
    writeJsonl(paths.questions, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: canonicals }), paths.indexDir);
    writeJson(paths.mergeHistory, {
        schema_version: 'canonical_merge_history.v1',
        items: [],
    });
    writeJson(paths.reviewProgress, {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-08-01',
        items: [
            progress('cq_target', { level: 3, review_count: 2 }),
            progress('cq_source', { level: 1, review_count: 4, mistake_count: 1 }),
        ],
    });
    writeJson(path.join(paths.reviewSessionsDir, '2026-08-01.json'), {
        events: [
            { event_id: 'e-target', canonical_id: 'cq_target', result: 'good' },
            { event_id: 'e-source', canonical_id: 'cq_source', result: 'hard' },
        ],
    });

    fs.mkdirSync(paths.answersDir, { recursive: true });
    fs.writeFileSync(
        path.join(paths.answersDir, 'cq_target.md'),
        answerContent('cq_target', {
            version: 4,
            status: 'ready',
            quality_tier: 'curated',
        }),
        'utf8',
    );
    fs.writeFileSync(
        path.join(paths.answersDir, 'cq_source.md'),
        answerContent('cq_source', { version: 2, status: 'draft' }),
        'utf8',
    );

    return { root, paths };
}

function formalPaths(paths) {
    const indexes = getIndexPaths(paths.indexDir);
    return [
        paths.canonicalQuestions,
        paths.questions,
        paths.reviewProgress,
        path.join(paths.reviewSessionsDir, '2026-08-01.json'),
        path.join(paths.answersDir, 'cq_target.md'),
        path.join(paths.answersDir, 'cq_source.md'),
        path.join(paths.answerArchiveDir, 'cq_source.md'),
        indexes.entity,
        indexes.company,
        indexes.domain,
        indexes.hotspot,
        paths.mergeHistory,
    ];
}

function snapshotFormalFiles(paths) {
    return Object.fromEntries(formalPaths(paths).map((filePath) => [
        path.relative(paths.root, filePath),
        fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : null,
    ]));
}

async function createFullMergePlan(root) {
    const canonicalRepositories = createFsCanonicalRepositories({ root });
    const reviewRepository = createFsReviewRepository({ root });
    const answerRepository = createFsAnswerRepository({ root });
    const [target, source, targetBindings, sourceBindings, review, answer] = await Promise.all([
        canonicalRepositories.canonicalRepository.get('cq_target'),
        canonicalRepositories.canonicalRepository.get('cq_source'),
        canonicalRepositories.questionBindingRepository.findByCanonical('cq_target'),
        canonicalRepositories.questionBindingRepository.findByCanonical('cq_source'),
        reviewRepository.loadMergeState('cq_target', 'cq_source'),
        answerRepository.loadMergeState('cq_target', 'cq_source'),
    ]);

    const merged = mergeCanonical(target.record, source.record);
    const reviewMigration = planCanonicalReviewMigration({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetItems: review.target_items,
        sourceItems: review.source_items,
        updatedAtFallback: '2026-08-12',
    });
    const answerMerge = planCanonicalAnswerMerge({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetAnswer: answer.target_answer,
        sourceAnswer: answer.source_answer,
        sourceArchiveExists: answer.source_archive_exists,
        updatedAt: '2026-08-12',
    });

    return createCanonicalMutationPlan({
        operation: 'merge',
        expected_revisions: [target, source, targetBindings, sourceBindings, review, answer]
            .map((snapshot) => ({ resource: snapshot.resource, revision: snapshot.revision })),
        changes: {
            canonical_upserts: [merged],
            canonical_removals: ['cq_source'],
            question_rebindings: [{
                question_id: 'q2',
                from_canonical_id: 'cq_source',
                to_canonical_id: 'cq_target',
            }],
            review_migrations: [reviewMigration],
            answer_invalidations: answerMerge.target_invalidation
                ? [answerMerge.target_invalidation]
                : [],
            answer_archives: answerMerge.source_archive ? [answerMerge.source_archive] : [],
            rebuild_indexes: true,
            history_entry: {
                schema_version: 'canonical_merge.v1',
                merged_at: '2026-08-12T06:36:00.000Z',
                target: 'cq_target',
                source: 'cq_source',
                reason: 'same knowledge point',
                moved_question_ids: ['q2'],
            },
        },
    });
}

function cleanup(root) {
    fs.rmSync(root, { recursive: true, force: true });
}

test('filesystem answer repository revision covers target, source, and source archive state', async () => {
    const fixture = createFixture();
    try {
        const repository = createFsAnswerRepository({ root: fixture.root });
        const before = await repository.loadMergeState('cq_target', 'cq_source');
        assert.equal(before.target_answer.metadata.status, 'ready');
        assert.equal(before.source_answer.metadata.status, 'draft');
        assert.equal(before.source_archive_exists, false);
        assert.match(before.resource, /^answer-merge:cq_target:cq_source$/);

        fs.writeFileSync(
            path.join(fixture.paths.answersDir, 'cq_source.md'),
            answerContent('cq_source', { version: 3, status: 'draft' }),
            'utf8',
        );
        const afterSourceEdit = await repository.loadMergeState('cq_target', 'cq_source');
        assert.notEqual(afterSourceEdit.revision, before.revision);

        fs.mkdirSync(fixture.paths.answerArchiveDir, { recursive: true });
        fs.writeFileSync(
            path.join(fixture.paths.answerArchiveDir, 'cq_source.md'),
            'external archive',
            'utf8',
        );
        const afterArchive = await repository.loadMergeState('cq_target', 'cq_source');
        assert.equal(afterArchive.source_archive_exists, true);
        assert.notEqual(afterArchive.revision, afterSourceEdit.revision);
    } finally {
        cleanup(fixture.root);
    }
});

test('filesystem mutation gateway commits answer invalidation and archive with canonical and review state', async () => {
    const fixture = createFixture();
    try {
        const plan = await createFullMergePlan(fixture.root);
        const gateway = createFileCanonicalMutationGatewayAdapter({ root: fixture.root });
        const token = await gateway.preflight(plan);
        const result = await gateway.commit(plan, token);

        assert.equal(result.committed, true);
        assert.equal(result.answer_invalidation_count, 1);
        assert.equal(result.answer_archive_count, 1);

        const target = readAnswerFile(path.join(fixture.paths.answersDir, 'cq_target.md'));
        assert.equal(target.metadata.status, 'needs_update');
        assert.equal(target.metadata.quality_tier, 'needs_update');
        assert.equal(target.metadata.version, 5);
        assert.equal(target.metadata.updated_at, '2026-08-12');
        assert.equal(target.metadata.invalidated_by_canonical_merge, 'cq_source');

        assert.equal(fs.existsSync(path.join(fixture.paths.answersDir, 'cq_source.md')), false);
        const archived = readAnswerFile(path.join(fixture.paths.answerArchiveDir, 'cq_source.md'));
        assert.equal(archived.metadata.canonical_id, 'cq_source');
        assert.equal(archived.metadata.version, 2);

        assert.deepEqual(readJsonl(fixture.paths.canonicalQuestions, []).map((item) => item.canonical_id), ['cq_target']);
        assert.equal(readJsonl(fixture.paths.questions, []).find((item) => item.question_id === 'q2').canonical_id, 'cq_target');
        assert.equal(readJson(fixture.paths.reviewProgress).items.length, 1);
        assert.equal(readJson(fixture.paths.mergeHistory).items.length, 1);
    } finally {
        cleanup(fixture.root);
    }
});

test('commit rejects stale answer revision before publishing canonical, review, or answer state', async () => {
    const fixture = createFixture();
    try {
        const plan = await createFullMergePlan(fixture.root);
        const gateway = createFileCanonicalMutationGatewayAdapter({ root: fixture.root });
        const token = await gateway.preflight(plan);
        const beforeCanonical = readJsonl(fixture.paths.canonicalQuestions, []);

        fs.writeFileSync(
            path.join(fixture.paths.answersDir, 'cq_target.md'),
            answerContent('cq_target', {
                version: 9,
                status: 'ready',
                quality_tier: 'curated',
                external_field: 'concurrent edit',
            }),
            'utf8',
        );

        await assert.rejects(
            gateway.commit(plan, token),
            /Revision mismatch for answer-merge:cq_target:cq_source/,
        );
        assert.deepEqual(readJsonl(fixture.paths.canonicalQuestions, []), beforeCanonical);
        assert.equal(readAnswerFile(path.join(fixture.paths.answersDir, 'cq_target.md')).metadata.version, 9);
        assert.equal(fs.existsSync(path.join(fixture.paths.answerArchiveDir, 'cq_source.md')), false);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});

for (const failure of [
    ['answer_invalidation:cq_target', 'injected answer metadata publish failure'],
    ['answer_archive_write:cq_source', 'injected answer archive publish failure'],
    ['answer_archive_delete_source:cq_source', 'injected source answer delete failure'],
]) {
    test(`${failure[0]} rolls canonical, review, answer, indexes, and history back together`, async () => {
        const fixture = createFixture();
        try {
            const before = snapshotFormalFiles(fixture.paths);
            const plan = await createFullMergePlan(fixture.root);
            const gateway = createFileCanonicalMutationGatewayAdapter({
                root: fixture.root,
                faultInjector(stage, context) {
                    if (stage === 'before_publish' && context.operation.kind === failure[0]) {
                        throw new Error(failure[1]);
                    }
                },
            });
            const token = await gateway.preflight(plan);

            await assert.rejects(gateway.commit(plan, token), new RegExp(failure[1]));
            assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
            assert.equal(fs.existsSync(fixture.paths.journal), false);
            assert.equal(fs.existsSync(fixture.paths.lock), false);
        } finally {
            cleanup(fixture.root);
        }
    });
}

test('filesystem answer effects require an opaque answer-merge revision', async () => {
    const fixture = createFixture();
    try {
        const fullPlan = await createFullMergePlan(fixture.root);
        const plan = createCanonicalMutationPlan({
            operation: fullPlan.operation,
            expected_revisions: fullPlan.expected_revisions.filter(
                (item) => !item.resource.startsWith('answer-merge:'),
            ),
            changes: fullPlan.changes,
        });
        const before = snapshotFormalFiles(fixture.paths);
        const gateway = createFileCanonicalMutationGatewayAdapter({ root: fixture.root });

        await assert.rejects(
            gateway.preflight(plan),
            /Filesystem answer mutation requires an opaque answer-merge revision/,
        );
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});
