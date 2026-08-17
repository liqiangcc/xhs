'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createCanonicalMutationPlan } = require('../src/application/canonical/mutation-plan');
const { assertCanonicalRepository } = require('../src/ports/repositories/canonical-repository');
const { assertCanonicalQuestionOwnershipRepository } = require('../src/ports/repositories/canonical-question-ownership-repository');
const { assertQuestionBindingRepository } = require('../src/ports/repositories/question-binding-repository');
const { assertCanonicalMutationGateway } = require('../src/ports/canonical-mutation-gateway');

test('Canonical read ports require only the narrow capabilities used by current application', () => {
    const canonicalRepository = { get() {} };
    const ownershipRepository = { findOwners() {} };
    const questionBindingRepository = { findByCanonical() {}, findByQuestionId() {} };

    assert.equal(assertCanonicalRepository(canonicalRepository), canonicalRepository);
    assert.equal(
        assertCanonicalQuestionOwnershipRepository(ownershipRepository),
        ownershipRepository,
    );
    assert.equal(assertQuestionBindingRepository(questionBindingRepository), questionBindingRepository);
    assert.throws(() => assertCanonicalRepository({}), /CanonicalRepository\.get\(\) is required/);
    assert.throws(
        () => assertCanonicalQuestionOwnershipRepository({}),
        /CanonicalQuestionOwnershipRepository\.findOwners\(\) is required/,
    );
    assert.throws(
        () => assertQuestionBindingRepository({ findByCanonical() {} }),
        /QuestionBindingRepository\.findByQuestionId\(\) is required/,
    );
});

test('CanonicalMutationGateway exposes one preflight/commit consistency boundary', () => {
    const gateway = { preflight() {}, commit() {} };
    assert.equal(assertCanonicalMutationGateway(gateway), gateway);
    assert.throws(() => assertCanonicalMutationGateway({ commit() {} }), /preflight\(\) is required/);
    assert.throws(() => assertCanonicalMutationGateway({ preflight() {} }), /commit\(\) is required/);
});

test('MutationPlan is storage agnostic, immutable, and carries opaque revisions', () => {
    const input = {
        operation: 'merge',
        expected_revisions: [
            { resource: 'canonicals', revision: 'opaque-canonical-revision' },
            { resource: 'question-bindings', revision: 'opaque-binding-revision' },
        ],
        changes: {
            canonical_upserts: [
                { canonical_id: 'cq_target', question_ids: ['q1', 'q2'], answer_status: 'needs_update' },
            ],
            canonical_removals: ['cq_source'],
            question_rebindings: [
                { question_id: 'q2', from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
            ],
            review_migrations: [
                { from_canonical_id: 'cq_source', to_canonical_id: 'cq_target' },
            ],
            answer_invalidations: [
                { canonical_id: 'cq_target', caused_by: 'cq_source' },
            ],
            answer_archives: [
                { canonical_id: 'cq_source', target_canonical_id: 'cq_target' },
            ],
            rebuild_indexes: true,
            history_entry: { type: 'canonical_merge', target: 'cq_target', source: 'cq_source' },
        },
    };

    const plan = createCanonicalMutationPlan(input);

    assert.equal(plan.schema_version, 'canonical_mutation_plan.v1');
    assert.equal(plan.operation, 'merge');
    assert.equal(plan.expected_revisions[0].revision, 'opaque-canonical-revision');
    assert.equal(plan.changes.canonical_upserts[0].canonical_id, 'cq_target');
    assert.equal(plan.changes.canonical_removals[0], 'cq_source');
    assert.equal(plan.changes.rebuild_indexes, true);
    assert.equal(Object.isFrozen(plan), true);
    assert.equal(Object.isFrozen(plan.changes), true);
    assert.equal(Object.isFrozen(plan.changes.canonical_upserts[0]), true);

    input.expected_revisions[0].revision = 'changed-after-plan-build';
    input.changes.canonical_upserts[0].answer_status = 'ready';
    assert.equal(plan.expected_revisions[0].revision, 'opaque-canonical-revision');
    assert.equal(plan.changes.canonical_upserts[0].answer_status, 'needs_update');

    const serialized = JSON.stringify(plan);
    assert.doesNotMatch(serialized, /questions\.jsonl|canonical_questions\.jsonl|review\/answers|filePath|temp file/i);
});

test('MutationPlan rejects the retired accept operation', () => {
    assert.throws(
        () => createCanonicalMutationPlan({
            operation: 'accept',
            changes: {
                canonical_upserts: [{ canonical_id: 'cq_target', question_ids: ['q1'] }],
                question_rebindings: [
                    { question_id: 'q1', from_canonical_id: null, to_canonical_id: 'cq_target' },
                ],
            },
        }),
        /Unsupported canonical mutation operation: accept/,
    );
});

test('MutationPlan rejects contradictory or ineffective semantic changes', () => {
    assert.throws(
        () => createCanonicalMutationPlan({
            operation: 'merge',
            changes: {
                canonical_upserts: [{ canonical_id: 'cq_same' }],
                canonical_removals: ['cq_same'],
            },
        }),
        /cannot be upserted and removed/,
    );

    assert.throws(
        () => createCanonicalMutationPlan({
            operation: 'split',
            changes: {
                question_rebindings: [
                    { question_id: 'q1', from_canonical_id: 'cq_a', to_canonical_id: 'cq_a' },
                ],
            },
        }),
        /must change canonical ownership/,
    );

    assert.throws(
        () => createCanonicalMutationPlan({
            operation: 'canonicalize',
            changes: {
                canonical_upserts: [{ canonical_id: 'cq_target' }],
                question_rebindings: [
                    { question_id: 'q1', to_canonical_id: 'cq_target' },
                ],
            },
        }),
        /from_canonical_id is required/,
    );

    assert.throws(
        () => createCanonicalMutationPlan({ operation: 'merge', changes: {} }),
        /must contain a canonical or question-binding change/,
    );

    assert.throws(
        () => createCanonicalMutationPlan({
            operation: 'merge',
            expected_revisions: [{ resource: 'canonicals' }],
            changes: { canonical_removals: ['cq_source'] },
        }),
        /revision is required/,
    );
});
