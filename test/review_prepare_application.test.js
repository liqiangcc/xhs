'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createReviewPrepareUseCase } = require('../src/application/review/review-prepare');

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

function progress(id, overrides = {}) {
    return {
        canonical_id: id,
        status: 'new',
        level: 0,
        review_count: 0,
        last_reviewed_at: null,
        next_review_at: '2026-06-30',
        confidence: 0.5,
        difficulty: 3,
        mistake_count: 0,
        updated_at: '2026-06-30',
        ...overrides,
    };
}

const strategy = {
    priority_weights: { P0: 100, P1: 70 },
    status_weights: { weak: 80, new: 30, learning: 20 },
    answer_status_weights: { ready: 20, missing: -10 },
    frequency_weight: 2,
    difficulty_weight: 5,
    mistake_weight: 12,
    due_bonus: 50,
    upcoming_day_penalty: 4,
};

function createFixture(overrides = {}) {
    const writes = [];
    const plans = [];
    let issueLoads = 0;
    const dependencies = {
        canonicalCatalogRepository: {
            list() {
                return [
                    canonical('cq_match', {
                        canonical_title: 'Redis Cluster 原理',
                        primary_entities: ['Redis', 'Cluster'],
                        review_priority: 'P0',
                    }),
                    canonical('cq_wrong_company', {
                        canonical_title: 'Redis Cluster 复制',
                        review_priority: 'P0',
                        companies: ['百度'],
                    }),
                    canonical('cq_upcoming', {
                        canonical_title: 'Redis Cluster 扩容',
                        review_priority: 'P0',
                    }),
                ];
            },
        },
        questionCatalogRepository: {
            list() {
                return [{
                    question_id: 'q_cq_match',
                    canonical_id: 'cq_match',
                    company: '美团',
                    level: '社招',
                }];
            },
        },
        progressReader: {
            load() {
                return {
                    schema_version: 'review_progress_store.v1',
                    updated_at: '2026-06-30',
                    items: [
                        progress('cq_match', {
                            status: 'weak',
                            review_count: 2,
                            confidence: 0.4,
                            mistake_count: 1,
                        }),
                        progress('cq_wrong_company', {
                            status: 'weak',
                            review_count: 2,
                            confidence: 0.4,
                            mistake_count: 1,
                        }),
                        progress('cq_upcoming', {
                            status: 'weak',
                            next_review_at: '2026-07-03',
                            review_count: 1,
                            confidence: 0.4,
                        }),
                    ],
                };
            },
        },
        progressWriter: {
            write(value) {
                writes.push(structuredClone(value));
                return value;
            },
        },
        strategyReader: {
            read() {
                return structuredClone(strategy);
            },
        },
        issueLinkReader: {
            load() {
                issueLoads++;
                return {
                    schema_version: 'review_issue_links.v1',
                    items: [{
                        canonical_id: 'cq_match',
                        issue_url: 'https://example.test/issues/12',
                    }],
                };
            },
        },
        planPublisher: {
            publish(plan) {
                plans.push(structuredClone(plan));
                return 'review/plans/redis-social.md';
            },
        },
        ...overrides,
    };

    return {
        prepare: createReviewPrepareUseCase(dependencies),
        writes,
        plans,
        issueLoadCount: () => issueLoads,
        dependencies,
    };
}

test('ReviewPrepare preserves due selection filters ranking enrichment and plan publication', () => {
    const fixture = createFixture();

    const result = fixture.prepare({
        date: '2026-06-30',
        target: 'redis-social',
        limit: 10,
        priority: 'P0',
        status: 'weak',
        domain: '缓存',
        company: '美团',
        level: '社',
        topic: 'CLUSTER',
        with_issues: true,
        write_progress: true,
        write_plan: true,
    });

    assert.equal(result.schema_version, 'review_prepare_result.v1');
    assert.equal(result.ok, true);
    assert.equal(result.dry_run, false);
    assert.equal(result.plan_path, 'review/plans/redis-social.md');
    assert.equal(result.item_count, 1);
    assert.equal(result.rows[0].canonical_id, 'cq_match');
    assert.equal(typeof result.rows[0].review_score, 'number');
    assert.equal(result.rows[0].companies.includes('美团'), true);
    assert.equal(result.rows[0].levels.includes('社招'), true);
    assert.equal(result.rows[0].issue_url, 'https://example.test/issues/12');

    assert.equal(fixture.writes.length, 1);
    assert.equal(fixture.issueLoadCount(), 1);
    assert.equal(fixture.plans.length, 1);
    assert.equal(fixture.plans[0].target, 'redis-social');
    assert.equal(fixture.plans[0].date, '2026-06-30');
    assert.equal(fixture.plans[0].with_issues, true);
    assert.deepEqual(
        fixture.plans[0].rows.map((row) => row.canonical_id),
        ['cq_match'],
    );
});

test('ReviewPrepare days mode includes due upcoming and synthesized rows inside the horizon', () => {
    const fixture = createFixture({
        canonicalCatalogRepository: {
            list() {
                return [
                    canonical('cq_due'),
                    canonical('cq_upcoming'),
                    canonical('cq_outside'),
                    canonical('cq_missing'),
                ];
            },
        },
        questionCatalogRepository: { list: () => [] },
        progressReader: {
            load() {
                return {
                    schema_version: 'review_progress_store.v1',
                    updated_at: '2026-06-30',
                    items: [
                        progress('cq_due', { next_review_at: '2026-06-30' }),
                        progress('cq_upcoming', { next_review_at: '2026-07-03' }),
                        progress('cq_outside', { next_review_at: '2026-07-20' }),
                    ],
                };
            },
        },
    });

    const result = fixture.prepare({
        date: '2026-06-30',
        target: 'week',
        days: 7,
        limit: 10,
        with_issues: false,
        write_progress: false,
        write_plan: false,
    });

    assert.equal(result.dry_run, true);
    assert.equal(result.plan_path, null);
    assert.equal(result.item_count, 3);
    assert.deepEqual(
        new Set(result.rows.map((row) => row.canonical_id)),
        new Set(['cq_due', 'cq_upcoming', 'cq_missing']),
    );
    assert.equal(result.rows.some((row) => row.canonical_id === 'cq_outside'), false);
    assert.equal(result.rows.find((row) => row.canonical_id === 'cq_missing').progress.next_review_at, '2026-06-30');
    assert.equal(fixture.writes.length, 0);
    assert.equal(fixture.plans.length, 0);
    assert.equal(fixture.issueLoadCount(), 0);
});

test('ReviewPrepare preserves legacy default limit of 20', () => {
    const records = Array.from(
        { length: 21 },
        (_, index) => canonical(`cq_${String(index).padStart(2, '0')}`),
    );
    const fixture = createFixture({
        canonicalCatalogRepository: { list: () => structuredClone(records) },
        questionCatalogRepository: { list: () => [] },
        progressReader: {
            load: () => ({
                schema_version: 'review_progress_store.v1',
                updated_at: null,
                items: [],
            }),
        },
    });

    const result = fixture.prepare({
        date: '2026-07-01',
        target: 'default-limit',
        write_progress: false,
        write_plan: false,
    });

    assert.equal(result.item_count, 20);
    assert.equal(result.rows.length, 20);
});

test('ReviewPrepare requires shared queue capabilities target and ReviewPlanPublisher', () => {
    const fixture = createFixture();
    assert.throws(
        () => fixture.prepare({
            date: '2026-06-30',
            write_progress: false,
            write_plan: false,
        }),
        /Usage: review prepare --target <name>/,
    );
    assert.throws(
        () => createReviewPrepareUseCase({}),
        /CanonicalCatalogRepository is required/,
    );

    const withoutPlanPublisher = { ...fixture.dependencies, planPublisher: null };
    assert.throws(
        () => createReviewPrepareUseCase(withoutPlanPublisher),
        /ReviewPlanPublisher is required/,
    );
});
