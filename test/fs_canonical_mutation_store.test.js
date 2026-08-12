'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { mergeCanonical } = require('../src/domain/canonical/merge-policy');
const { createCanonicalMutationPlan } = require('../src/application/canonical/mutation-plan');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../src/infrastructure/filesystem/canonical-repositories');
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
    return { root, paths };
}

function formalPaths(paths) {
    const indexes = getIndexPaths(paths.indexDir);
    return [
        paths.canonicalQuestions,
        paths.questions,
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

async function createCoreMergePlan(root) {
    const adapters = createFsCanonicalRepositories({ root });
    const target = await adapters.canonicalRepository.get('cq_target');
    const source = await adapters.canonicalRepository.get('cq_source');
    const targetBindings = await adapters.questionBindingRepository.findByCanonical('cq_target');
    const sourceBindings = await adapters.questionBindingRepository.findByCanonical('cq_source');
    const merged = mergeCanonical(target.record, source.record);
    return createCanonicalMutationPlan({
        operation: 'merge',
        expected_revisions: [target, source, targetBindings, sourceBindings].map((snapshot) => ({
            resource: snapshot.resource,
            revision: snapshot.revision,
        })),
        changes: {
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

test('commit rechecks opaque revisions and refuses stale state before staging', async () => {
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

test('filesystem core slice rejects review and answer effects instead of silently ignoring them', async () => {
    const fixture = createFixture();
    try {
        const corePlan = await createCoreMergePlan(fixture.root);
        const plan = createCanonicalMutationPlan({
            operation: corePlan.operation,
            expected_revisions: corePlan.expected_revisions,
            changes: {
                ...corePlan.changes,
                review_migrations: [{ from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' }],
                answer_invalidations: [{ canonical_id: 'cq_target' }],
            },
        });
        const before = snapshotFormalFiles(fixture.paths);
        const store = createFsCanonicalMutationStore({ root: fixture.root });

        await assert.rejects(store.preflight(plan), /does not yet materialize review_migrations/);
        assert.deepEqual(snapshotFormalFiles(fixture.paths), before);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
    } finally {
        cleanup(fixture.root);
    }
});
