'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    assertSplitCanonical,
    splitCanonical,
} = require('../src/domain/canonical/split-policy');

function canonical(overrides = {}) {
    return {
        canonical_id: 'cq_source',
        canonical_title: 'Source title',
        aliases: ['Source title'],
        question_ids: ['q1', 'q2'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: 2,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        editorial_note: 'keep-source-metadata',
        ...overrides,
    };
}

test('splits one question into a new canonical while preserving remaining source metadata', () => {
    const result = splitCanonical(canonical(), {
        questionId: 'q2',
        newCanonicalId: 'cq_new',
        title: 'Redis 事件循环',
        questionFacts: {
            aliases: ['Redis 事件循环', 'Redis event loop'],
            primary_domain: { l1: '缓存', l2: 'Redis' },
            primary_entities: ['Redis', 'EventLoop', 'Redis'],
            companies: ['字节', '美团', '字节'],
            frequency: 3,
        },
    });

    assert.deepEqual(result.remaining_source.question_ids, ['q1']);
    assert.equal(result.remaining_source.canonical_id, 'cq_source');
    assert.equal(result.remaining_source.editorial_note, 'keep-source-metadata');

    assert.deepEqual(result.new_canonical, {
        canonical_id: 'cq_new',
        canonical_title: 'Redis 事件循环',
        aliases: ['Redis 事件循环', 'Redis event loop'],
        question_ids: ['q2'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis', 'EventLoop'],
        companies: ['美团', '字节'].sort((a, b) => a.localeCompare(b, 'zh')),
        frequency: 3,
        review_priority: 'P1',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    });
});

test('returns no remaining source when the final question is split out', () => {
    const result = splitCanonical(canonical({ question_ids: ['q1'] }), {
        questionId: 'q1',
        newCanonicalId: 'cq_new',
        title: 'New title',
        questionFacts: { frequency: 1 },
    });

    assert.equal(result.remaining_source, null);
    assert.deepEqual(result.new_canonical.question_ids, ['q1']);
});

test('derives priority from normalized split facts', () => {
    const result = splitCanonical(canonical(), {
        questionId: 'q2',
        newCanonicalId: 'cq_new',
        title: 'New title',
        questionFacts: {
            companies: ['a', 'b', 'c', 'd'],
            frequency: 1,
        },
    });

    assert.equal(result.new_canonical.review_priority, 'P0');
});

test('rejects invalid split requests', () => {
    assert.throws(
        () => assertSplitCanonical(null, 'q1', 'cq_new', 'Title'),
        /source canonical is required/,
    );
    assert.throws(
        () => assertSplitCanonical(canonical(), 'q1', 'cq_source', 'Title'),
        /new-canonical-id must differ from canonical-id/,
    );
    assert.throws(
        () => assertSplitCanonical(canonical(), 'missing', 'cq_new', 'Title'),
        /Question missing is not part of cq_source/,
    );
    assert.throws(
        () => assertSplitCanonical(canonical(), 'q1', 'cq_new', ''),
        /canonical title is required/,
    );
});

test('does not mutate source canonical or split facts', () => {
    const source = canonical();
    const questionFacts = {
        aliases: ['Alias'],
        primary_domain: { l1: 'JVM', l2: 'GC' },
        primary_entities: ['JVM'],
        companies: ['美团'],
        frequency: 1,
    };
    const sourceBefore = structuredClone(source);
    const factsBefore = structuredClone(questionFacts);

    splitCanonical(source, {
        questionId: 'q2',
        newCanonicalId: 'cq_new',
        title: 'New title',
        questionFacts,
    });

    assert.deepEqual(source, sourceBefore);
    assert.deepEqual(questionFacts, factsBefore);
});
