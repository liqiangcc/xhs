'use strict';

const assert = require('node:assert/strict');

function advance(history, value) {
  if (Object.is(history.current, value)) {
    return { history, previous: history.previous, changed: false };
  }
  const next = { current: value, previous: history.current };
  return { history: next, previous: next.previous, changed: true };
}

let state = { current: 1, previous: undefined };
assert.equal(state.previous, undefined);

let result = advance(state, 2);
assert.equal(result.changed, true);
assert.deepEqual(result.history, { current: 2, previous: 1 });
assert.equal(result.previous, 1);
state = result.history;

result = advance(state, 2);
assert.equal(result.changed, false);
assert.strictEqual(result.history, state);
assert.equal(result.previous, 1);

result = advance(state, 3);
assert.deepEqual(result.history, { current: 3, previous: 2 });
assert.equal(result.previous, 2);

const nanState = { current: Number.NaN, previous: 7 };
result = advance(nanState, Number.NaN);
assert.equal(result.changed, false);
assert.strictEqual(result.history, nanState);

const minusZeroState = { current: -0, previous: 9 };
result = advance(minusZeroState, 0);
assert.equal(result.changed, true);
assert.equal(Object.is(result.history.current, 0), true);
assert.equal(Object.is(result.previous, -0), true);

console.log('PASS initial=undefined transitions=1->2->3 stable_same=true object_is_edges=true');
