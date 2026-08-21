'use strict';

const assert = require('node:assert/strict');
const { groupBy } = require('./groupBy');

function entries(map) {
  return Array.from(map.entries());
}

function sameValueZero(a, b) {
  return a === b || (Number.isNaN(a) && Number.isNaN(b));
}

function slowOracle(items, keySelector) {
  const result = [];
  for (let index = 0; index < items.length; index += 1) {
    const item = items[index];
    const key = keySelector(item, index, items);
    let bucket = null;
    for (const pair of result) {
      if (sameValueZero(pair[0], key)) {
        bucket = pair[1];
        break;
      }
    }
    if (bucket === null) {
      result.push([key, [item]]);
    } else {
      bucket.push(item);
    }
  }
  return result;
}

function normalizePairs(pairs) {
  return pairs.map(([key, values]) => [
    typeof key === 'number' && Number.isNaN(key) ? 'NaN' : `${typeof key}:${String(key)}`,
    values.map((item) => item.id),
  ]);
}

function assertSameGrouping(actualMap, expectedPairs) {
  assert.deepEqual(normalizePairs(entries(actualMap)), normalizePairs(expectedPairs));
}

const people = [
  { id: 'a', sex: 'F', age: 20 },
  { id: 'b', sex: 'M', age: 21 },
  { id: 'c', sex: 'F', age: 21 },
  { id: 'd', sex: 'M', age: 20 },
  { id: 'e', sex: 'F', age: 20 },
];

assert.deepEqual(entries(groupBy([], (item) => item)), []);
assert.deepEqual(entries(groupBy(people, (item) => item.sex)), [
  ['F', [people[0], people[2], people[4]]],
  ['M', [people[1], people[3]]],
]);
assert.deepEqual(entries(groupBy(people, (item) => item.age)), [
  [20, [people[0], people[3], people[4]]],
  [21, [people[1], people[2]]],
]);
assert.deepEqual(entries(groupBy(people, (_item, index) => index % 2)), [
  [0, [people[0], people[2], people[4]]],
  [1, [people[1], people[3]]],
]);
assert.deepEqual(entries(groupBy([{ id: 'x', key: '__proto__' }, { id: 'y', key: 'constructor' }], (item) => item.key)).map(([key, values]) => [key, values.map((item) => item.id)]), [
  ['__proto__', ['x']],
  ['constructor', ['y']],
]);
assert.equal(groupBy([{ id: 'n', key: 1 }, { id: 's', key: '1' }], (item) => item.key).size, 2);
assert.throws(() => groupBy(null, () => 1), /items must be an array/);
assert.throws(() => groupBy([], null), /keySelector must be a function/);

const originalOrder = people.map((item) => item.id);
const bySex = groupBy(people, (item) => item.sex);
assert.deepEqual(people.map((item) => item.id), originalOrder);
assert.notEqual(bySex.get('F'), people);
assert.equal(bySex.get('F')[0], people[0]);

let state = 0x6d2b79f5;
function nextUInt() {
  state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
  return state;
}

for (let round = 0; round < 1000; round += 1) {
  const length = nextUInt() % 40;
  const items = [];
  for (let i = 0; i < length; i += 1) {
    items.push({
      id: `${round}:${i}`,
      sex: (nextUInt() & 1) === 0 ? 'F' : 'M',
      age: 18 + (nextUInt() % 8),
      score: nextUInt() % 100,
    });
  }

  const selectors = [
    (item) => item.sex,
    (item) => item.age,
    (item) => item.age % 3,
    (item) => item.score < 60,
  ];

  for (const selector of selectors) {
    assertSameGrouping(groupBy(items, selector), slowOracle(items, selector));
  }
}

console.log('PASS fixed=10 randomized_rounds=1000 selectors=4 oracle=slow-pair-scan order_preserved=true input_array_unchanged=true');
