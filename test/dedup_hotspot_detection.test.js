'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    detectHotspotQuestionClusters,
} = require('../src/domain/dedup/hotspot-cluster-detection');

function question(overrides = {}) {
    return {
        question_id: 'q_hot',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        is_valid_for_library: true,
        canonical_id: null,
        ...overrides,
    };
}

function ref(item) {
    return {
        question_id: item.question_id,
        source_note_id: item.source_note_id,
        source_question_index: item.source_question_index,
    };
}

test('hotspot detection preserves legacy repeated-row eligibility and emits evidence only', () => {
    const rows = [
        question(),
        question({ source_note_id: 'note-b', company: '字节' }),
    ];
    const hotspots = [{
        canonical_id: null,
        question_id: 'q_hot',
        frequency: 2,
        companies: ['美团', '字节'],
        refs: rows.map(ref),
    }];
    const beforeRows = structuredClone(rows);
    const beforeHotspots = structuredClone(hotspots);

    const clusters = detectHotspotQuestionClusters(hotspots, rows);

    assert.equal(clusters.length, 1);
    assert.equal(clusters[0].anchor_question_id, 'q_hot');
    assert.deepEqual(clusters[0].question_ids, ['q_hot']);
    assert.equal(clusters[0].member_count, 2);
    assert.equal(clusters[0].distinct_source_count, 2);
    assert.deepEqual(clusters[0].evidence, [{
        signal: 'hotspot_question_id',
        question_id: 'q_hot',
        eligible_member_count: 2,
        indexed_frequency: 2,
        matched: true,
    }]);
    for (const forbidden of ['candidate_id', 'canonical_id', 'relation', 'mutation_plan']) {
        assert.equal(Object.hasOwn(clusters[0], forbidden), false);
    }
    assert.deepEqual(rows, beforeRows);
    assert.deepEqual(hotspots, beforeHotspots);
});

test('hotspot detection keeps historical same-source duplicates eligible', () => {
    const rows = [
        question({ source_note_id: 'note-a', source_question_index: 0 }),
        question({ source_note_id: 'note-a', source_question_index: 1 }),
    ];
    const clusters = detectHotspotQuestionClusters([{
        canonical_id: null,
        question_id: 'q_hot',
        frequency: 2,
        refs: rows.map(ref),
    }], rows);

    assert.equal(clusters.length, 1);
    assert.equal(clusters[0].member_count, 2);
    assert.equal(clusters[0].distinct_source_count, 1);
});

test('hotspot detection drops assigned, invalid, canonicalized, or sub-threshold groups', () => {
    const rows = [
        question({ question_id: 'q_assigned', canonical_id: 'cq_existing' }),
        question({ question_id: 'q_assigned', source_note_id: 'note-b', canonical_id: 'cq_existing' }),
        question({ question_id: 'q_invalid', is_valid_for_library: false }),
        question({ question_id: 'q_invalid', source_note_id: 'note-c', is_valid_for_library: false }),
        question({ question_id: 'q_single' }),
    ];
    const hotspots = [
        { canonical_id: null, question_id: 'q_assigned', frequency: 2, refs: rows.slice(0, 2).map(ref) },
        { canonical_id: null, question_id: 'q_invalid', frequency: 2, refs: rows.slice(2, 4).map(ref) },
        { canonical_id: null, question_id: 'q_single', frequency: 2, refs: [ref(rows[4])] },
        { canonical_id: 'cq_existing', question_id: 'q_canonical', frequency: 3, refs: [] },
    ];

    assert.deepEqual(detectHotspotQuestionClusters(hotspots, rows), []);
});

test('hotspot detection preserves legacy ordering by eligible frequency, company spread, then question id', () => {
    const rows = [
        question({ question_id: 'q_b', source_note_id: 'b1', company: '美团' }),
        question({ question_id: 'q_b', source_note_id: 'b2', company: '美团' }),
        question({ question_id: 'q_a', source_note_id: 'a1', company: '美团' }),
        question({ question_id: 'q_a', source_note_id: 'a2', company: '字节' }),
        question({ question_id: 'q_c', source_note_id: 'c1', company: '美团' }),
        question({ question_id: 'q_c', source_note_id: 'c2', company: '字节' }),
        question({ question_id: 'q_c', source_note_id: 'c3', company: '阿里' }),
    ];
    const byId = (id) => rows.filter((row) => row.question_id === id).map(ref);
    const hotspots = [
        { canonical_id: null, question_id: 'q_b', frequency: 2, refs: byId('q_b') },
        { canonical_id: null, question_id: 'q_a', frequency: 2, refs: byId('q_a') },
        { canonical_id: null, question_id: 'q_c', frequency: 3, refs: byId('q_c') },
    ];

    assert.deepEqual(
        detectHotspotQuestionClusters(hotspots, rows).map((cluster) => cluster.anchor_question_id),
        ['q_c', 'q_a', 'q_b'],
    );
});
