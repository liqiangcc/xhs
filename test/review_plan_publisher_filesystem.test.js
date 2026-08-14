'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const {
    createFileReviewPlanPublisherAdapter,
} = require('../src/infrastructure/filesystem/review-plan-publisher-adapter');

function row(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: `title ${id}`,
        review_priority: 'P0',
        answer_status: 'missing',
        progress: { next_review_at: '2026-07-01' },
        ...overrides,
    };
}

test('FileReviewPlanPublisherAdapter preserves legacy safe path and issue Markdown format', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-plan-publisher-'));
    const publisher = createFileReviewPlanPublisherAdapter({ root });

    const planPath = publisher.publish({
        target: 'Redis / 社招 Plan!',
        date: '2026-06-30',
        with_issues: true,
        rows: [
            row('cq_redis', { issue_url: 'https://example.test/issues/12' }),
            row('cq_no_issue', { progress: { next_review_at: null }, issue_url: null }),
        ],
    });

    assert.equal(planPath, path.join('review', 'plans', 'redis_社招_plan.md'));
    const body = fs.readFileSync(path.join(root, planPath), 'utf8');
    assert.match(body, /^# Redis \/ 社招 Plan!/);
    assert.match(body, /Generated: 2026-06-30/);
    assert.match(body, /\| canonical_id \| priority \| answer \| due \| issue \| title \|/);
    assert.match(body, /\| cq_redis \| P0 \| missing \| 2026-07-01 \| https:\/\/example\.test\/issues\/12 \| title cq_redis \|/);
    assert.match(body, /\| cq_no_issue \| P0 \| missing \|  \|  \| title cq_no_issue \|/);

    fs.rmSync(root, { recursive: true, force: true });
});

test('FileReviewPlanPublisherAdapter omits issue column unless requested and requires root', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-plan-publisher-basic-'));
    const publisher = createFileReviewPlanPublisherAdapter({ root });

    const planPath = publisher.publish({
        target: 'redis',
        date: '2026-07-01',
        with_issues: false,
        rows: [row('cq_redis')],
    });

    const body = fs.readFileSync(path.join(root, planPath), 'utf8');
    assert.match(body, /\| canonical_id \| priority \| answer \| due \| title \|/);
    assert.doesNotMatch(body, /\| issue \|/);
    assert.throws(
        () => createFileReviewPlanPublisherAdapter({}),
        /File review plan publisher adapter root is required/,
    );

    fs.rmSync(root, { recursive: true, force: true });
});
