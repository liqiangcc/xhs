'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const QUALITY = require('../config/answer_quality.json');
const { sha256, validateAnswerEvidence, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');

function candidate(content, type = 'concept') {
    return { metadata: { canonical_id: 'cq_redis', answer_type: type }, content };
}

function context() {
    return {
        canonical: { canonical_id: 'cq_redis', canonical_title: 'Redis 为什么快？' },
        primary_entities: ['Redis'], source_variants: ['Redis 为什么快？'],
        source_questions: [{ question_id: 'q1', original_question: 'Redis 为什么快？' }],
    };
}

function evidence(content) {
    return {
        schema_version: 'answer_evidence.v1', canonical_id: 'cq_redis', candidate_sha256: sha256(content), checked_at: '2026-07-11',
        writer: { writer_id: 'writer', writer_version: 'model-v1' },
        sources: [{ source_id: 's1', title: 'Redis docs', locator: 'https://redis.io/docs/', source_type: 'official_documentation', checked_at: '2026-07-11' }],
        claims: [{ claim_id: 'c1', text: 'event loop', source_ids: ['s1'], answer_locations: ['原理机制'] }],
        source_question_coverage: [{ question_id: 'q1', covered: true, answer_locations: ['核心结论'] }],
        review: { reviewer_id: 'reviewer', review_version: 'model-v2', independent: true, decision: 'pass', revision_round: 1, hard_failures: [], scores: {} },
    };
}

test('evidence requires versioned writer reviewer sources claims and source-question coverage', () => {
    const content = 'Redis event loop';
    const valid = validateAnswerEvidence(evidence(content), candidate(content), context(), QUALITY);
    assert.deepEqual(valid, { errors: [], hard_failures: [] });

    const invalid = evidence(content);
    invalid.sources = [];
    invalid.claims[0].source_ids = ['missing'];
    invalid.source_question_coverage = [];
    invalid.review.revision_round = 3;
    const result = validateAnswerEvidence(invalid, candidate(content), context(), QUALITY);
    assert.ok(result.hard_failures.includes('missing_evidence'));
    assert.ok(result.hard_failures.includes('unsupported_factual_claim'));
    assert.ok(result.hard_failures.includes('uncovered_source_variant'));
    assert.ok(result.errors.some((row) => row.error === 'invalid_revision_round'));
});

test('semantic gates detect legacy templates generic followups and cross-topic core answers', () => {
    const content = [
        '## 核心结论', 'MySQL B+ 树的叶子节点保存整行或主键。',
        '## 常见追问', '- 问：这道题最先要澄清什么？答：看情况。', '- 问：方案的主要代价是什么？答：看情况。', '- 问：如何验证回答不是背诵？答：做实验。',
        '## 关键细节', '先界定题目中的概念、版本和约束。',
    ].join('\n');
    const result = validateSpecializedCandidate(candidate(content), evidence(content), context());
    assert.ok(result.hard_failures.includes('generic_followups'));
    assert.ok(result.hard_failures.includes('template_only_answer'));
    assert.ok(result.hard_failures.includes('cross_topic_contamination'));
});

test('project claims require real evidence and reject unfilled placeholders', () => {
    const content = '## 核心结论\n项目复盘\n## 常见追问\n- 问：约束？答：成本。\n- 问：取舍？答：一致性。\n- 问：复盘？答：演练。\n## 项目经验版\n我主导上线并将延迟降低 40%，公司是[公司名称]。';
    const result = validateSpecializedCandidate(candidate(content, 'project'), evidence(content), { ...context(), primary_entities: ['项目复盘'] });
    assert.ok(result.hard_failures.includes('fabricated_experience'));
    assert.ok(result.hard_failures.includes('placeholder_implementation'));
});

