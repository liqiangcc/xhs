'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    decideReviewedCanonicalConsolidation,
} = require('../src/domain/canonical/reviewed-consolidation-policy');

function intent(overrides = {}) {
    return {
        schema_version: 'dedup_relation_apply_intent.v1',
        relation_candidate_key: 'pair|q_a,q_b',
        relation: 'same',
        intent_kind: 'canonicalize_question_group',
        intent_state: 'ready',
        apply_required: true,
        question_ids: ['q_a', 'q_b'],
        canonical_target: {
            canonical_id: 'cq_target',
            canonical_title: 'Target',
        },
        ...overrides,
    };
}

test('reviewed consolidation rejects an unrelated existing target with no reviewed member', () => {
    assert.throws(
        () => decideReviewedCanonicalConsolidation({
            intent: intent(),
            target_record: {
                canonical_id: 'cq_target',
                question_ids: ['q_unrelated'],
            },
            question_owners: [
                { question_id: 'q_a', canonical_ids: ['cq_source'] },
                { question_id: 'q_b', canonical_ids: ['cq_source'] },
            ],
            source_records: {
                cq_source: {
                    canonical_id: 'cq_source',
                    question_ids: ['q_a', 'q_b'],
                },
            },
        }),
        /target cq_target is not represented by any reviewed Question/,
    );
});

test('reviewed consolidation requires an apply-authorized intent', () => {
    assert.throws(
        () => decideReviewedCanonicalConsolidation({
            intent: intent({ apply_required: false }),
            target_record: null,
            question_owners: [
                { question_id: 'q_a', canonical_ids: [] },
                { question_id: 'q_b', canonical_ids: [] },
            ],
            source_records: {},
        }),
        /requires apply_required=true/,
    );
});
