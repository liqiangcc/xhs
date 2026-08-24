'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    decideReviewedCanonicalConsolidation,
} = require('../src/domain/canonical/reviewed-consolidation-policy');
const {
    createMergeCanonicalUseCase,
} = require('../src/application/canonical/merge-canonical');
const {
    createApplyRelationDecisionUseCase,
} = require('../src/application/dedup/apply-relation-decision');

function intent() {
    return {
        schema_version: 'dedup_relation_apply_intent.v1',
        relation_candidate_key: 'pair|q_target,q_source',
        relation: 'same',
        intent_kind: 'canonicalize_question_group',
        intent_state: 'ready',
        apply_required: true,
        question_ids: ['q_target', 'q_source'],
        canonical_target: {
            canonical_id: 'cq_target',
            canonical_title: 'Target',
        },
    };
}

function reviewedPolicyInput(overrides = {}) {
    return {
        intent: intent(),
        target_record: {
            canonical_id: 'cq_target',
            question_ids: ['q_target'],
        },
        question_owners: [
            { question_id: 'q_target', canonical_ids: ['cq_target'] },
            { question_id: 'q_source', canonical_ids: ['cq_source'] },
        ],
        source_records: {
            cq_source: {
                canonical_id: 'cq_source',
                question_ids: ['q_source'],
            },
        },
        ...overrides,
    };
}

function snapshot(resource, valueKey, value) {
    return {
        [valueKey]: value,
        resource,
        revision: `rev:${resource}`,
    };
}

function createMergeHarness({ targetQuestionIds, sourceQuestionIds }) {
    let mutationCalled = false;
    const canonicalRepository = {
        async get(canonicalId) {
            if (canonicalId === 'cq_target') {
                return snapshot('canonical:cq_target', 'record', {
                    canonical_id: 'cq_target',
                    question_ids: [...targetQuestionIds],
                });
            }
            if (canonicalId === 'cq_source') {
                return snapshot('canonical:cq_source', 'record', {
                    canonical_id: 'cq_source',
                    question_ids: [...sourceQuestionIds],
                });
            }
            return null;
        },
    };
    const questionBindingRepository = {
        async findByCanonical(canonicalId) {
            return snapshot(`question-bindings:${canonicalId}`, 'bindings', []);
        },
        async findByQuestionId(questionId) {
            return snapshot(`question-bindings-by-question:${questionId}`, 'bindings', []);
        },
    };
    const reviewRepository = {
        async loadMergeState() {
            return {
                target_items: [],
                source_items: [],
                source_session_event_count: 0,
                resource: 'review-merge:cq_target:cq_source',
                revision: 'review-rev',
            };
        },
    };
    const answerRepository = {
        async loadMergeState() {
            return {
                target_answer: null,
                source_answer: null,
                source_archive_exists: false,
                resource: 'answer-merge:cq_target:cq_source',
                revision: 'answer-rev',
            };
        },
    };
    const mutationGateway = {
        async preflight() {
            mutationCalled = true;
            throw new Error('preflight should not run');
        },
        async commit() {
            mutationCalled = true;
            throw new Error('commit should not run');
        },
    };
    const integrityChecker = {
        async check() {
            throw new Error('integrity should not run');
        },
    };
    const merge = createMergeCanonicalUseCase({
        canonicalRepository,
        questionBindingRepository,
        reviewRepository,
        answerRepository,
        mutationGateway,
        integrityChecker,
        taxonomy: {},
    });
    return {
        merge,
        mutationCalled: () => mutationCalled,
    };
}

test('reviewed consolidation fails closed when an existing source is mixed with an unowned reviewed Question', () => {
    const input = reviewedPolicyInput({
        target_record: {
            canonical_id: 'cq_target',
            question_ids: [],
        },
        question_owners: [
            { question_id: 'q_target', canonical_ids: [] },
            { question_id: 'q_source', canonical_ids: ['cq_source'] },
        ],
    });

    assert.throws(
        () => decideReviewedCanonicalConsolidation(input),
        /cannot combine an unowned Question with an existing source Canonical: q_target/,
    );
});

test('reviewed consolidation rejects ownership and Canonical record read skew', () => {
    const input = reviewedPolicyInput({
        target_record: {
            canonical_id: 'cq_target',
            question_ids: [],
        },
    });

    assert.throws(
        () => decideReviewedCanonicalConsolidation(input),
        /ownership changed while resolving target cq_target: q_target/,
    );
});

test('Canonical merge rejects source membership growth beyond the reviewed scope before mutation', async () => {
    const harness = createMergeHarness({
        targetQuestionIds: ['q_target'],
        sourceQuestionIds: ['q_source', 'q_unreviewed'],
    });

    await assert.rejects(
        harness.merge({
            target: 'cq_target',
            source: 'cq_source',
            reason: 'reviewed same relation',
            expected_source_question_ids: ['q_source'],
            expected_target_reviewed_question_ids: ['q_target'],
        }),
        /Reviewed Canonical merge source scope changed/,
    );
    assert.equal(harness.mutationCalled(), false);
});

test('Canonical merge rejects loss of a reviewed target Question before mutation', async () => {
    const harness = createMergeHarness({
        targetQuestionIds: [],
        sourceQuestionIds: ['q_source'],
    });

    await assert.rejects(
        harness.merge({
            target: 'cq_target',
            source: 'cq_source',
            reason: 'reviewed same relation',
            expected_source_question_ids: ['q_source'],
            expected_target_reviewed_question_ids: ['q_target'],
        }),
        /Reviewed Canonical merge target scope changed/,
    );
    assert.equal(harness.mutationCalled(), false);
});

test('Dedup apply carries reviewed Canonical scope into the merge preconditions', async () => {
    let mergeInput = null;
    const apply = createApplyRelationDecisionUseCase({
        async prepareRelationApply() {
            return {
                ok: true,
                relation_candidate_key: 'pair|q_target,q_source',
                relation: 'same',
                intent: intent(),
                decision_snapshot: { resource: 'decision', revision: 'decision-rev' },
                current_source_revisions: [],
            };
        },
        async resolveReviewedCanonicalConsolidation() {
            return {
                schema_version: 'reviewed_canonical_apply_strategy.v1',
                strategy: 'merge_existing_canonical',
                relation_candidate_key: 'pair|q_target,q_source',
                relation: 'same',
                target_canonical_id: 'cq_target',
                source_canonical_id: 'cq_source',
                reviewed_question_ids: ['q_source', 'q_target'],
                target_reviewed_question_ids: ['q_target'],
                source_question_ids: ['q_source'],
            };
        },
        async mergeCanonical(inputValue) {
            mergeInput = structuredClone(inputValue);
            return {
                ok: true,
                moved_question_ids: ['q_source'],
                assigned_question_rows: 2,
                canonical_count: 1,
                review_migration: null,
                invalidated_target_answer: null,
                archived_source_answer: null,
                integrity: { schema_version: 'canonical_quality_report.v1', ok: true },
                commit: { committed: true, operation: 'merge' },
            };
        },
        async resolveQuestionGroupCanonicalization() {
            throw new Error('question-group resolution must not run');
        },
        async executeQuestionGroupCanonicalization() {
            throw new Error('question-group execution must not run');
        },
    });

    const result = await apply({
        relation_candidate_key: 'pair|q_target,q_source',
        canonical_id: 'cq_target',
        canonical_title: 'Target',
    });

    assert.equal(result.ok, true);
    assert.deepEqual(mergeInput.expected_source_question_ids, ['q_source']);
    assert.deepEqual(mergeInput.expected_target_reviewed_question_ids, ['q_target']);
});
