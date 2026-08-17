'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { mergeReviewProgress } = require('../src/domain/review/merge-progress-policy');
const { planCanonicalReviewMigration } = require('../src/application/canonical/review-migration-plan');
const { assertReviewRepository } = require('../src/ports/repositories/review-repository');

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

test('review merge policy preserves legacy conservative progress semantics', () => {
    const target = progress('cq_target', {
        level: 4,
        review_count: 5,
        last_reviewed_at: '2026-08-03',
        next_review_at: '2026-08-20',
        confidence: 0.8,
        difficulty: 2,
        mistake_count: 1,
        updated_at: '2026-08-03',
        migrated_from_canonical_ids: ['cq_old_target'],
        target_only_field: 'keep-me',
    });
    const source = progress('cq_source', {
        level: 1,
        review_count: 7,
        last_reviewed_at: '2026-08-05',
        next_review_at: '2026-08-08',
        confidence: 0.4,
        difficulty: 5,
        mistake_count: 2,
        updated_at: '2026-08-05',
        migrated_from_canonical_ids: ['cq_old_source'],
    });

    const merged = mergeReviewProgress(target, source, 'cq_target', {
        updatedAtFallback: '2026-08-12',
    });

    assert.equal(merged.canonical_id, 'cq_target');
    assert.equal(merged.target_only_field, 'keep-me');
    assert.equal(merged.status, 'weak');
    assert.equal(merged.level, 1);
    assert.equal(merged.review_count, 12);
    assert.equal(merged.last_reviewed_at, '2026-08-05');
    assert.equal(merged.next_review_at, '2026-08-08');
    assert.equal(merged.confidence, 0.4);
    assert.equal(merged.difficulty, 5);
    assert.equal(merged.mistake_count, 3);
    assert.equal(merged.updated_at, '2026-08-05');
    assert.deepEqual(merged.migrated_from_canonical_ids, [
        'cq_old_source',
        'cq_old_target',
        'cq_source',
    ]);
});

test('review merge policy derives mastered only when merged level is five and there are no mistakes', () => {
    const merged = mergeReviewProgress(
        progress('cq_target', { level: 5, mistake_count: 0 }),
        progress('cq_source', { level: 5, mistake_count: 0 }),
        'cq_target',
        { updatedAtFallback: '2026-08-12' },
    );
    assert.equal(merged.status, 'mastered');
    assert.equal(merged.level, 5);
});

test('source-only progress is moved to target without inventing a second review state', () => {
    const source = progress('cq_source', {
        migrated_from_canonical_ids: ['cq_older'],
        source_only_field: 'preserve',
    });
    const before = structuredClone(source);

    const merged = mergeReviewProgress(null, source, 'cq_target', {
        updatedAtFallback: '2026-08-12',
    });

    assert.equal(merged.canonical_id, 'cq_target');
    assert.equal(merged.source_only_field, 'preserve');
    assert.deepEqual(merged.migrated_from_canonical_ids, ['cq_older', 'cq_source']);
    assert.deepEqual(source, before);
});

test('review migration planner materializes progress merge and leaves session migration as semantic intent', () => {
    const target = progress('cq_target', { level: 3, review_count: 2 });
    const source = progress('cq_source', { level: 1, review_count: 4, mistake_count: 1 });

    const plan = planCanonicalReviewMigration({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetItems: [target],
        sourceItems: [source],
        updatedAtFallback: '2026-08-12',
    });

    assert.equal(plan.from_canonical_id, 'cq_source');
    assert.equal(plan.to_canonical_id, 'cq_target');
    assert.equal(plan.progress.source_found, true);
    assert.equal(plan.progress.target_found, true);
    assert.deepEqual(plan.progress.remove_canonical_ids, ['cq_target', 'cq_source']);
    assert.equal(plan.progress.upsert.canonical_id, 'cq_target');
    assert.equal(plan.progress.upsert.level, 1);
    assert.equal(plan.progress.upsert.review_count, 6);
    assert.equal(plan.progress.upsert.status, 'weak');
    assert.deepEqual(plan.session_events, {
        rebind_from_canonical_id: 'cq_source',
        rebind_to_canonical_id: 'cq_target',
        annotate_migrated_from: true,
    });
});

test('review migration planner keeps session rebinding when source has no progress row', () => {
    const plan = planCanonicalReviewMigration({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetItems: [progress('cq_target')],
        sourceItems: [],
    });

    assert.equal(plan.progress.source_found, false);
    assert.equal(plan.progress.target_found, true);
    assert.deepEqual(plan.progress.remove_canonical_ids, []);
    assert.equal(plan.progress.upsert, null);
    assert.equal(plan.session_events.rebind_from_canonical_id, 'cq_source');
    assert.equal(plan.session_events.rebind_to_canonical_id, 'cq_target');
});

test('review migration planner rejects duplicate progress rows before mutation', () => {
    assert.throws(
        () => planCanonicalReviewMigration({
            targetCanonicalId: 'cq_target',
            sourceCanonicalId: 'cq_source',
            targetItems: [progress('cq_target'), progress('cq_target')],
            sourceItems: [progress('cq_source')],
        }),
        /Cannot merge review progress with duplicate rows: cq_target=2, cq_source=1/,
    );
    assert.throws(
        () => planCanonicalReviewMigration({
            targetCanonicalId: 'cq_target',
            sourceCanonicalId: 'cq_source',
            targetItems: [],
            sourceItems: [progress('cq_source'), progress('cq_source')],
        }),
        /Cannot merge review progress with duplicate rows: cq_target=0, cq_source=2/,
    );
});

test('ReviewRepository contract stays narrow and merge-specific', () => {
    const repository = { loadMergeState() {} };
    assert.equal(assertReviewRepository(repository), repository);
    assert.throws(() => assertReviewRepository({}), /ReviewRepository\.loadMergeState\(\) is required/);
});
