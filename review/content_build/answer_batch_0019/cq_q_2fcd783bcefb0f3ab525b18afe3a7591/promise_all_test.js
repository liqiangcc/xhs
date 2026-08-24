'use strict';

const assert = require('node:assert/strict');
const { myPromiseAll } = require('./promise_all');

function afterMicrotasks(value, ticks, shouldReject = false) {
  let p = Promise.resolve();
  for (let i = 0; i < ticks; i++) {
    p = p.then(() => undefined);
  }
  return p.then(() => {
    if (shouldReject) {
      throw value;
    }
    return value;
  });
}

async function capture(promise) {
  try {
    return { status: 'fulfilled', value: await promise };
  } catch (error) {
    return { status: 'rejected', reason: error };
  }
}

function normalizeOutcome(outcome) {
  if (outcome.status === 'fulfilled') {
    return { status: 'fulfilled', value: outcome.value };
  }
  const reason = outcome.reason;
  if (reason instanceof Error) {
    return { status: 'rejected', reason: `${reason.name}:${reason.message}` };
  }
  return { status: 'rejected', reason };
}

async function assertMatchesNative(factory, label) {
  const nativeOutcome = normalizeOutcome(await capture(Promise.all(factory())));
  const customOutcome = normalizeOutcome(await capture(myPromiseAll(factory())));
  assert.deepEqual(customOutcome, nativeOutcome, label);
}

async function runFixedCases() {
  let fixed = 0;

  await assertMatchesNative(() => [], 'empty array');
  fixed++;

  await assertMatchesNative(() => [1, 'x', null, undefined], 'plain values');
  fixed++;

  await assertMatchesNative(
    () => [afterMicrotasks('slow', 4), afterMicrotasks('fast', 0), afterMicrotasks('mid', 2)],
    'input order is preserved despite completion order',
  );
  fixed++;

  await assertMatchesNative(
    () => [Promise.resolve(Promise.resolve(7)), 8],
    'nested promise adoption',
  );
  fixed++;

  await assertMatchesNative(
    () => [
      { then(resolve) { resolve('thenable'); } },
      Promise.resolve('promise'),
    ],
    'thenable adoption',
  );
  fixed++;

  await assertMatchesNative(
    () => [afterMicrotasks('later-reject', 3, true), afterMicrotasks('first-reject', 0, true)],
    'first observed rejection wins',
  );
  fixed++;

  await assertMatchesNative(
    () => new Set([Promise.resolve(1), 2, afterMicrotasks(3, 1)]),
    'non-array iterable Set',
  );
  fixed++;

  await assertMatchesNative(
    () => (function* generator() {
      yield Promise.resolve('a');
      yield 'b';
      yield afterMicrotasks('c', 2);
    }()),
    'generator iterable',
  );
  fixed++;

  await assertMatchesNative(
    () => {
      const values = [];
      values.length = 3;
      values[1] = Promise.resolve('middle');
      return values;
    },
    'sparse array holes become undefined',
  );
  fixed++;

  await assertMatchesNative(
    () => ({
      [Symbol.iterator]() {
        let step = 0;
        return {
          next() {
            if (step++ === 0) return { done: false, value: Promise.resolve(1) };
            throw new Error('iterator-boom');
          },
        };
      },
    }),
    'iterator throw rejects result promise',
  );
  fixed++;

  await assertMatchesNative(
    () => [
      { then(_resolve, reject) { reject('thenable-reject'); } },
      afterMicrotasks('late', 2),
    ],
    'rejecting thenable',
  );
  fixed++;

  const custom = myPromiseAll([]);
  let callbackRan = false;
  custom.then(() => { callbackRan = true; });
  assert.equal(callbackRan, false, 'then callback for empty iterable still runs asynchronously');
  await custom;
  await Promise.resolve();
  assert.equal(callbackRan, true, 'then callback eventually runs');
  fixed++;

  return fixed;
}

function makePrng(seed) {
  let state = seed >>> 0;
  return function next() {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function buildRandomInput(descriptors) {
  return descriptors.map((descriptor) => {
    switch (descriptor.kind) {
      case 'plain':
        return descriptor.value;
      case 'promise':
        return afterMicrotasks(descriptor.value, descriptor.ticks, false);
      case 'reject':
        return afterMicrotasks(descriptor.value, descriptor.ticks, true);
      case 'thenable':
        return {
          then(resolve) {
            let p = Promise.resolve();
            for (let i = 0; i < descriptor.ticks; i++) p = p.then(() => undefined);
            p.then(() => resolve(descriptor.value));
          },
        };
      default:
        throw new Error(`unknown descriptor kind: ${descriptor.kind}`);
    }
  });
}

async function runRandomizedCases() {
  const random = makePrng(0x5eed1234);
  const cases = 2000;

  for (let caseIndex = 0; caseIndex < cases; caseIndex++) {
    const length = Math.floor(random() * 12);
    const descriptors = [];
    for (let i = 0; i < length; i++) {
      const r = random();
      const value = `c${caseIndex}-i${i}-v${Math.floor(random() * 100000)}`;
      const ticks = Math.floor(random() * 5);
      if (r < 0.35) descriptors.push({ kind: 'plain', value, ticks });
      else if (r < 0.68) descriptors.push({ kind: 'promise', value, ticks });
      else if (r < 0.9) descriptors.push({ kind: 'thenable', value, ticks });
      else descriptors.push({ kind: 'reject', value: `reject:${value}`, ticks });
    }

    const nativeOutcome = normalizeOutcome(await capture(Promise.all(buildRandomInput(descriptors))));
    const customOutcome = normalizeOutcome(await capture(myPromiseAll(buildRandomInput(descriptors))));
    assert.deepEqual(customOutcome, nativeOutcome, `randomized case ${caseIndex}`);
  }

  return cases;
}

(async () => {
  const fixed = await runFixedCases();
  const randomized = await runRandomizedCases();
  console.log(`PASS fixed=${fixed} randomized=${randomized} oracle=native-Promise.all iterable=supported order=input reject=first-observed thenable=adopted empty=fulfilled`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
