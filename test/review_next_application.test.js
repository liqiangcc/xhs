'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createReviewNextUseCase } = require('../src/application/review/review-next');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: `title ${id}`,
        question_ids: [`q_${id}`],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 1,
        review_priority: 'P1',
        answer_status: 'missing',
        ...overrides,
    };
}

const strategy = {
    priority_weights: { P0: 100, P1: 70 },
    status_weights: { weak: 80, new: 30 },
    answer_status_weights: { ready: 20, missing: -10 },
    frequency_weight: 2,
    difficulty_weight: 5,
    mistake_weight: 12,
    due_bonus: 50,
    upcoming_day_penalty: 4,
};

function createUseCase(overrides = {}) {
    const writes = [];
    let issueLoads = 0;
    const dependencies = {
        canonicalCatalogRepository: {
            list() {
                return [
                    canonical('cq_due', { review_priority: 'P0' }),
                    canonical('cq_upcoming'),
                    canonical('cq_outside'),
                    canonical('cq_missing'),
                ];
            },
        },
        questionCatalogRepository: {
            list() {
                return [
                    { question_id: 'q_cq_upcoming', canonical_id: 'cq_upcoming', company: '美团', level: '社招' },
                ];
            },
        },
        progressReader: {
            load() {
                return {
                    schema_version: 'review_progress_store.v1',
                    updated_at: '2026-06-29',
                    items: [
                        {
                            canonical_id: 'cq_due', status: 'weak', level: 1,
                            review_count: 2, next_review_at: '2026-06-30',
                            confidence: 0.4, difficulty: 4, mistake_count: 1,
                        },
                        {
                            canonical_id: 'cq_upcoming', status: 'new', level: 0,
                            review_count: 0, next_review_at: '2026-07-03',
                            confidence: 0.5, difficulty: 3, mistake_count: 0,
                        },
                        {
                            canonical_id: 'cq_outside', status: 'new', level: 0,
                            review_count: 0, next_review_at: '2026-07-20',
                            confidence: 0.5, difficulty: 3, mistake_count: 0,
                        },
                    ],
                };
            },
        },
        progressWriter: {
            write(progress) {
                writes.push(structuredClone(progress));
                return progress;
            },
        },
        strategyReader: { read: () => structuredClone(strategy) },
        issueLinkReader: {
            load() {
                issueLoads++;
                return {
                    schema_version: 'review_issue_links.v1',
                    items: [{ canonical_id: 'cq_upcoming', issue_url: 'https://example.test/issues/3' }],
                };
            },
        },
        ...overrides,
    };
    return {
        next: createReviewNextUseCase(dependencies),
        writes,
        issueLoadCount: () => issueLoads,
    };
}

test('ReviewNext preserves horizon selection ranking initialization and issue semantics', () => {
    const fixture = createUseCase();

    const result = fixture.next({
        date: '2026-06-30',
        days: 7,
        limit: 10,
        with_issues: true,
        write_progress: true,
    });

    assert.equal(result.schema_version, 'review_next.v1');
    assert.equal(result.date, '2026-06-30');
    assert.equal(result.days, 7);
    assert.equal(result.returned_count, 3);
    assert.deepEqual(result.rows.map((row) => row.canonical_id), [
        'cq_due', 'cq_missing', 'cq_upcoming',
    ]);
    assert.equal(result.rows.some((row) => row.canonical_id === 'cq_outside'), false);
    assert.equal(result.rows.find((row) => row.canonical_id === 'cq_upcoming').issue_url, 'https://example.test/issues/3');
    assert.equal(result.rows.find((row) => row.canonical_id === 'cq_missing').progress.next_review_at, '2026-06-30');
    assert.equal(result.rows.find((row) => row.canonical_id === 'cq_upcoming').companies.includes('美团'), true);
    assert.equal(fixture.writes.length, 1);
    assert.equal(fixture.writes[0].items.some((item) => item.canonical_id === 'cq_missing'), true);
    assert.equal(fixture.issueLoadCount(), 1);
});

test('ReviewNext noWrite suppresses progress persistence but keeps synthesized progress', () => {
    const fixture = createUseCase({
        canonicalCatalogRepository: { list: () => [canonical('cq_missing')] },
        questionCatalogRepository: { list: () => [] },
        progressReader: {
            load: () => ({ schema_version: 'review_progress_store.v1', updated_at: null, items: [] }),
        },
    });

    const result = fixture.next({
        date: '2026-07-01',
        write_progress: false,
        with_issues: false,
    });

    assert.equal(result.days, 7);
    assert.equal(result.returned_count, 1);
    assert.equal(result.rows[0].progress.status, 'new');
    assert.equal(result.rows[0].progress.next_review_at, '2026-07-01');
    assert.equal('issue_url' in result.rows[0], false);
    assert.equal(fixture.writes.length, 0);
    assert.equal(fixture.issueLoadCount(), 0);
});

test('ReviewNext preserves legacy default limit of 20 and default horizon of 7 days', () => {
    const records = Array.from({ length: 21 }, (_, index) => canonical(`cq_${String(index).padStart(2, '0')}`));
    const fixture = createUseCase({
        canonicalCatalogRepository: { list: () => structuredClone(records) },
        questionCatalogRepository: { list: () => [] },
        progressReader: {
            load: () => ({ schema_version: 'review_progress_store.v1', updated_at: null, items: [] }),
        },
    });

    const result = fixture.next({ date: '2026-07-01', write_progress: false });

    assert.equal(result.days, 7);
    assert.equal(result.returned_count, 20);
    assert.equal(result.rows.length, 20);
});

test('ReviewNext requires the shared queue-state outbound capabilities and a date', () => {
    const fixture = createUseCase();
    assert.throws(() => fixture.next({}), /review date is required/);
    assert.throws(
        () => createReviewNextUseCase({}),
        /CanonicalCatalogRepository is required/,
    );
});
