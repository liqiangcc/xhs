'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    PRIORITY_RANK,
    priorityRank,
    pickPriority,
    computePriority,
} = require('../src/domain/canonical/priority-policy');

test('canonical priority ranks supported levels in review order', () => {
    assert.deepEqual(PRIORITY_RANK, { P0: 0, P1: 1, P2: 2, P3: 3 });
    assert.equal(priorityRank('P0'), 0);
    assert.equal(priorityRank('P1'), 1);
    assert.equal(priorityRank('P2'), 2);
    assert.equal(priorityRank('P3'), 3);
    assert.equal(priorityRank('UNKNOWN'), 9);
    assert.equal(priorityRank(undefined), 9);
});

test('pickPriority keeps the highest priority and preserves legacy fallback', () => {
    assert.equal(pickPriority('P2', 'P0', 'P1'), 'P0');
    assert.equal(pickPriority('P3', 'P2'), 'P2');
    assert.equal(pickPriority(undefined, null, 'P1'), 'P1');
    assert.equal(pickPriority(), 'P2');
});

test('computePriority returns P0 for high frequency or broad company coverage', () => {
    assert.equal(computePriority(5, 1), 'P0');
    assert.equal(computePriority(1, 4), 'P0');
    assert.equal(computePriority(5, 4), 'P0');
});

test('computePriority returns P1 for medium frequency below P0 thresholds', () => {
    assert.equal(computePriority(3, 1), 'P1');
    assert.equal(computePriority(4, 3), 'P1');
});

test('computePriority returns P2 below review escalation thresholds', () => {
    assert.equal(computePriority(0, 0), 'P2');
    assert.equal(computePriority(1, 1), 'P2');
    assert.equal(computePriority(2, 3), 'P2');
});

test('priority policy is deterministic and does not mutate caller input', () => {
    const priorities = ['P2', 'P1', 'P3'];
    const snapshot = [...priorities];
    assert.equal(pickPriority(...priorities), 'P1');
    assert.deepEqual(priorities, snapshot);
});
