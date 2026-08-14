'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('Review queue state uses the approved Coordinator role rather than Loader', () => {
    const coordinatorPath = 'src/application/review/review-queue-state-coordinator.js';
    const legacyPath = path.join(ROOT, 'src/application/review/review-queue-state.js');
    const coordinator = read(coordinatorPath);

    assert.equal(fs.existsSync(legacyPath), false);
    assert.match(coordinator, /function createReviewQueueStateCoordinator/);
    assert.match(coordinator, /return function buildReviewQueueState/);
    assert.doesNotMatch(coordinator, /createReviewQueueStateLoader|loadReviewQueueState/);

    for (const relativePath of [
        'src/application/review/review-today.js',
        'src/application/review/review-next.js',
        'src/application/review/review-weak.js',
        'src/application/review/review-prepare.js',
    ]) {
        const source = read(relativePath);
        assert.match(source, /createReviewQueueStateCoordinator/);
        assert.match(source, /buildReviewQueueState/);
        assert.doesNotMatch(source, /createReviewQueueStateLoader|loadReviewQueueState/);
    }
});

test('Review naming audit records completed outbound and coordinator naming decisions', () => {
    const audit = read('docs/refactor/14_naming_convention_audit.md');

    assert.match(audit, /ReviewPlanPublisher[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewStrategyReader[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewQueueStateCoordinator[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewProgressWriter[\s\S]*review mark/i);
});
