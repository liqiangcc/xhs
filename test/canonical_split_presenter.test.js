'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { presentCanonicalSplitResult } = require('../src/interfaces/cli/canonical-split-presenter');

test('split presenter preserves legacy cli json and hides application diagnostics', () => {
    const presented = presentCanonicalSplitResult({
        ok: false,
        source: 'cq_source',
        new_canonical_id: 'cq_new',
        question_id: 'q1',
        canonical_count: 2,
        integrity: { schema_version: 'canonical_quality_report.v1', ok: false },
        plan: { operation: 'split' },
        commit: { committed: true, recoverable: true },
    });

    assert.deepEqual(presented, {
        ok: false,
        source: 'cq_source',
        new_canonical_id: 'cq_new',
        question_id: 'q1',
        canonical_count: 2,
    });
    assert.equal('integrity' in presented, false);
    assert.equal('plan' in presented, false);
    assert.equal('commit' in presented, false);
});

test('split presenter rejects missing application results', () => {
    assert.throws(() => presentCanonicalSplitResult(null), /application result is required/);
});
