'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    scoreReviewRow,
    rankReviewRows,
} = require('../src/domain/review/ranking-policy');

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

function row(canonicalId, overrides = {}) {
    return {
        canonical_id: canonicalId,
        review_priority: 'P1',
        answer_status: 'missing',
        frequency: 1,
        progress: {
            status: 'new',
            next_review_at: '2026-06-30',
            difficulty: 3,
            mistake_count: 0,
        },
        ...overrides,
    };
}

test('Review ranking policy preserves weighted score semantics', () => {
    const value = scoreReviewRow(row('cq_a'), {
        strategy,
        date: '2026-06-30',
    });

    assert.equal(value, 70 + 30 - 10 + 2 + 15 + 0 + 50);
});

test('Review ranking policy preserves score due frequency and id tie breaks without mutation', () => {
    const rows = [
        row('cq_b', { frequency: 3 }),
        row('cq_a', { frequency: 3 }),
        row('cq_high', {
            review_priority: 'P0',
            frequency: 1,
        }),
        row('cq_future', {
            progress: {
                status: 'new',
                next_review_at: '2026-07-02',
                difficulty: 3,
                mistake_count: 0,
            },
        }),
    ];
    const before = structuredClone(rows);

    const ranked = rankReviewRows(rows, {
        strategy,
        date: '2026-06-30',
    });

    assert.deepEqual(rows, before);
    assert.deepEqual(
        ranked.map((item) => item.canonical_id),
        ['cq_high', 'cq_a', 'cq_b', 'cq_future'],
    );
    assert.equal(ranked.every((item) => typeof item.review_score === 'number'), true);
});
