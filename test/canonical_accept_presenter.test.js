'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { presentCanonicalAcceptResult } = require('../src/interfaces/cli/canonical-accept-presenter');

test('canonical accept presenter preserves legacy CLI JSON and hides application diagnostics', () => {
    const result = presentCanonicalAcceptResult({
        ok: true,
        canonical_id: 'cq_redis_fast',
        accepted_candidate_id: 'cand_redis_fast',
        question_ids: ['q1', 'q2'],
        updated_question_rows: 3,
        canonical_count: 5,
        plan: { operation: 'accept' },
        commit: { committed: true, recoverable: true },
    });

    assert.deepEqual(result, {
        ok: true,
        canonical_id: 'cq_redis_fast',
        accepted_candidate_id: 'cand_redis_fast',
        question_ids: ['q1', 'q2'],
        updated_question_rows: 3,
        canonical_count: 5,
    });
    assert.equal('plan' in result, false);
    assert.equal('commit' in result, false);
});

test('canonical accept presenter requires an application result object', () => {
    assert.throws(() => presentCanonicalAcceptResult(), /application result is required/);
});
