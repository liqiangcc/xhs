'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createListCanonicalsUseCase } = require('../src/application/canonical/list-canonicals');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: `title ${id}`,
        review_priority: 'P2',
        answer_status: 'missing',
        frequency: 1,
        question_ids: [`q_${id}`],
        companies: ['美团'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        aliases: [`alias ${id}`],
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function repository(records) {
    return {
        list() {
            return structuredClone(records);
        },
    };
}

test('ListCanonicals preserves canonical_list.v1 ordering and projection', async () => {
    const list = createListCanonicalsUseCase({
        catalogRepository: repository([
            canonical('cq_p1_low', { review_priority: 'P1', frequency: 1 }),
            canonical('cq_p0_low', { review_priority: 'P0', frequency: 2 }),
            canonical('cq_p0_high_b', { review_priority: 'P0', frequency: 5 }),
            canonical('cq_p0_high_a', { review_priority: 'P0', frequency: 5 }),
            canonical('cq_unknown', { review_priority: 'PX', frequency: 99 }),
        ]),
    });

    const result = await list();

    assert.equal(result.schema_version, 'canonical_list.v1');
    assert.equal(result.total_count, 5);
    assert.equal(result.returned_count, 5);
    assert.deepEqual(
        result.records.map((record) => record.canonical_id),
        ['cq_p0_high_a', 'cq_p0_high_b', 'cq_p0_low', 'cq_p1_low', 'cq_unknown'],
    );
    assert.deepEqual(Object.keys(result.records[0]), [
        'canonical_id',
        'canonical_title',
        'review_priority',
        'answer_status',
        'frequency',
        'question_ids',
        'companies',
        'primary_domain',
        'primary_entities',
    ]);
    assert.equal('aliases' in result.records[0], false);
    assert.equal('schema_version' in result.records[0], false);
});

test('ListCanonicals applies exact filters before limit and preserves total_count semantics', async () => {
    const list = createListCanonicalsUseCase({
        catalogRepository: repository([
            canonical('cq_a', { review_priority: 'P0', answer_status: 'missing', frequency: 3 }),
            canonical('cq_b', { review_priority: 'P0', answer_status: 'missing', frequency: 2 }),
            canonical('cq_c', { review_priority: 'P0', answer_status: 'ready', frequency: 5 }),
            canonical('cq_d', { review_priority: 'P1', answer_status: 'missing', frequency: 9 }),
        ]),
    });

    const result = await list({ priority: 'P0', answer_status: 'missing', limit: '1' });

    assert.equal(result.total_count, 2);
    assert.equal(result.returned_count, 1);
    assert.deepEqual(result.records.map((record) => record.canonical_id), ['cq_a']);
});

test('ListCanonicals keeps the legacy default limit of 50', async () => {
    const records = Array.from({ length: 55 }, (_, index) => canonical(
        `cq_${String(index).padStart(2, '0')}`,
        { review_priority: 'P2', frequency: 1 },
    ));
    const list = createListCanonicalsUseCase({ catalogRepository: repository(records) });

    const result = await list();

    assert.equal(result.total_count, 55);
    assert.equal(result.returned_count, 50);
    assert.equal(result.records.length, 50);
});

test('ListCanonicals requires only the catalog list capability', () => {
    assert.throws(
        () => createListCanonicalsUseCase({ catalogRepository: {} }),
        /CanonicalCatalogRepository\.list\(\) is required/,
    );
});
