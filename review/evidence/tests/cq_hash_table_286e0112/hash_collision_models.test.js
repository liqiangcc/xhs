const test = require('node:test');
const assert = require('node:assert/strict');

test('separate chaining retains distinct keys that share an initial bucket', () => {
  const buckets = Array.from({ length: 3 }, () => []);
  const index = () => 1;
  const put = (key, value) => buckets[index(key)].push({ key, value });
  const get = (key) => buckets[index(key)].find((entry) => entry.key === key)?.value;
  put('alpha', 1);
  put('beta', 2);
  assert.equal(get('alpha'), 1);
  assert.equal(get('beta'), 2);
});

test('a third colliding key requires examining all prior bucket candidates in this model', () => {
  const bucket = [{ key: 'alpha', value: 1 }, { key: 'beta', value: 2 }, { key: 'gamma', value: 3 }];
  let comparisons = 0;
  const value = bucket.find((entry) => {
    comparisons += 1;
    return entry.key === 'gamma';
  })?.value;
  assert.equal(value, 3);
  assert.equal(comparisons, 3);
  assert.equal(bucket.length / 3, 1);
});

test('open addressing tombstone preserves the probe path after deletion', () => {
  const slots = Array(5).fill(null);
  const TOMBSTONE = Symbol('tombstone');
  const home = () => 0;
  const put = (key, value) => {
    for (let step = 0; step < slots.length; step += 1) {
      const i = (home(key) + step) % slots.length;
      if (slots[i] === null || slots[i] === TOMBSTONE) {
        slots[i] = { key, value };
        return;
      }
    }
    throw new Error('full');
  };
  const get = (key) => {
    for (let step = 0; step < slots.length; step += 1) {
      const i = (home(key) + step) % slots.length;
      if (slots[i] === null) return undefined;
      if (slots[i] !== TOMBSTONE && slots[i].key === key) return slots[i].value;
    }
    return undefined;
  };
  put('alpha', 1);
  put('beta', 2);
  slots[0] = TOMBSTONE;
  assert.equal(get('beta'), 2);
});

test('rehashing after capacity growth retains every live mapping', () => {
  const entries = [['a', 1], ['b', 2], ['c', 3]];
  let reinserts = 0;
  const table = (capacity) => {
    const buckets = Array.from({ length: capacity }, () => []);
    for (const [key, value] of entries) {
      reinserts += 1;
      buckets[key.charCodeAt(0) % capacity].push([key, value]);
    }
    return buckets;
  };
  const grown = table(7);
  assert.deepEqual(grown.flat().sort(), entries.slice().sort());
  assert.equal(reinserts, entries.length);
});
