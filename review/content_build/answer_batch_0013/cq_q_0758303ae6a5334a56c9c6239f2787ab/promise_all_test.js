'use strict';

const assert = require('node:assert/strict');
const { interviewPromiseAll } = require('./promise_all_impl');

async function main() {
  assert.deepEqual(await interviewPromiseAll([]), []);
  assert.deepEqual(await interviewPromiseAll([1, Promise.resolve(2), 3]), [1, 2, 3]);

  let resolveSlow;
  let resolveMiddle;
  const slow = new Promise((resolve) => { resolveSlow = resolve; });
  const middle = new Promise((resolve) => { resolveMiddle = resolve; });
  const orderedAggregate = interviewPromiseAll([slow, Promise.resolve('fast'), middle]);
  resolveMiddle('middle');
  resolveSlow('slow');
  assert.deepEqual(await orderedAggregate, ['slow', 'fast', 'middle']);

  const thenable = { then(resolve) { resolve('thenable'); } };
  assert.deepEqual(await interviewPromiseAll([thenable]), ['thenable']);

  let rejectFirstInput;
  let rejectSecondInput;
  const firstInput = new Promise((_, reject) => { rejectFirstInput = reject; });
  const secondInput = new Promise((_, reject) => { rejectSecondInput = reject; });
  const rejectionAggregate = interviewPromiseAll([firstInput, secondInput]);
  const firstObservedRejection = new Error('second input rejected first');
  rejectSecondInput(firstObservedRejection);
  rejectFirstInput(new Error('first input rejected later'));
  await assert.rejects(rejectionAggregate, (error) => error === firstObservedRejection);

  const iterableError = new Error('iteration failed');
  const badIterable = {
    *[Symbol.iterator]() {
      yield Promise.resolve(1);
      throw iterableError;
    },
  };
  await assert.rejects(interviewPromiseAll(badIterable), (error) => error === iterableError);

  console.log('PASS cases=6 order=preserved thenable=assimilated first_rejection=observed iterable_throw=rejected');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
