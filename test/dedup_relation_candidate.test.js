'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    RELATION_TYPES,
    createRelationCandidate,
} = require('../src/domain/dedup/relation-candidate');

function cluster(overrides = {}) {
    return {
        domain_key: '缓存/Redis',
        anchor_question_id: 'q_a',
        question_ids: ['q_b', 'q_a'],
        member_count: 2,
        distinct_source_count: 2,
        members: [
            { question_id: 'q_a', source_note_id: 'note-a', source_question_index: 0 },
            { question_id: 'q_b', source_note_id: 'note-b', source_question_index: 0 },
        ],
        evidence: [{
            signal: 'jaccard',
            left_question_id: 'q_a',
            right_question_id: 'q_b',
            score: 0.6,
            threshold: 0.38,
            matched: true,
        }],
        ...overrides,
    };
}

test('relation candidate is an immutable review object rather than a decision', () => {
    const source = cluster();
    const before = structuredClone(source);
    const candidate = createRelationCandidate({
        scope: 'entity',
        seed: 'Redis',
        cluster: source,
    });

    assert.equal(candidate.schema_version, 'dedup_relation_candidate.v1');
    assert.equal(candidate.review_state, 'pending');
    assert.equal(candidate.scope, 'entity');
    assert.equal(candidate.seed, 'Redis');
    assert.deepEqual(candidate.question_ids, ['q_a', 'q_b']);
    assert.deepEqual(candidate.allowed_relations, RELATION_TYPES);
    assert.equal(Object.isFrozen(candidate), true);
    assert.equal(Object.isFrozen(candidate.members), true);
    assert.equal(Object.isFrozen(candidate.evidence), true);
    assert.equal(Object.hasOwn(candidate, 'relation'), false);
    assert.equal(Object.hasOwn(candidate, 'canonical_id'), false);
    assert.equal(Object.hasOwn(candidate, 'mutation_plan'), false);
    assert.equal(Object.hasOwn(candidate, 'plan'), false);
    assert.deepEqual(source, before);
});

test('relation candidate keeps detection evidence but cannot silently manufacture it', () => {
    assert.throws(
        () => createRelationCandidate({ scope: 'entity', cluster: cluster({ evidence: [] }) }),
        /evidence is required/,
    );
    assert.throws(
        () => createRelationCandidate({ scope: 'entity', cluster: cluster({ members: [] }) }),
        /at least two detected members/,
    );
});

test('relation candidate requires the anchor to be part of the detected question set', () => {
    assert.throws(
        () => createRelationCandidate({
            scope: 'entity',
            cluster: cluster({ question_ids: ['q_b'] }),
        }),
        /anchor must belong to question_ids/,
    );
});
