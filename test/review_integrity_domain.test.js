'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { evaluateReviewIntegrity } = require('../src/domain/review/integrity-policy');

function canonical(canonicalId) {
    return { canonical_id: canonicalId };
}

test('Review integrity policy preserves duplicate stale malformed missing and session semantics', () => {
    const result = evaluateReviewIntegrity({
        canonical_records: [canonical('cq_a'), canonical('cq_b')],
        progress: {
            items: [
                { canonical_id: 'cq_a' },
                { canonical_id: 'cq_a' },
                { canonical_id: 'cq_removed' },
                {},
            ],
        },
        session_sources: [
            {
                source: 'review/sessions/2026-06-30.json',
                session: {
                    events: [
                        { canonical_id: 'cq_a' },
                        { canonical_id: 'cq_removed' },
                        {},
                    ],
                },
            },
            {
                source: 'review/sessions/invalid.json',
                parse_error: 'invalid_json',
            },
        ],
    });

    assert.equal(result.ok, false);
    assert.equal(result.canonical_count, 2);
    assert.equal(result.progress_item_count, 4);
    assert.equal(result.initialized_progress_count, 2);
    assert.equal(result.missing_progress_count, 1);
    assert.deepEqual(result.missing_progress_sample, ['cq_b']);
    assert.deepEqual(result.duplicate_progress_canonical_ids, [{ canonical_id: 'cq_a', count: 2 }]);
    assert.deepEqual(result.stale_progress_canonical_ids, ['cq_removed']);
    assert.deepEqual(result.malformed_progress_items, [{ index: 3, canonical_id: null }]);
    assert.deepEqual(result.stale_session_events, [
        {
            source: 'review/sessions/2026-06-30.json',
            index: 1,
            canonical_id: 'cq_removed',
            reason: 'unknown_canonical_id',
        },
        {
            source: 'review/sessions/2026-06-30.json',
            index: 2,
            canonical_id: null,
            reason: 'missing_canonical_id',
        },
        {
            source: 'review/sessions/invalid.json',
            index: null,
            canonical_id: null,
            reason: 'invalid_json',
        },
    ]);
    assert.equal(result.hard_failure_count, 6);
});

test('missing ReviewProgress alone is reported but is not a hard failure', () => {
    const result = evaluateReviewIntegrity({
        canonical_records: [canonical('cq_a'), canonical('cq_b')],
        progress: { items: [{ canonical_id: 'cq_a' }] },
        session_sources: [],
    });

    assert.equal(result.ok, true);
    assert.equal(result.missing_progress_count, 1);
    assert.deepEqual(result.missing_progress_sample, ['cq_b']);
    assert.equal(result.hard_failure_count, 0);
});
