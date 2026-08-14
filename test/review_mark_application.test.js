'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createReviewMarkUseCase } = require('../src/application/review/review-mark');

function canonical(id = 'cq_redis') {
    return {
        canonical_id: id,
        canonical_title: 'Redis 为什么快？',
        question_ids: ['q1'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: 'missing',
    };
}

function createFixture(overrides = {}) {
    const commits = [];
    let snapshots = 0;
    const dependencies = {
        canonicalCatalogRepository: { list: () => [canonical()] },
        mutationGateway: {
            snapshot() {
                snapshots++;
                return {
                    revision: 'mutation-rev-1',
                    progress: {
                        schema_version: 'review_progress_store.v1',
                        updated_at: '2026-06-30',
                        items: [],
                    },
                };
            },
            commit(mutation) {
                commits.push(structuredClone(mutation));
                return { committed: true, session_path: 'review/sessions/2026-07-01.json' };
            },
        },
        ...overrides,
    };
    return {
        mark: createReviewMarkUseCase(dependencies),
        commits,
        snapshotCount: () => snapshots,
    };
}

test('ReviewMark initializes progress applies Domain transition and commits one semantic mutation', () => {
    const fixture = createFixture();
    const result = fixture.mark({
        date: '2026-07-01',
        canonical_id: 'cq_redis',
        result: 'good',
        oral_version: 'one_minute',
        followup_answered: true,
        quality_defects: ['too_long', 'too_long'],
        hard_failures: ['hf_a', 'hf_a'],
        feedback_closed_at: '2026-07-01',
        notes: 'reviewed',
        write_mutation: true,
    });

    assert.equal(result.schema_version, 'review_mark_result.v1');
    assert.equal(result.ok, true);
    assert.equal(result.dry_run, false);
    assert.equal(result.canonical_id, 'cq_redis');
    assert.equal(result.result, 'good');
    assert.equal(result.progress.level, 1);
    assert.equal(result.progress.next_review_at, '2026-07-02');
    assert.equal(result.session_path, 'review/sessions/2026-07-01.json');
    assert.deepEqual(result.session_event.quality_defects, ['too_long']);
    assert.deepEqual(result.session_event.hard_failures, ['hf_a']);
    assert.equal(result.session_event.followup_answered, true);

    assert.equal(fixture.commits.length, 1);
    assert.equal(fixture.commits[0].schema_version, 'review_mutation.v1');
    assert.equal(fixture.commits[0].expected_revision, 'mutation-rev-1');
    assert.equal(fixture.commits[0].progress.items.length, 1);
    assert.equal(fixture.commits[0].session_event.reviewed_at, '2026-07-01');
});

test('ReviewMark noWrite returns proposed progress and event without commit', () => {
    const fixture = createFixture();
    const result = fixture.mark({
        date: '2026-07-01', canonical_id: 'cq_redis', result: 'again', write_mutation: false,
    });
    assert.equal(result.dry_run, true);
    assert.equal(result.session_path, null);
    assert.equal(result.progress.status, 'weak');
    assert.equal(fixture.commits.length, 0);
    assert.equal(fixture.snapshotCount(), 1);
});

test('ReviewMark preserves usage canonical and mark metadata validation semantics', () => {
    const fixture = createFixture();
    assert.throws(() => fixture.mark({ date: '2026-07-01' }), /Usage: review mark/);
    assert.throws(
        () => fixture.mark({ date: '2026-07-01', canonical_id: 'missing', result: 'good' }),
        /Canonical not found: missing/,
    );
    assert.throws(
        () => fixture.mark({ date: '2026-07-01', canonical_id: 'cq_redis', result: 'good', oral_version: 'full' }),
        /oral-version must be one_minute/,
    );
    assert.throws(
        () => fixture.mark({ date: '2026-07-01', canonical_id: 'cq_redis', result: 'good', feedback_closed_at: '07-01-2026' }),
        /feedback-closed-at must use YYYY-MM-DD/,
    );
    assert.throws(
        () => fixture.mark({ date: '2026-07-01', canonical_id: 'cq_redis', result: 'good', feedback_closed_at: '2026-07-01' }),
        /feedback-closed-at requires at least one quality-defect/,
    );
});

test('ReviewMark requires only Canonical catalog and ReviewMutationGateway outbound capabilities', () => {
    assert.throws(() => createReviewMarkUseCase({}), /CanonicalCatalogRepository is required/);
    assert.throws(
        () => createReviewMarkUseCase({ canonicalCatalogRepository: { list: () => [] } }),
        /ReviewMutationGateway is required/,
    );
});
