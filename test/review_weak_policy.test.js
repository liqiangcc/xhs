'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { isWeakReviewProgress } = require('../src/domain/review/weak-policy');

test('weak Review policy preserves legacy selector semantics', () => {
    assert.equal(isWeakReviewProgress({
        status: 'weak', mistake_count: 0, review_count: 0, confidence: 1,
    }), true);
    assert.equal(isWeakReviewProgress({
        status: 'learning', mistake_count: 1, review_count: 0, confidence: 1,
    }), true);
    assert.equal(isWeakReviewProgress({
        status: 'learning', mistake_count: 0, review_count: 2, confidence: 0.49,
    }), true);
    assert.equal(isWeakReviewProgress({
        status: 'learning', mistake_count: 0, review_count: 2, confidence: 0.5,
    }), false);
    assert.equal(isWeakReviewProgress({
        status: 'new', mistake_count: 0, review_count: 0, confidence: 0,
    }), false);
    assert.equal(isWeakReviewProgress(null), false);
});
