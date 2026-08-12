'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    assertMergeableCanonical,
    mergeCanonical,
} = require('../src/domain/canonical/merge-policy');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: [`q_${id}`],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: 1,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

test('merges source into target while preserving target identity and domain', () => {
    const target = canonical('cq_target', {
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？', 'Redis 快的原因'],
        question_ids: ['q2', 'q1'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: 2,
        review_priority: 'P1',
        answer_status: 'ready',
        editorial_note: 'keep-target-metadata',
    });
    const source = canonical('cq_source', {
        canonical_title: 'Redis 单线程为什么快？',
        aliases: ['Redis 快的原因', 'Redis 单线程模型'],
        question_ids: ['q3', 'q2'],
        primary_domain: { l1: '并发', l2: '线程模型' },
        primary_entities: ['Redis', 'EventLoop'],
        companies: ['字节', '美团'],
        frequency: 4,
        review_priority: 'P0',
        answer_status: 'missing',
    });

    const merged = mergeCanonical(target, source);

    assert.equal(merged.canonical_id, 'cq_target');
    assert.equal(merged.canonical_title, 'Redis 为什么快？');
    assert.deepEqual(merged.primary_domain, { l1: '缓存', l2: 'Redis' });
    assert.equal(merged.editorial_note, 'keep-target-metadata');
    assert.deepEqual(merged.question_ids, ['q1', 'q2', 'q3']);
    assert.deepEqual(merged.primary_entities, ['EventLoop', 'Redis']);
    assert.deepEqual(merged.companies, ['美团', '字节']);
    assert.deepEqual(
        [...merged.aliases].sort(),
        [
            'Redis 为什么快？',
            'Redis 快的原因',
            'Redis 单线程模型',
            'Redis 单线程为什么快？',
        ].sort(),
    );
    assert.equal(new Set(merged.aliases).size, merged.aliases.length);
    assert.equal(merged.frequency, 4);
    assert.equal(merged.review_priority, 'P0');
    assert.equal(merged.answer_status, 'needs_update');
    assert.equal(merged.schema_version, 'canonical_question.v1');
});

test('uses source title only when target title is empty', () => {
    const merged = mergeCanonical(
        canonical('cq_target', { canonical_title: '' }),
        canonical('cq_source', { canonical_title: 'Source title' }),
    );
    assert.equal(merged.canonical_title, 'Source title');
    assert.equal(merged.aliases.includes('Source title'), true);
});

test('preserves current pre-refresh frequency behavior by taking the maximum', () => {
    assert.equal(
        mergeCanonical(
            canonical('cq_target', { frequency: 5 }),
            canonical('cq_source', { frequency: 3 }),
        ).frequency,
        5,
    );
});

test('rejects missing records and self merge', () => {
    assert.throws(() => assertMergeableCanonical(null, canonical('cq_source')), /target canonical is required/);
    assert.throws(() => assertMergeableCanonical(canonical('cq_target'), null), /source canonical is required/);
    assert.throws(
        () => assertMergeableCanonical(canonical('cq_same'), canonical('cq_same')),
        /target and source must be different/,
    );
});

test('does not mutate target or source records', () => {
    const target = canonical('cq_target', { aliases: ['target'] });
    const source = canonical('cq_source', { aliases: ['source'] });
    const targetBefore = structuredClone(target);
    const sourceBefore = structuredClone(source);

    mergeCanonical(target, source);

    assert.deepEqual(target, targetBefore);
    assert.deepEqual(source, sourceBefore);
});
