'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
    decideReviewedCanonicalConsolidation,
} = require('../src/domain/canonical/reviewed-consolidation-policy');
const {
    createResolveReviewedCanonicalConsolidationUseCase,
} = require('../src/application/canonical/resolve-reviewed-canonical-consolidation');

function intent(overrides = {}) {
    return {
        schema_version: 'dedup_relation_apply_intent.v1',
        relation_candidate_key: 'pair|q_a,q_b|q_a,q_b',
        relation: 'same',
        intent_kind: 'canonicalize_question_group',
        intent_state: 'ready',
        apply_required: true,
        required_inputs: ['canonical_id', 'canonical_title'],
        question_ids: ['q_a', 'q_b'],
        canonical_target: {
            canonical_id: 'cq_target',
            canonical_title: 'Target',
        },
        decision_provenance: {
            actor: { type: 'ai', id: 'review-agent' },
            source_revisions: [{ resource: 'dedup-questions', revision: 'r1' }],
        },
        ...overrides,
    };
}

function owner(questionId, canonicalIds) {
    return { question_id: questionId, canonical_ids: canonicalIds };
}

test('policy keeps ordinary question-group path when no reviewed Question has another owner', () => {
    const result = decideReviewedCanonicalConsolidation({
        intent: intent(),
        target_record: null,
        question_owners: [owner('q_a', []), owner('q_b', [])],
        source_records: {},
    });

    assert.equal(result.strategy, 'question_group');
    assert.equal(result.target_canonical_id, 'cq_target');
    assert.deepEqual(result.reviewed_question_ids, ['q_a', 'q_b']);
});

test('policy permits existing Canonical merge only when the source membership is fully reviewed', () => {
    const result = decideReviewedCanonicalConsolidation({
        intent: intent(),
        target_record: { canonical_id: 'cq_target', question_ids: ['q_a'] },
        question_owners: [owner('q_a', ['cq_target']), owner('q_b', ['cq_source'])],
        source_records: {
            cq_source: { canonical_id: 'cq_source', question_ids: ['q_b'] },
        },
    });

    assert.equal(result.strategy, 'merge_existing_canonical');
    assert.equal(result.target_canonical_id, 'cq_target');
    assert.equal(result.source_canonical_id, 'cq_source');
    assert.deepEqual(result.source_question_ids, ['q_b']);
});

test('policy fails closed when Canonical merge would move an unreviewed source Question', () => {
    assert.throws(
        () => decideReviewedCanonicalConsolidation({
            intent: intent(),
            target_record: { canonical_id: 'cq_target', question_ids: ['q_a'] },
            question_owners: [owner('q_a', ['cq_target']), owner('q_b', ['cq_source'])],
            source_records: {
                cq_source: { canonical_id: 'cq_source', question_ids: ['q_b', 'q_unreviewed'] },
            },
        }),
        /would move unreviewed Questions.*q_unreviewed/,
    );
});

test('policy rejects ambiguous ownership and multiple external Canonicals', () => {
    assert.throws(
        () => decideReviewedCanonicalConsolidation({
            intent: intent(),
            target_record: { canonical_id: 'cq_target', question_ids: ['q_a'] },
            question_owners: [owner('q_a', ['cq_target', 'cq_other']), owner('q_b', ['cq_source'])],
            source_records: {},
        }),
        /belongs to multiple Canonicals/,
    );

    assert.throws(
        () => decideReviewedCanonicalConsolidation({
            intent: intent({ question_ids: ['q_a', 'q_b', 'q_c'] }),
            target_record: { canonical_id: 'cq_target', question_ids: ['q_a'] },
            question_owners: [
                owner('q_a', ['cq_target']),
                owner('q_b', ['cq_source']),
                owner('q_c', ['cq_other']),
            ],
            source_records: {},
        }),
        /spans multiple non-target Canonicals/,
    );
});

test('Application resolver reads ownership and Canonical facts behind Ports', async () => {
    const calls = [];
    const canonicalRepository = {
        async get(canonicalId) {
            calls.push(['canonical', canonicalId]);
            const records = {
                cq_target: { canonical_id: 'cq_target', question_ids: ['q_a'] },
                cq_source: { canonical_id: 'cq_source', question_ids: ['q_b'] },
            };
            const record = records[canonicalId];
            return record
                ? { record, resource: `canonical:${canonicalId}`, revision: `rev-${canonicalId}` }
                : null;
        },
    };
    const canonicalQuestionOwnershipRepository = {
        async findOwners(questionId) {
            calls.push(['owners', questionId]);
            return {
                canonical_ids: questionId === 'q_a' ? ['cq_target'] : ['cq_source'],
                resource: `owners:${questionId}`,
                revision: `rev-${questionId}`,
            };
        },
    };
    const resolve = createResolveReviewedCanonicalConsolidationUseCase({
        canonicalRepository,
        canonicalQuestionOwnershipRepository,
    });

    const result = await resolve({ intent: intent() });
    assert.equal(result.strategy, 'merge_existing_canonical');
    assert.equal(result.source_canonical_id, 'cq_source');
    assert.deepEqual(calls, [
        ['owners', 'q_a'],
        ['owners', 'q_b'],
        ['canonical', 'cq_target'],
        ['canonical', 'cq_source'],
    ]);
});

test('Application resolver requires an existing target before consolidating another Canonical', async () => {
    const resolve = createResolveReviewedCanonicalConsolidationUseCase({
        canonicalRepository: {
            async get(canonicalId) {
                if (canonicalId === 'cq_source') {
                    return {
                        record: { canonical_id: 'cq_source', question_ids: ['q_b'] },
                        resource: 'canonical:cq_source',
                        revision: 'r-source',
                    };
                }
                return null;
            },
        },
        canonicalQuestionOwnershipRepository: {
            async findOwners(questionId) {
                return {
                    canonical_ids: questionId === 'q_b' ? ['cq_source'] : [],
                    resource: `owners:${questionId}`,
                    revision: `r-${questionId}`,
                };
            },
        },
    });

    await assert.rejects(
        resolve({ intent: intent() }),
        /requires existing target cq_target/,
    );
});
