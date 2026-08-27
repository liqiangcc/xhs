'use strict';
const assert = require('assert');
const { createIntervalApi } = require('./interval_polyfill');

class FakeTimers {
  constructor() { this.nextId = 1; this.pending = new Map(); this.delays = []; }
  setTimeout(fn, delay) {
    const id = this.nextId++;
    this.pending.set(id, { fn, delay });
    this.delays.push(delay);
    return id;
  }
  clearTimeout(id) { this.pending.delete(id); }
  firstId() { return this.pending.keys().next().value; }
  fire(id) {
    const task = this.pending.get(id);
    if (!task) return false;
    this.pending.delete(id);
    task.fn();
    return true;
  }
}

const timers = new FakeTimers();
const api = createIntervalApi(timers.setTimeout.bind(timers), timers.clearTimeout.bind(timers));

let calls = 0;
const repeating = api.setIntervalPolyfill(() => { calls++; }, 25);
assert.strictEqual(timers.pending.size, 1);
let id = timers.firstId();
assert.strictEqual(timers.fire(id), true);
assert.strictEqual(calls, 1);
assert.strictEqual(timers.pending.size, 1);
id = timers.firstId();
assert.strictEqual(timers.fire(id), true);
assert.strictEqual(calls, 2);
assert.strictEqual(timers.pending.size, 1);
api.clearIntervalPolyfill(repeating);
assert.strictEqual(timers.pending.size, 0);
api.clearIntervalPolyfill(repeating);
assert.strictEqual(timers.pending.size, 0);

let beforeFirst = 0;
const early = api.setIntervalPolyfill(() => { beforeFirst++; }, 7);
assert.strictEqual(timers.pending.size, 1);
api.clearIntervalPolyfill(early);
assert.strictEqual(timers.pending.size, 0);
assert.strictEqual(beforeFirst, 0);

let insideCalls = 0;
let self;
self = api.setIntervalPolyfill(() => {
  insideCalls++;
  api.clearIntervalPolyfill(self);
}, 11);
assert.strictEqual(timers.pending.size, 1);
assert.strictEqual(timers.fire(timers.firstId()), true);
assert.strictEqual(insideCalls, 1);
assert.strictEqual(timers.pending.size, 0);

assert.throws(() => api.setIntervalPolyfill(null, 1), TypeError);
api.clearIntervalPolyfill(Object.freeze({}));
assert.deepStrictEqual(timers.delays, [25, 25, 25, 7, 11]);

console.log('PASS repeat-reschedules clear-stops clear-before-first clear-inside-callback double-clear unknown-handle delay-forwarding callback-type-check');
