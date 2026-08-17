'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    addDays,
    defaultProgressItem,
    ensureProgressItems,
    isDue,
} = require('../src/domain/review/progress-policy');

test('Review progress policy preserves default initialization and due semantics', () => {
    const date = '2026-06-30';
    const existing = {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-06-29',
        items: [{
            canonical_id: 'cq_existing',
            status: 'learning',
            level: 2,
            next_review_at: '2026-07-02',
        }],
    };
    const before = structuredClone(existing);

    const result = ensureProgressItems(existing, [
        { canonical_id: 'cq_existing' },
        { canonical_id: 'cq_missing' },
    ], date);

    assert.deepEqual(existing, before);
    assert.equal(result.updated_at, date);
    assert.equal(result.items.length, 2);
    assert.deepEqual(result.items.find((item) => item.canonical_id === 'cq_missing'), {
        canonical_id: 'cq_missing',
        status: 'new',
        level: 0,
        review_count: 0,
        last_reviewed_at: null,
        next_review_at: date,
        confidence: 0.5,
        difficulty: 3,
        mistake_count: 0,
        updated_at: date,
    });
    assert.equal(isDue(result.items.find((item) => item.canonical_id === 'cq_missing'), date), true);
    assert.equal(isDue(result.items.find((item) => item.canonical_id === 'cq_existing'), date), false);
    assert.equal(isDue({ next_review_at: null }, date), true);
});

test('Review progress date helpers preserve the legacy UTC day arithmetic', () => {
    assert.equal(addDays('2026-06-30', 1), '2026-07-01');
    assert.equal(addDays('2026-12-31', 1), '2027-01-01');
    assert.equal(defaultProgressItem('cq_a', '2026-07-11').next_review_at, '2026-07-11');
});
