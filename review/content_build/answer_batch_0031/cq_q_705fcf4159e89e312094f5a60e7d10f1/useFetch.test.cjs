'use strict';
const assert = require('node:assert/strict');
const { createUseFetch } = require('./useFetch.cjs');

function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function createHarness() {
  const states = [];
  const effects = [];
  let stateIndex = 0;
  let effectIndex = 0;

  const React = {
    useState(initial) {
      const i = stateIndex++;
      if (!(i in states)) states[i] = initial;
      return [states[i], updater => {
        states[i] = typeof updater === 'function' ? updater(states[i]) : updater;
      }];
    },
    useEffect(setup, deps) {
      const i = effectIndex++;
      const prev = effects[i];
      const changed = !prev || prev.deps.length !== deps.length || deps.some((d, j) => !Object.is(d, prev.deps[j]));
      effects[i] = { setup, deps, cleanup: prev?.cleanup, changed };
    },
  };

  function render(hook, ...args) {
    stateIndex = 0;
    effectIndex = 0;
    const result = hook(...args);
    for (const effect of effects) {
      if (!effect.changed) continue;
      if (effect.cleanup) effect.cleanup();
      effect.cleanup = effect.setup() || undefined;
      effect.changed = false;
    }
    return result;
  }

  function unmount() {
    for (const effect of effects) if (effect.cleanup) effect.cleanup();
  }

  return { React, render, unmount, states };
}

async function flush() {
  await new Promise(resolve => setImmediate(resolve));
}

async function main() {
  const harness = createHarness();
  const useFetch = createUseFetch(harness.React);
  const calls = [];
  const queue = [];
  const request = (params, { signal }) => {
    const d = deferred();
    calls.push({ params, signal, d });
    queue.push(d);
    return d.promise;
  };

  const p1 = { page: 1 };
  harness.render(useFetch, request, p1);
  assert.equal(calls.length, 1, 'mount triggers one request');
  assert.equal(harness.states[0].loading, true);

  harness.render(useFetch, request, p1);
  assert.equal(calls.length, 1, 'same params identity must not retrigger');

  const p1sameValueNewIdentity = { page: 1 };
  harness.render(useFetch, request, p1sameValueNewIdentity);
  assert.equal(calls.length, 2, 'new object identity retriggers');
  assert.equal(calls[0].signal.aborted, true, 'cleanup aborts previous request');

  p1sameValueNewIdentity.page = 2;
  harness.render(useFetch, request, p1sameValueNewIdentity);
  assert.equal(calls.length, 2, 'in-place mutation keeps identity and does not retrigger');

  const p2 = { page: 2 };
  harness.render(useFetch, request, p2);
  assert.equal(calls.length, 3, 'immutable params replacement retriggers');
  assert.equal(calls[1].signal.aborted, true, 'second stale request aborted');

  queue[0].resolve('old-page-1');
  queue[1].resolve('old-equal-value');
  await flush();
  assert.equal(harness.states[0].data, null, 'stale responses cannot write state');

  queue[2].resolve('page-2');
  await flush();
  harness.render(useFetch, request, p2);
  assert.equal(harness.states[0].data, 'page-2');
  assert.equal(harness.states[0].loading, false);
  assert.equal(calls.length, 3, 'state re-render with stable deps does not refetch');

  const p3 = { page: 3 };
  harness.render(useFetch, request, p3);
  assert.equal(calls.length, 4);
  queue[3].reject(new Error('network'));
  await flush();
  harness.render(useFetch, request, p3);
  assert.equal(harness.states[0].error.message, 'network');
  assert.equal(harness.states[0].loading, false);

  harness.unmount();
  assert.equal(calls[3].signal.aborted, true, 'unmount cleanup aborts active request');
  console.log('PASS mount=1 same-identity=no-refetch new-identity=refetch mutation=no-refetch stale-writes=blocked error=recorded cleanup=abort');
}

main().catch(error => { console.error(error); process.exit(1); });
