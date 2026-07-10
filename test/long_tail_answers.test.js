'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { parseAnswerMetadata, validateAnswerContent } = require('../scripts/lib/answer_store');
const {
    GENERATOR_VERSION,
    answerType,
    codingGuide,
    renderAnswer,
} = require('../scripts/content/generate_long_tail_answers');

function canonical(overrides = {}) {
    return {
        canonical_id: 'cq_generated_test',
        canonical_title: 'HashMap 中链表转红黑树的条件是什么？',
        aliases: [],
        question_ids: ['question-a'],
        primary_domain: { l1: 'Java基础', l2: '集合' },
        primary_entities: ['HashMap'],
        companies: ['示例公司'],
        frequency: 1,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(overrides = {}) {
    return {
        original_question: 'HashMap 中链表转红黑树的条件是什么？',
        question_type: '原理深度_UnderTheHood',
        tech_entities: ['HashMap', '红黑树'],
        ...overrides,
    };
}

test('renders a deterministic entity-grounded long-tail answer', () => {
    const content = renderAnswer(canonical(), [question()], '2026-07-10');
    const metadata = parseAnswerMetadata(content);
    assert.equal(metadata.status, 'ready');
    assert.equal(metadata.generator_version, GENERATOR_VERSION);
    assert.equal(metadata.quality_tier, 'long_tail_baseline');
    assert.match(content, /数组容量至少 64/);
    assert.match(content, /项目经验版/);
    assert.equal(validateAnswerContent({ metadata, content }).length, 0);
    assert.equal(content, renderAnswer(canonical(), [question()], '2026-07-10'));
});

test('coding answers include an invariant complexity and Java implementation', () => {
    const record = canonical({
        canonical_title: '算法：反转链表',
        primary_domain: { l1: '算法', l2: '链表' },
        primary_entities: ['链表反转'],
    });
    const source = question({
        original_question: '算法：反转链表',
        question_type: '算法手撕_Coding',
        tech_entities: ['链表反转'],
    });
    const content = renderAnswer(record, [source], '2026-07-10');
    assert.equal(answerType([source]), 'coding');
    assert.match(content, /算法不变量/);
    assert.match(content, /~~~java/);
    assert.match(content, /static ListNode reverse/);
    assert.match(codingGuide('反转链表').complexity, /O\(n\)/);
});

test('project and behavioral answers require real evidence instead of fabricated experience', () => {
    const record = canonical({
        canonical_title: '你遇到过的最大挑战是什么？',
        primary_domain: { l1: '其他', l2: '行为面试' },
        primary_entities: [],
    });
    const source = question({
        original_question: record.canonical_title,
        question_type: '行为软技_Behavioral',
        tech_entities: [],
    });
    const content = renderAnswer(record, [source], '2026-07-10');
    assert.equal(answerType([source]), 'behavior');
    assert.match(content, /真实 STAR 案例/);
    assert.match(content, /把团队成果说成个人贡献/);
});
