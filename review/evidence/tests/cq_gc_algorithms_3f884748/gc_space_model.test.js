'use strict';

const assert = require('node:assert/strict');

const heap = [
    { id: 'a', live: true },
    { id: 'b', live: false },
    { id: 'c', live: true },
    { id: 'd', live: false },
];

const swept = heap.map((object) => object.live ? object : null);
assert.deepEqual(swept.map((object) => object?.id ?? null), ['a', null, 'c', null]);
assert.equal(swept.slice(0, 3).every((object) => object === null), false, 'sweep can leave non-contiguous holes');
assert.equal(swept.some((_, index) => swept[index] === null && swept[index + 1] === null), false, 'two free slots need not be contiguous after sweep');

const compacted = heap.filter((object) => object.live).concat([null, null]);
assert.deepEqual(compacted.map((object) => object?.id ?? null), ['a', 'c', null, null]);
assert.equal(compacted.slice(2).every((object) => object === null), true, 'compaction leaves a contiguous free suffix');
assert.equal(compacted.some((_, index) => compacted[index] === null && compacted[index + 1] === null), true, 'compaction can satisfy a two-slot contiguous allocation');

const toSpace = heap.filter((object) => object.live).map((object) => ({ ...object }));
assert.deepEqual(toSpace.map((object) => object.id), ['a', 'c']);
assert.notStrictEqual(toSpace[0], heap[0], 'copying moves a surviving object into target space');
