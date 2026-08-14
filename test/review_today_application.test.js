'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createReviewTodayUseCase } = require('../src/application/review/review-today');

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
                    canonical('cq_a', { review_priority: 'P0' }),
                    canonical('cq_b', { frequency: 2 }),
                    canonical('cq_future'),
                ];
            },
        },
        questionCatalogRepository: {
            list() {
                return [
                    { question_id: 'q_cq_a', canonical_id: 'cq_a', company: '美团', level: '社招' },
                    { question_id: 'q_cq_b', canonical_id: 'cq_b', company: '阿里', level: '校招' },
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
                            canonical_id: 'cq_a', status: 'weak', level: 1,
                            review_count: 2, next_review_at: '2026-06-30',
                            confidence: 0.4, difficulty: 4, mistake_count: 1,
                        },
                        {
                            canonical_id: 'cq_future', status: 'new', level: 0,
                            review_count: 0, next_review_at: '2026-07-05',
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
        strategyProvider: {
            load() {
                return structuredClone(strategy);
            },
        },
        issueLinkReader: {
            load() {
                issueLoads++;
                return {
                    schema_version: 'review_issue_links.v1',
                    items: [{ canonical_id: 'cq_b', issue_url: 'https://example.test/issues/2' }],
                };
            },
        },
        ...overrides,
    };
    return {
        today: createReviewTodayUseCase(dependencies),
        writes,
        issueLoadCount: () => issueLoads,
    };
}

test('ReviewToday preserves initialization persistence due ranking enrichment and issue semantics', () => {
    const fixture = createUseCase();

    const result = fixture.today({
        date: '2026-06-30',
        limit: 10,
        with_issues: true,
        write_progress: true,
    });

    assert.equal(result.schema_version, 'review_today.v1');
    assert.equal(result.date, '2026-06-30');
    assert.equal(result.total_due_count, 2);
    assert.equal(result.returned_count, 2);
    assert.deepEqual(result.rows.map((row) => row.canonical_id), ['cq_a', 'cq_b']);
    assert.equal(result.rows[0].issue_url, null);
    assert.equal(result.rows[1].issue_url, 'https://example.test/issues/2');
    assert.equal(result.rows[1].progress.status, 'new');
    assert.equal(result.rows[1].progress.next_review_at, '2026-06-30');
    assert.equal(result.rows[0].companies.includes('美团'), true);
    assert.equal(result.rows[0].levels.includes('社招'), true);
    assert.equal(typeof result.rows[0].review_score, 'number');

    assert.equal(fixture.writes.length, 1);
    assert.equal(fixture.writes[0].updated_at, '2026-06-30');
    assert.equal(fixture.writes[0].items.some((item) => item.canonical_id === 'cq_b'), true);
    assert.equal(fixture.issueLoadCount(), 1);
});

test('ReviewToday noWrite suppresses persistence but still returns synthesized progress', () => {
    const fixture = createUseCase({
        canonicalCatalogRepository: {
            list() {
                return [canonical('cq_missing')];
            },
        },
        questionCatalogRepository: { list: () => [] },
        progressReader: {
            load() {
                return { schema_version: 'review_progress_store.v1', updated_at: null, items: [] };
            },
        },
    });

    const result = fixture.today({
        date: '2026-07-01',
        write_progress: false,
        with_issues: false,
    });

    assert.equal(fixture.writes.length, 0);
    assert.equal(fixture.issueLoadCount(), 0);
    assert.equal(result.returned_count, 1);
    assert.equal(result.rows[0].progress.status, 'new');
    assert.equal(result.rows[0].progress.next_review_at, '2026-07-01');
    assert.equal('issue_url' in result.rows[0], false);
});

test('ReviewToday preserves the legacy default limit of 20', () => {
    const records = Array.from({ length: 21 }, (_, index) => canonical(`cq_${String(index).padStart(2, '0')}`));
    const fixture = createUseCase({
        canonicalCatalogRepository: { list: () => structuredClone(records) },
        questionCatalogRepository: { list: () => [] },
        progressReader: {
            load() {
                return { schema_version: 'review_progress_store.v1', updated_at: null, items: [] };
            },
        },
    });

    const result = fixture.today({ date: '2026-07-01', write_progress: false });

    assert.equal(result.total_due_count, 21);
    assert.equal(result.returned_count, 20);
    assert.equal(result.rows.length, 20);
});

test('ReviewToday requires a resolved review date and narrow outbound capabilities', () => {
    const fixture = createUseCase();
    assert.throws(() => fixture.today({}), /review date is required/);
    assert.throws(
        () => createReviewTodayUseCase({}),
        /CanonicalCatalogRepository\.list\(\) is required/,
    );
});
