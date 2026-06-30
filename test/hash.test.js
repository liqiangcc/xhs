'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { normalizeQuestion, computeQuestionId } = require('../scripts/lib/hash');

test('normalizes questions with the shared historical hash rule', () => {
    assert.equal(normalizeQuestion('ArrayList 和 LinkedList 的区别？'), 'arraylist和linkedlist的区别');
    assert.equal(computeQuestionId('Redis 有哪些集群模式？'), '25cce32833b12a6614779ef8a4ae258c');
    assert.equal(computeQuestionId('ArrayList 和 LinkedList 的区别？'), '7364b88c547ec129fbcb31aa9d14c521');
});
