'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const { refreshCanonicalFromQuestions } = require('../src/domain/canonical/refresh-policy');

function canonical(overrides = {}) {
    return {
        canonical_id: 'cq_redis',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 单线程为什么快？', 'Redis 为什么快？'],
        question_ids: ['q2', 'q1'],
        primary_domain: { l1: '其他', l2: '其他' },
        primary_entities: ['legacy'],
        companies: ['旧公司'],
        frequency: 99,
        review_priority: 'P2',
        answer_status: 'needs_update',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(questionId, overrides = {}) {
    return {
        question_id: questionId,
        company: '美团',
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
        ...overrides,
    };
}

test('recomputes legacy canonical aggregate fields from every matching question row', () => {
    const record = canonical();
    const rows = [
        question('q1', { company: '美团', tech_entities: ['redis', 'Jedis'] }),
        question('q2', { company: '字节', tech_entities: ['Redis'] }),
        question('q2', { company: '美团', tech_entities: ['redis'] }),
        question('other', { company: '不应计入', domain: { l1: '数据库', l2: 'MySQL' } }),
    ];

    const refreshed = refreshCanonicalFromQuestions(record, rows, taxonomy);

    assert.equal(refreshed.frequency, 3);
    assert.deepEqual(refreshed.question_ids, ['q1', 'q2']);
    assert.deepEqual(refreshed.companies, ['字节', '美团'].sort((a, b) => a.localeCompare(b, 'zh')));
    assert.deepEqual(refreshed.primary_domain, { l1: '缓存', l2: 'Redis' });
    assert.equal(refreshed.primary_entities[0], 'Redis');
    assert.equal(refreshed.review_priority, 'P1');
    assert.equal(refreshed.answer_status, 'needs_update');
});

test('preserves a valid editorial domain override while refreshing derived fields', () => {
    const record = canonical({
        primary_domain_override: { l1: '中间件', l2: '搜索引擎(Elasticsearch等)' },
    });
    const refreshed = refreshCanonicalFromQuestions(record, [
        question('q1'),
        question('q2'),
    ], taxonomy);

    assert.deepEqual(refreshed.primary_domain, {
        l1: '中间件',
        l2: '搜索引擎(Elasticsearch等)',
    });
    assert.deepEqual(refreshed.primary_domain_override, record.primary_domain_override);
});

test('falls back to existing frequency and entities when no matching rows exist', () => {
    const record = canonical({ frequency: 7, primary_entities: ['Redis'] });
    const refreshed = refreshCanonicalFromQuestions(record, [], taxonomy);

    assert.equal(refreshed.frequency, 7);
    assert.deepEqual(refreshed.primary_entities, ['Redis']);
    assert.deepEqual(refreshed.companies, []);
});

test('does not mutate canonical records or question rows', () => {
    const record = canonical();
    const rows = [question('q1'), question('q2')];
    const beforeRecord = structuredClone(record);
    const beforeRows = structuredClone(rows);

    refreshCanonicalFromQuestions(record, rows, taxonomy);

    assert.deepEqual(record, beforeRecord);
    assert.deepEqual(rows, beforeRows);
});
