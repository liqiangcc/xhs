const test = require('node:test');
const assert = require('node:assert/strict');

test('Base62 fixed-width capacity covers the declared 10-billion design target', () => {
  assert.equal(62n ** 5n, 916132832n);
  assert.equal(62n ** 6n, 56800235584n);
  assert.ok(62n ** 5n < 10_000_000_000n);
  assert.ok(62n ** 6n >= 10_000_000_000n);
});

test('range allocation model preserves unique issued ids and leaves failed tails unused', () => {
  let maxId = 0;
  const claim = (size) => {
    const start = maxId + 1;
    maxId += size;
    return { next: start, end: maxId };
  };
  const first = claim(3);
  const second = claim(3);
  assert.deepEqual(first, { next: 1, end: 3 });
  assert.deepEqual(second, { next: 4, end: 6 });
  const issued = [first.next, first.next + 1, second.next, second.next + 1];
  assert.equal(new Set(issued).size, issued.length);
  assert.ok(!issued.includes(3));
  assert.ok(!issued.includes(6));
});

test('idempotency model returns an existing short code on retry', () => {
  const mappings = new Map();
  const create = (idempotencyKey, id) => {
    if (mappings.has(idempotencyKey)) return mappings.get(idempotencyKey);
    const code = id.toString(36);
    mappings.set(idempotencyKey, code);
    return code;
  };
  assert.equal(create('tenant-a:req-1', 100), '2s');
  assert.equal(create('tenant-a:req-1', 101), '2s');
  assert.equal(mappings.size, 1);
});
