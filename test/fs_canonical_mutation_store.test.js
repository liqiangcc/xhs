'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { mergeCanonical } = require('../src/domain/canonical/merge-policy');
const { createCanonicalMutationPlan } = require('../src/application/canonical/mutation-plan');
const { planCanonicalReviewMigration } = require('../src/application/canonical/review-migration-plan');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../src/infrastructure/filesystem/canonical-repositories');
const { createFsReviewRepository } = require('../src/infrastructure/filesystem/review-repositories');
const {
    SimulatedCanonicalMutationCrash,
    createFsCanonicalMutationStore,
} = require('../src/infrastructure/filesystem/fs-canonical-mutation-store');
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

function createFixture() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-fs-canonical-'));
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
        updated_at: '2026-08-05',
        items: [
            progress('cq_target', {
                level: 3,
                review_count: 2,
                last_reviewed_at: '2026-08-02',
                next_review_at: '2026-08-20',
                confidence: 0.8,
                difficulty: 2,
                updated_at: '2026-08-02',
            }),
            progress('cq_source', {
                level: 1,
                review_count: 4,
                last_reviewed_at: '2026-08-05',
                next_review_at: '2026-08-08',
                confidence: 0.4,
                difficulty: 5,
                mistake_count: 1,
                updated_at: '2026-08-05',
            }),
        ],
    });
    writeJson(path.join(paths.reviewSessionsDir, '2026-08-01.json'), {
        schema_version: 'review_session.v1',
        date: '2026-08-01',
        events: [
            { event_id: 'e-source', canonical_id: 'cq_source', result: 'hard' },
            { event_id: 'e-other', canonical_id: 'cq_other', result: 'good' },
        ],
    });
    writeJson(path.join(paths.reviewSessionsDir, '2026-08-02.json'), {
        schema_version: 'review_session.v1',
        date: '2026-08-02',
        events: [
            { event_id: 'e-target', canonical_id: 'cq_target', result: 'good' },
        ],
    });
    return { root, paths };
}

function formalPaths(paths) {
    const indexes = getIndexPaths(paths.indexDir);
    const sessions = fs.existsSync(paths.reviewSessionsDir)
        ? fs.readdirSync(paths.reviewSessionsDir)
            .filter((name) => name.endsWith('.json'))
            .sort()
            .map((name) => path.join(paths.reviewSessionsDir, name))
        : [];
    return [
        paths.canonicalQuestions,
        paths.questions,
        paths.reviewProgress,
        ...sessions,
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

async function loadCoreSnapshots(root) {
    const adapters = createFsCanonicalRepositories({ root });
    const target = await adapters.canonicalRepository.get('cq_target');
    const source = await adapters.canonicalRepository.get('cq_source');
    const targetBindings = await adapters.questionBindingRepository.findByCanonical('cq_target');
    const sourceBindings = await adapters.questionBindingRepository.findByCanonical('cq_source');
    return { target, source, targetBindings, sourceBindings };
}

function coreChanges(snapshots) {
    const merged = mergeCanonical(snapshots.target.record, snapshots.source.record);
    return {
        canonical_upserts: [merged],
        canonical_removals: ['cq_source'],
        question_rebindings: [{
            question_id: 'q2',
            from_canonical_id: 'cq_source',
            to_canonical_id: 'cq_target',
        }],
        rebuild_indexes: true,
        history_entry: {
            schema_version: 'canonical_merge.v1',
            merged_at: '2026-08-12T05:57:00.000Z',
            target: 'cq_target',
            source: 'cq_source',
            reason: 'same knowledge point',
            moved_question_ids: ['q2'],
        },
    };
}

async function createCoreMergePlan(root) {
    const snapshots = await loadCoreSnapshots(root);
    return createCanonicalMutationPlan({
        operation: 'merge',
        expected_revisions: [
            snapshots.target,
            snapshots.source,
            snapshots.targetBindings,
            snapshots.sourceBindings,
        ].map((snapshot) => ({
            resource: snapshot.resource,
            revision: snapshot.revision,
        })),
        changes: coreChanges(snapshots),
    });
}

async function createReviewAwareMergePlan(root) {
    const snapshots = await loadCoreSnapshots(root);
    const reviewRepository = createFsReviewRepository({ root });
    const review = await reviewRepository.loadMergeState('cq_target', 'cq_source');
    const reviewMigration = planCanonicalReviewMigration({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetItems: review.target_items,
        sourceItems: review.source_items,
        updatedAtFallback: '2026-08-12',
    });
    return createCanonicalMutationPlan({
        operation: 'merge',
        expected_revisions: [
            snapshots.target,
            snapshots.source,
            snapshots.targetBindings,
            snapshots.sourceBindings,
            review,
        ].map((snapshot) => ({
            resource: snapshot.resource,
            revision: snapshot.revision,
        })),
        changes: {
            ...coreChanges(snapshots),
            review_migrations: [reviewMigration],
        },
    });
}

function cleanup(root) {
    fs.rmSync(root, { recursive: true, force: true });
}

test('filesystem mutation store commits canonical, bindings, indexes, and history as one recoverable unit', async () => {
    const fixture = createFixture();
    try {
        const plan = await createCoreMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({ root: fixture.root });
        const token = await store.preflight(plan);
        const result = await store.commit(plan, token);

        assert.equal(result.committed, true);
        assert.equal(result.recoverable, true);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);

        const canonicals = readJsonl(fixture.paths.canonicalQuestions, []);
        assert.deepEqual(canonicals.map((record) => record.canonical_id), ['cq_target']);
        assert.deepEqual(canonicals[0].question_ids, ['q1', 'q2']);
        const questions = readJsonl(fixture.paths.questions, []);
        assert.equal(questions.find((row) => row.question_id === 'q2').canonical_id, 'cq_target');

        const hotspot = readJson(getIndexPaths(fixture.paths.indexDir).hotspot);
        assert.equal(hotspot.entries.length, 1);
        assert.equal(hotspot.entries[0].canonical_id, 'cq_target');
        assert.equal(hotspot.entries[0].frequency, 2);

        const history = readJson(fixture.paths.mergeHistory);
        assert.equal(history.items.length, 1);
        assert.equal(history.items[0].source, 'cq_source');
        assert.equal(history.items[0].target, 'cq_target');
    } finally {
        cleanup(fixture.root);
    }
});

test('filesystem review repository returns merge rows with a revision covering progress and sessions', async () => {
    const fixture = createFixture();
    try {
        const repository = createFsReviewRepository({ root: fixture.root });
        const before = await repository.loadMergeState('cq_target', 'cq_source');
        assert.equal(before.target_items.length, 1);
        assert.equal(before.source_items.length, 1);
        assert.match(before.resource, /^review-merge:cq_target:cq_source$/);

        const sessionPath = path.join(fixture.paths.reviewSessionsDir, '2026-08-02.json');
        const session = readJson(sessionPath);
        writeJson(sessionPath, { ...session, external_note: 'concurrent unrelated edit' });
        const after = await repository.loadMergeState('cq_target', 'cq_source');

        assert.deepEqual(after.target_items, before.target_items);
        assert.deepEqual(after.source_items, before.source_items);
        assert.notEqual(after.revision, before.revision);
    } finally {
        cleanup(fixture.root);
    }
});

test('filesystem mutation store materializes planned review progress and session migration in the same transaction', async () => {
    const fixture = createFixture();
    try {
        const plan = await createReviewAwareMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({ root: fixture.root });
        const token = await store.preflight(plan);
        const result = await store.commit(plan, token);

        assert.equal(result.committed, true);
        assert.equal(result.review_migration_count, 1);

        const review = readJson(fixture.paths.reviewProgress);
        assert.equal(review.updated_at, '2026-08-12');
        assert.equal(review.items.length, 1);
        assert.equal(review.items[0].canonical_id, 'cq_target');
        assert.equal(review.items[0].level, 1);
        assert.equal(review.items[0].review_count, 6);
        assert.equal(review.items[0].mistake_count, 1);
        assert.equal(review.items[0].confidence, 0.4);
        assert.equal(review.items[0].difficulty, 5);
        assert.equal(review.items[0].status, 'weak');

        const session = readJson(path.join(fixture.paths.reviewSessionsDir, '2026-08-01.json'));
        const migrated = session.events.find((event) => event.event_id === 'e-source');
        assert.equal(migrated.canonical_id, 'cq_target');
        assert.equal(migrated.migrated_from_canonical_id, 'cq_source');
        assert.equal(session.events.find((event) => event.event_id === 'e-other').canonical_id, 'cq_other');
    } finally {
        cleanup(fixture.root);
    }
});

test('commit rechecks opaque canonical revisions and refuses stale state before staging', async () => {
    const fixture = createFixture();
    try {
        const plan = await createCoreMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({ root: fixture.root });
        const token = await store.preflight(plan);

        const canonicals = readJsonl(fixture.paths.canonicalQuestions, []);
        canonicals[0] = { ...canonicals[0], canonical_title: 'externally changed title' };
        writeJsonl(fixture.paths.canonicalQuestions, canonicals);

        await assert.rejects(store.commit(plan, token), /Revision mismatch for canonical:cq_target/);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(readJsonl(fixture.paths.canonicalQuestions, []).some((record) => record.canonical_id === 'cq_source'), true);
        assert.equal(readJsonl(fixture.paths.questions, []).find((row) => row.question_id === 'q2').canonical_id, 'cq_source');
    } finally {
        cleanup(fixture.root);
    }
});

test('commit rejects a stale review revision without overwriting the concurrent review edit', async () => {
    const fixture = createFixture();
    try {
        const plan = await createReviewAwareMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({ root: fixture.root });
        const token = await store.preflight(plan);

        const sessionPath = path.join(fixture.paths.reviewSessionsDir, '2026-08-02.json');
        const session = readJson(sessionPath);
        writeJson(sessionPath, {
            ...session,
            events: [...session.events, { event_id: 'external', canonical_id: 'cq_other', result: 'easy' }],
        });

        await assert.rejects(store.commit(plan, token), /Revision mismatch for review-merge:cq_target:cq_source/);
        assert.equal(readJsonl(fixture.paths.canonicalQuestions, []).some((record) => record.canonical_id === 'cq_source'), true);
        assert.equal(readJsonl(fixture.paths.questions, []).find((row) => row.question_id === 'q2').canonical_id, 'cq_source');
        assert.equal(readJson(sessionPath).events.some((event) => event.event_id === 'external'), true);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('review progress publish failure rolls canonical, question, review, indexes, and history back together', async () => {
    const fixture = createFixture();
    try {
        const before = snapshotFormalFiles(fixture.paths);
        const plan = await createReviewAwareMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({
            root: fixture.root,
            faultInjector(stage, context) {
                if (stage === 'before_publish' && context.operation.kind === 'review_progress') {
                    throw new Error('injected review progress publish failure');
                }
            },
        });
        const token = await store.preflight(plan);

        await assert.rejects(store.commit(plan, token), /injected review progress publish failure/);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('review session publish failure rolls already-published progress and canonical state back together', async () => {
    const fixture = createFixture();
    try {
        const before = snapshotFormalFiles(fixture.paths);
        const plan = await createReviewAwareMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({
            root: fixture.root,
            faultInjector(stage, context) {
                if (stage === 'before_publish' && String(context.operation.kind).startsWith('review_session:')) {
                    throw new Error('injected review session publish failure');
                }
            },
        });
        const token = await store.preflight(plan);

        await assert.rejects(store.commit(plan, token), /injected review session publish failure/);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('index publish failure rolls every formal file back to its exact previous bytes', async () => {
    const fixture = createFixture();
    try {
        const before = snapshotFormalFiles(fixture.paths);
        const plan = await createCoreMergePlan(fixture.root);
        const store = createFsCanonicalMutationStore({
            root: fixture.root,
            faultInjector(stage, context) {
                if (stage === 'before_publish' && context.operation.kind === 'index:entity') {
                    throw new Error('injected index publish failure');
                }
            },
        });
        const token = await store.preflight(plan);

        await assert.rejects(store.commit(plan, token), /injected index publish failure/);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('a simulated process crash after partial publish is recovered automatically by the next preflight', async () => {
    const fixture = createFixture();
    try {
        const before = snapshotFormalFiles(fixture.paths);
        const plan = await createCoreMergePlan(fixture.root);
        const crashingStore = createFsCanonicalMutationStore({
            root: fixture.root,
            faultInjector(stage, context) {
                if (stage === 'after_publish' && context.index === 1) {
                    throw new SimulatedCanonicalMutationCrash('crash after questions publish');
                }
            },
        });
        const token = await crashingStore.preflight(plan);

        await assert.rejects(
            crashingStore.commit(plan, token),
            /crash after questions publish/,
        );
        assert.equal(fs.existsSync(fixture.paths.journal), true);
        assert.notDeepEqual(snapshotFormalFiles(fixture.paths), before);

        const recoveredStore = createFsCanonicalMutationStore({ root: fixture.root });
        await recoveredStore.preflight(plan);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('a crash after the committed journal marker preserves committed state during recovery', async () => {
    const fixture = createFixture();
    try {
        const before = snapshotFormalFiles(fixture.paths);
        const plan = await createCoreMergePlan(fixture.root);
        const crashingStore = createFsCanonicalMutationStore({
            root: fixture.root,
            faultInjector(stage) {
                if (stage === 'after_commit_mark') {
                    throw new SimulatedCanonicalMutationCrash('crash after commit marker');
                }
            },
        });
        const token = await crashingStore.preflight(plan);

        await assert.rejects(crashingStore.commit(plan, token), /crash after commit marker/);
        assert.equal(fs.existsSync(fixture.paths.journal), true);
        const committedBytes = snapshotFormalFiles(fixture.paths);
        assert.notDeepEqual(committedBytes, before);

        const recoveredStore = createFsCanonicalMutationStore({ root: fixture.root });
        const recovery = recoveredStore.recoverPendingTransaction();
        assert.deepEqual(recovery, { recovered: true, outcome: 'committed' });
        assert.deepEqual(snapshotFormalFiles(fixture.paths), committedBytes);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('filesystem store rejects review mutation without review concurrency coverage', async () => {
    const fixture = createFixture();
    try {
        const reviewPlan = await createReviewAwareMergePlan(fixture.root);
        const plan = createCanonicalMutationPlan({
            operation: reviewPlan.operation,
            expected_revisions: reviewPlan.expected_revisions
                .filter((item) => !item.resource.startsWith('review-merge:')),
            changes: reviewPlan.changes,
        });
        const before = snapshotFormalFiles(fixture.paths);
        const store = createFsCanonicalMutationStore({ root: fixture.root });

        await assert.rejects(store.preflight(plan), /requires an opaque review-merge revision/);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});

test('filesystem store still rejects answer effects instead of silently ignoring them', async () => {
    const fixture = createFixture();
    try {
        const corePlan = await createCoreMergePlan(fixture.root);
        const plan = createCanonicalMutationPlan({
            operation: corePlan.operation,
            expected_revisions: corePlan.expected_revisions,
            changes: {
                ...corePlan.changes,
                answer_invalidations: [{ canonical_id: 'cq_target' }],
            },
        });
        const before = snapshotFormalFiles(fixture.paths);
        const store = createFsCanonicalMutationStore({ root: fixture.root });

        await assert.rejects(store.preflight(plan), /does not yet materialize answer_invalidations/);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});
