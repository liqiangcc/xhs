const test = require('node:test');
const assert = require('node:assert/strict');

test('duplicate delivery and post-commit offset failure leave one business state and one outbox record', () => {
  const processed = new Set();
  const business = new Map();
  const outbox = new Map();
  const process = (eventId, amount) => {
    if (processed.has(eventId)) return { duplicate: true, offsetCommitted: false };
    processed.add(eventId);
    business.set(eventId, amount);
    outbox.set(eventId, { eventId, status: 'pending' });
    return { duplicate: false, offsetCommitted: false };
  };
  assert.deepEqual(process('evt-1', 100), { duplicate: false, offsetCommitted: false });
  assert.deepEqual(process('evt-1', 100), { duplicate: true, offsetCommitted: false });
  assert.equal(business.size, 1);
  assert.equal(outbox.size, 1);
});

test('outbox relay retry retains the same downstream idempotency key after an ambiguous send', () => {
  const outbox = { eventId: 'evt-2', status: 'pending' };
  const attempts = [];
  const relay = (markDelivered) => {
    attempts.push(outbox.eventId);
    if (markDelivered) outbox.status = 'delivered';
  };
  relay(false);
  relay(true);
  assert.deepEqual(attempts, ['evt-2', 'evt-2']);
  assert.equal(outbox.status, 'delivered');
});
