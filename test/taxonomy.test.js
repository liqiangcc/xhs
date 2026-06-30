'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
    validateDomain,
    validateQuestionType,
    validateCognitiveDepth,
    normalizeEntity,
} = require('../scripts/lib/taxonomy');

test('validates canonical taxonomy values', () => {
    const domain = validateDomain({ l1: 'Java基础', l2: 'JVM' });
    assert.equal(domain.valid, true);
    assert.equal(domain.reason, 'canonical');
    assert.deepEqual(domain.normalized_domain, { l1: 'Java基础', l2: 'JVM' });
    assert.equal(validateQuestionType('原理深度_UnderTheHood').valid, true);
    assert.equal(validateCognitiveDepth('L2_Mechanism').valid, true);
});

test('normalizes historical taxonomy aliases without mutating source values', () => {
    const domain = validateDomain({ l1: 'Java', l2: 'Java并发' });
    assert.equal(domain.valid, true);
    assert.equal(domain.reason, 'legacy_alias');
    assert.deepEqual(domain.normalized_domain, { l1: 'Java基础', l2: '并发编程(JUC)' });
    assert.equal(validateQuestionType('手写代码_Coding').normalized_value, '算法手撕_Coding');
    assert.equal(validateCognitiveDepth('L4_Systematic').normalized_value, 'L3_Diagnostic');
});

test('normalizes pair aliases and long-tail l2 values', () => {
    const pair = validateDomain({ l1: '工程实践', l2: 'Java基础' });
    assert.equal(pair.valid, true);
    assert.equal(pair.reason, 'legacy_pair_alias');
    assert.deepEqual(pair.normalized_domain, { l1: 'Java基础', l2: '语言特性' });

    const fallback = validateDomain({ l1: '系统设计', l2: '未知长尾标签' });
    assert.equal(fallback.valid, true);
    assert.equal(fallback.reason, 'legacy_l2_other');
    assert.deepEqual(fallback.normalized_domain, { l1: '系统设计', l2: '其他' });
});

test('reports unknown taxonomy values', () => {
    assert.equal(validateDomain({ l1: '不存在', l2: '也不存在' }).valid, false);
    assert.equal(validateQuestionType('Unknown_Type').valid, false);
    assert.equal(validateCognitiveDepth('L9').valid, false);
});

test('normalizes common entity aliases', () => {
    assert.equal(normalizeEntity('redis'), 'Redis');
    assert.equal(normalizeEntity('HashMap'), 'HashMap');
    assert.equal(normalizeEntity('zk'), 'ZooKeeper');
});
