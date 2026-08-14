'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createReviewWeakUseCase } = require('../src/application/review/review-weak');

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
    status_weights: { weak: 80, learning: 20, new: 30 },
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
                    canonical('cq_status', { review_priority: 'P0' }),
                    canonical('cq_mistake'),
                    canonical('cq_confidence'),
                    canonical('cq_healthy'),
                    canonical('cq_missing'),
                ];
            },
        },
        questionCatalogRepository: {
            list() {
                return [{
                    question_id: 'q_cq_confidence', canonical_id: 'cq_confidence',
                    company: '美团', level: '社招',
                }];
            },
        },
        progressRepository: {
            snapshot() {
                return {
                    revision: 'progress-rev-1',
                    progress: {
                        schema_version: 'review_progress_store.v1',
                        updated_at: '2026-06-29',
                        items: [
                            {
                                canonical_id: 'cq_status', status: 'weak', level: 1,
                                review_count: 2, next_review_at: '2026-07-10',
                                confidence: 0.8, difficulty: 3, mistake_count: 0,
                            },
                            {
                                canonical_id: 'cq_mistake', status: 'learning', level: 1,
                                review_count: 1, next_review_at: '2026-07-10',
                                confidence: 0.8, difficulty: 3, mistake_count: 1,
                            },
                            {
                                canonical_id: 'cq_confidence', status: 'learning', level: 1,
                                review_count: 2, next_review_at: '2026-07-10',
                                confidence: 0.4, difficulty: 3, mistake_count: 0,
                            },
                            {
                                canonical_id: 'cq_healthy', status: 'learning', level: 1,
                                review_count: 2, next_review_at: '2026-07-10',
                                confidence: 0.5, difficulty: 3, mistake_count: 0,
                            },
                        ],
                    },
                };
            },
            save(progress, input) {
                writes.push({ progress: structuredClone(progress), input: structuredClone(input) });
                return progress;
            },
        },
        strategyReader: { read: () => structuredClone(strategy) },
        issueLinkReader: {
            load() {
                issueLoads++;
                return {
                    schema_version: 'review_issue_links.v1',
                    items: [{ canonical_id: 'cq_confidence', issue_url: 'https://example.test/issues/4' }],
                };
            },
        },
        ...overrides,
    };
    return {
        weak: createReviewWeakUseCase(dependencies),
        writes,
        issueLoadCount: () => issueLoads,
    };
}

function progressRepositoryFor(progress) {
    return {
        snapshot: () => ({ revision: 'test-rev', progress: structuredClone(progress) }),
        save() { throw new Error('save must not be called'); },
    };
}

test('ReviewWeak preserves selector ranking initialization and issue semantics', () => {
    const fixture = createUseCase();
    const result = fixture.weak({ date: '2026-06-30', limit: 10, with_issues: true, write_progress: true });
    assert.equal(result.schema_version, 'review_weak.v1');
    assert.equal(result.returned_count, 3);
    assert.deepEqual(result.rows.map((row) => row.canonical_id).sort(), ['cq_confidence', 'cq_mistake', 'cq_status']);
    assert.equal(result.rows.some((row) => row.canonical_id === 'cq_healthy'), false);
    assert.equal(result.rows.some((row) => row.canonical_id === 'cq_missing'), false);
    assert.equal(result.rows.find((row) => row.canonical_id === 'cq_confidence').issue_url, 'https://example.test/issues/4');
    assert.equal(result.rows.find((row) => row.canonical_id === 'cq_confidence').companies.includes('美团'), true);
    assert.equal(fixture.writes.length, 1);
    assert.equal(fixture.writes[0].progress.items.some((item) => item.canonical_id === 'cq_missing'), true);
    assert.equal(fixture.writes[0].input.expected_revision, 'progress-rev-1');
    assert.equal(fixture.issueLoadCount(), 1);
});

test('ReviewWeak noWrite suppresses progress persistence and optional issue loading', () => {
    const fixture = createUseCase({
        canonicalCatalogRepository: { list: () => [canonical('cq_missing')] },
        questionCatalogRepository: { list: () => [] },
        progressRepository: progressRepositoryFor({ schema_version: 'review_progress_store.v1', updated_at: null, items: [] }),
    });
    const result = fixture.weak({ date: '2026-07-01', write_progress: false, with_issues: false });
    assert.equal(result.returned_count, 0);
    assert.equal(fixture.issueLoadCount(), 0);
});

test('ReviewWeak preserves legacy default limit of 20', () => {
    const records = Array.from({ length: 21 }, (_, index) => canonical(`cq_${String(index).padStart(2, '0')}`));
    const items = records.map((record) => ({
        canonical_id: record.canonical_id,
        status: 'weak', level: 1, review_count: 1,
        next_review_at: '2026-07-01', confidence: 0.5,
        difficulty: 3, mistake_count: 0,
    }));
    const fixture = createUseCase({
        canonicalCatalogRepository: { list: () => structuredClone(records) },
        questionCatalogRepository: { list: () => [] },
        progressRepository: progressRepositoryFor({
            schema_version: 'review_progress_store.v1', updated_at: '2026-07-01', items,
        }),
    });
    const result = fixture.weak({ date: '2026-07-01', write_progress: false });
    assert.equal(result.returned_count, 20);
    assert.equal(result.rows.length, 20);
});

test('ReviewWeak requires shared queue-state outbound capabilities and a date', () => {
    const fixture = createUseCase();
    assert.throws(() => fixture.weak({}), /review date is required/);
    assert.throws(() => createReviewWeakUseCase({}), /CanonicalCatalogRepository is required/);
});
