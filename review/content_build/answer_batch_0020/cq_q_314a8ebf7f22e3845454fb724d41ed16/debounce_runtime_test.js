'use strict';

const assert = require('node:assert/strict');
const { debounce } = require('./debounce_runtime_mirror');

class FakeTimers {
  constructor() {
    this.now = 0;
    this.nextId = 1;
    this.tasks = new Map();
  }

  setTimeout(fn, delay) {
    const id = this.nextId++;
    this.tasks.set(id, { id, due: this.now + Number(delay), fn });
    return id;
  }

  clearTimeout(id) {
    this.tasks.delete(id);
  }

  advance(ms) {
    const target = this.now + ms;
    for (;;) {
      const due = [...this.tasks.values()]
        .filter((task) => task.due <= target)
        .sort((a, b) => a.due - b.due || a.id - b.id)[0];
      if (!due) break;
      this.tasks.delete(due.id);
      this.now = due.due;
      due.fn();
    }
    this.now = target;
  }
}

const realSetTimeout = global.setTimeout;
const realClearTimeout = global.clearTimeout;
const clock = new FakeTimers();
global.setTimeout = clock.setTimeout.bind(clock);
global.clearTimeout = clock.clearTimeout.bind(clock);

try {
  {
    const calls = [];
    const receiver = { tag: 'r1' };
    const wrapped = debounce(function (...args) {
      calls.push({ receiver: this, args, at: clock.now });
    }, 100);

    wrapped.call(receiver, 'A', 1);
    clock.advance(99);
    assert.equal(calls.length, 0);
    clock.advance(1);
    assert.deepEqual(calls, [{ receiver, args: ['A', 1], at: 100 }]);
  }

  {
    const calls = [];
    const wrapped = debounce((value) => calls.push([value, clock.now]), 100);
    wrapped('A');
    clock.advance(30);
    wrapped('B');
    clock.advance(40);
    wrapped('C');
    clock.advance(99);
    assert.deepEqual(calls, []);
    clock.advance(1);
    assert.deepEqual(calls, [['C', 270]]);
  }

  {
    const calls = [];
    const wrapped = debounce((value) => calls.push([value, clock.now]), 50, true);
    wrapped('first');
    assert.deepEqual(calls, [['first', 270]]);
    clock.advance(20);
    wrapped('suppressed');
    assert.equal(calls.length, 1);
    clock.advance(50);
    wrapped('after-quiet');
    assert.deepEqual(calls, [['first', 270], ['after-quiet', 340]]);
  }

  {
    const a = [];
    const b = [];
    const left = debounce((value) => a.push(value), 10);
    const right = debounce((value) => b.push(value), 10);
    left(1);
    right(2);
    left(3);
    clock.advance(10);
    assert.deepEqual(a, [3]);
    assert.deepEqual(b, [2]);
  }

  {
    const calls = [];
    const wrapped = debounce((value) => calls.push(value), 0);
    wrapped('zero');
    assert.deepEqual(calls, []);
    clock.advance(0);
    assert.deepEqual(calls, ['zero']);
  }

  {
    assert.throws(() => debounce(() => {}, -1), RangeError);
    assert.throws(() => debounce(() => {}, Infinity), RangeError);
  }

  console.log(
    'PASS fixed=6 fake_clock=deterministic trailing=last-call leading=immediate-no-trailing this-and-args=preserved',
  );
} finally {
  global.setTimeout = realSetTimeout;
  global.clearTimeout = realClearTimeout;
}
