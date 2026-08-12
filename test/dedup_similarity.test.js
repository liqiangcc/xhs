'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    tokenizeSimilarityText,
    jaccardSimilarity,
    measureQuestionSimilarity,
} = require('../src/domain/dedup/similarity');

test('dedup similarity preserves historical english and chinese token signals', () => {
    assert.deepEqual(
        [...tokenizeSimilarityText('Redis 为什么快？')],
        ['redis', '为什', '什么', '么快'],
    );
    assert.deepEqual([...tokenizeSimilarityText('A？')], []);
    assert.deepEqual([...tokenizeSimilarityText('快？')], ['快']);
});

test('jaccard similarity is a signal and does not classify a semantic relation', () => {
    const signal = measureQuestionSimilarity(
        'Redis 为什么快？',
        'Redis 为什么这么快？',
        { threshold: 0.38 },
    );

    assert.equal(signal.metric, 'jaccard');
    assert.equal(signal.threshold, 0.38);
    assert.equal(signal.matched, true);
    assert.ok(signal.score > 0.38);
    assert.equal(Object.hasOwn(signal, 'relation'), false);
    assert.equal(Object.hasOwn(signal, 'canonical_id'), false);
});

test('jaccard similarity handles empty sets and validates thresholds', () => {
    assert.equal(jaccardSimilarity(new Set(), new Set(['redis'])), 0);
    assert.equal(jaccardSimilarity(new Set(['redis']), new Set(['redis'])), 1);
    assert.throws(
        () => measureQuestionSimilarity('a', 'b', { threshold: 1.1 }),
        /Invalid similarity threshold/,
    );
});
