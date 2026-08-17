'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createCanonicalStatsUseCase } = require('../src/application/canonical/canonical-stats');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: `title ${id}`,
        frequency: 1,
        question_ids: [`q_${id}`],
        companies: ['美团'],
        primary_entities: ['Redis'],
        review_priority: 'P2',
        answer_status: 'missing',
        ...overrides,
    };
}

function catalog(records) {
    return {
        list() {
            return structuredClone(records);
        },
    };
}

test('CanonicalStats preserves canonical_stats.v1 cross-catalog aggregation and top ordering', () => {
    const stats = createCanonicalStatsUseCase({
        canonicalCatalogRepository: catalog([
            canonical('cq_b', { frequency: 5, question_ids: ['q1', 'q2'] }),
            canonical('cq_a', { frequency: 5, question_ids: ['q2', 'q3'] }),
            canonical('cq_c', { frequency: 2, question_ids: [] }),
        ]),
        questionCatalogRepository: catalog([
            { question_id: 'q1', canonical_id: 'cq_b' },
            { question_id: 'q2', canonical_id: 'cq_a' },
            { question_id: 'q3', canonical_id: null },
            { question_id: 'q4', canonical_id: 'cq_unknown' },
        ]),
    });

    const result = stats({ limit: '2' });

    assert.deepEqual(result, {
        schema_version: 'canonical_stats.v1',
        canonical_count: 3,
        canonical_question_id_count: 3,
        assigned_question_rows: 3,
        top_canonical: [
            {
                canonical_id: 'cq_a',
                canonical_title: 'title cq_a',
                frequency: 5,
                companies: ['美团'],
                primary_entities: ['Redis'],
            },
            {
                canonical_id: 'cq_b',
                canonical_title: 'title cq_b',
                frequency: 5,
                companies: ['美团'],
                primary_entities: ['Redis'],
            },
        ],
    });
});

test('CanonicalStats keeps the legacy default top limit of 20', () => {
    const canonicals = Array.from({ length: 23 }, (_, index) => canonical(
        `cq_${String(index).padStart(2, '0')}`,
        { frequency: 23 - index },
    ));
    const stats = createCanonicalStatsUseCase({
        canonicalCatalogRepository: catalog(canonicals),
        questionCatalogRepository: catalog([]),
    });

    const result = stats();

    assert.equal(result.canonical_count, 23);
    assert.equal(result.top_canonical.length, 20);
});

test('CanonicalStats requires only the two catalog list capabilities', () => {
    assert.throws(
        () => createCanonicalStatsUseCase({
            canonicalCatalogRepository: {},
            questionCatalogRepository: catalog([]),
        }),
        /CanonicalCatalogRepository\.list\(\) is required/,
    );
    assert.throws(
        () => createCanonicalStatsUseCase({
            canonicalCatalogRepository: catalog([]),
            questionCatalogRepository: {},
        }),
        /QuestionCatalogRepository\.list\(\) is required/,
    );
});
