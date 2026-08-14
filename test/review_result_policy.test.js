'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { applyReviewResult } = require('../src/domain/review/review-result-policy');

function item(overrides = {}) {
    return {
        canonical_id: 'cq_review',
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

test('Review result policy preserves again hard good and easy transitions', () => {
    const again = applyReviewResult(item({ level: 1 }), 'again', '2026-07-01');
    assert.equal(again.level, 0);
    assert.equal(again.status, 'weak');
    assert.equal(again.next_review_at, '2026-07-01');
    assert.equal(again.confidence, 0.3);
    assert.equal(again.difficulty, 4);
    assert.equal(again.mistake_count, 1);

    const hard = applyReviewResult(item(), 'hard', '2026-07-01');
    assert.equal(hard.level, 0);
    assert.equal(hard.status, 'weak');
    assert.equal(hard.next_review_at, '2026-07-02');

    const good = applyReviewResult(item(), 'good', '2026-07-01');
    assert.equal(good.level, 1);
    assert.equal(good.status, 'learning');
    assert.equal(good.next_review_at, '2026-07-02');

    const easy = applyReviewResult(item({ level: 3, mistake_count: 1 }), 'easy', '2026-07-01');
    assert.equal(easy.level, 5);
    assert.equal(easy.status, 'mastered');
    assert.equal(easy.next_review_at, '2026-07-31');
    assert.equal(easy.mistake_count, 0);
});

test('Review result policy clamps confidence difficulty and level exactly as legacy behavior', () => {
    const again = applyReviewResult(item({ level: 0, confidence: 0.1, difficulty: 5 }), 'again', '2026-07-01');
    assert.equal(again.level, 0);
    assert.equal(again.confidence, 0);
    assert.equal(again.difficulty, 5);

    const easy = applyReviewResult(item({ level: 5, confidence: 0.9, difficulty: 1 }), 'easy', '2026-07-01');
    assert.equal(easy.level, 5);
    assert.equal(easy.confidence, 1);
    assert.equal(easy.difficulty, 1);
});

test('Review result policy rejects invalid inputs and does not mutate caller state', () => {
    const current = item();
    const before = structuredClone(current);
    assert.throws(() => applyReviewResult(current, 'unknown', '2026-07-01'), /Invalid review result/);
    assert.throws(() => applyReviewResult(null, 'good', '2026-07-01'), /progress item is required/i);
    assert.throws(() => applyReviewResult(current, 'good'), /result date is required/i);
    assert.deepEqual(current, before);
});
