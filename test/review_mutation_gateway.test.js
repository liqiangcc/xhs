'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { readJson, writeJson } = require('../scripts/lib/io');
const {
    SimulatedReviewMutationCrash,
    createFileReviewMutationGatewayAdapter,
} = require('../src/infrastructure/filesystem/review-mutation-gateway-adapter');
const {
    createFileReviewProgressRepositoryAdapter,
} = require('../src/infrastructure/filesystem/review-progress-repository-adapter');

function progressStore(status = 'new') {
    return {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-07-01',
        items: [{
            canonical_id: 'cq_redis', status, level: 0, review_count: 0,
            last_reviewed_at: null, next_review_at: '2026-07-01',
            confidence: 0.5, difficulty: 3, mistake_count: 0,
            updated_at: '2026-07-01',
        }],
    };
}

function mutation(snapshot, status = 'learning') {
    return {
        schema_version: 'review_mutation.v1',
        expected_revision: snapshot.revision,
        date: '2026-07-01',
        progress: progressStore(status),
        session_event: {
            canonical_id: 'cq_redis', result: 'good', notes: '',
            reviewed_at: '2026-07-01', next_review_at: '2026-07-02',
            oral_version: null, followup_answered: false,
            quality_defects: [], hard_failures: [], feedback_closed_at: null,
        },
    };
}

test('FileReviewMutationGatewayAdapter commits progress and session as one recoverable mutation', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-gateway-'));
    const gateway = createFileReviewMutationGatewayAdapter({ root });
    const snapshot = gateway.snapshot({ date: '2026-07-01' });
    const result = gateway.commit(mutation(snapshot));

    assert.equal(result.committed, true);
    assert.equal(result.recoverable, true);
    assert.equal(result.file_operation_count, 2);
    assert.equal(result.session_path, path.join('review', 'sessions', '2026-07-01.json'));
    assert.equal(readJson(path.join(root, 'review', 'progress.json')).items[0].status, 'learning');
    const session = readJson(path.join(root, 'review', 'sessions', '2026-07-01.json'));
    assert.equal(session.events.length, 1);
    assert.equal(session.events[0].result, 'good');
    assert.equal(fs.existsSync(path.join(root, '.xhs', 'review-mutations', 'active.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('normal publish failure rolls progress and session back together', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-gateway-rollback-'));
    writeJson(path.join(root, 'review', 'progress.json'), progressStore('new'));
    const gateway = createFileReviewMutationGatewayAdapter({
        root,
        faultInjector(stage, context) {
            if (stage === 'after_publish' && context.operation.kind === 'review_progress') {
                throw new Error('injected session publish failure');
            }
        },
    });
    const snapshot = gateway.snapshot({ date: '2026-07-01' });
    assert.throws(() => gateway.commit(mutation(snapshot)), /injected session publish failure/);
    assert.equal(readJson(path.join(root, 'review', 'progress.json')).items[0].status, 'new');
    assert.equal(fs.existsSync(path.join(root, 'review', 'sessions', '2026-07-01.json')), false);
    assert.equal(fs.existsSync(path.join(root, '.xhs', 'review-mutations', 'active.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('simulated crash after partial publish is recovered by the next snapshot', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-gateway-crash-'));
    writeJson(path.join(root, 'review', 'progress.json'), progressStore('new'));
    const crashing = createFileReviewMutationGatewayAdapter({
        root,
        faultInjector(stage, context) {
            if (stage === 'after_publish' && context.operation.kind === 'review_progress') {
                throw new SimulatedReviewMutationCrash();
            }
        },
    });
    const snapshot = crashing.snapshot({ date: '2026-07-01' });
    assert.throws(() => crashing.commit(mutation(snapshot)), SimulatedReviewMutationCrash);
    assert.equal(readJson(path.join(root, 'review', 'progress.json')).items[0].status, 'learning');
    assert.equal(fs.existsSync(path.join(root, '.xhs', 'review-mutations', 'active.json')), true);

    const recovering = createFileReviewMutationGatewayAdapter({ root });
    recovering.snapshot({ date: '2026-07-01' });
    assert.equal(readJson(path.join(root, 'review', 'progress.json')).items[0].status, 'new');
    assert.equal(fs.existsSync(path.join(root, 'review', 'sessions', '2026-07-01.json')), false);
    assert.equal(fs.existsSync(path.join(root, '.xhs', 'review-mutations', 'active.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('Review mutation and progress repository reject stale snapshots instead of overwriting newer state', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-gateway-cas-'));
    const gateway = createFileReviewMutationGatewayAdapter({ root });
    const repository = createFileReviewProgressRepositoryAdapter({ root });
    const markSnapshot = gateway.snapshot({ date: '2026-07-01' });
    const queueSnapshot = repository.snapshot({ date: '2026-07-01' });

    repository.save(progressStore('new'), {
        date: '2026-07-01', expected_revision: queueSnapshot.revision,
    });
    assert.throws(() => gateway.commit(mutation(markSnapshot)), /Review revision mismatch/);

    const staleQueue = repository.snapshot({ date: '2026-07-01' });
    const freshGateway = gateway.snapshot({ date: '2026-07-01' });
    gateway.commit(mutation(freshGateway, 'learning'));
    assert.throws(
        () => repository.save(progressStore('weak'), {
            date: '2026-07-01', expected_revision: staleQueue.revision,
        }),
        /Review revision mismatch/,
    );
    assert.equal(readJson(path.join(root, 'review', 'progress.json')).items[0].status, 'learning');
    fs.rmSync(root, { recursive: true, force: true });
});
