'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    createApplyRelationDecisionUseCase,
} = require('../src/application/dedup/apply-relation-decision');

function canonicalIntent(overrides = {}) {
    return {
        schema_version: 'dedup_relation_apply_intent.v1',
        relation_candidate_key: 'entity|Redis|q_a,q_b',
        relation: 'same',
        intent_kind: 'canonicalize_question_group',
        intent_state: 'ready',
        apply_required: true,
        required_inputs: ['canonical_id', 'canonical_title'],
        question_ids: ['q_a', 'q_b'],
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        },
        decision_provenance: {
            actor: { type: 'human', id: 'reviewer-1' },
            decided_at: '2026-08-13T17:50:00+08:00',
            source_revisions: [{ resource: 'dedup-index:Redis', revision: 'source-rev' }],
        },
        ...overrides,
    };
}

function prepared(overrides = {}) {
    return {
        ok: true,
        relation_candidate_key: 'entity|Redis|q_a,q_b',
        relation: 'same',
        intent: canonicalIntent(),
        decision_snapshot: {
            resource: 'dedup-relation-decision:entity|Redis|q_a,q_b',
            revision: 'decision-rev',
        },
        current_source_revisions: [
            { resource: 'dedup-index:Redis', revision: 'source-rev' },
            { resource: 'dedup-questions:Redis', revision: 'questions-rev' },
        ],
        ...overrides,
    };
}

function createHarness(overrides = {}) {
    const calls = [];
    const prepareRelationApply = overrides.prepareRelationApply || (async (input) => {
        calls.push(['prepare', structuredClone(input)]);
        return prepared();
    });
    const resolveQuestionGroupCanonicalization = overrides.resolveQuestionGroupCanonicalization || (async (input) => {
        calls.push(['resolve', structuredClone(input)]);
        return {
            ok: true,
            canonical_id: 'cq_redis_performance',
            resolution: 'absent',
            plan: {
                schema_version: 'canonicalization_plan.v1',
                relation_candidate_key: 'entity|Redis|q_a,q_b',
            },
        };
    });
    const executeQuestionGroupCanonicalization = overrides.executeQuestionGroupCanonicalization || (async (input) => {
        calls.push(['execute', structuredClone(input)]);
        return {
            ok: true,
            canonical_id: 'cq_redis_performance',
            question_ids: ['q_a', 'q_b'],
            updated_question_rows: 2,
            canonical_count: 1,
            commit: {
                committed: true,
                operation: 'canonicalize',
            },
        };
    });
    return {
        calls,
        apply: createApplyRelationDecisionUseCase({
            prepareRelationApply,
            resolveQuestionGroupCanonicalization,
            executeQuestionGroupCanonicalization,
        }),
    };
}

test('orchestrator revalidates Decision first, then resolves and executes Canonicalization without exposing intermediates', async () => {
    const harness = createHarness();

    const result = await harness.apply({
        relation_candidate_key: 'entity|Redis|q_a,q_b',
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 为什么快？',
    });

    assert.deepEqual(harness.calls.map(([name]) => name), ['prepare', 'resolve', 'execute']);
    assert.deepEqual(harness.calls[0][1], {
        relation_candidate_key: 'entity|Redis|q_a,q_b',
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 为什么快？',
    });
    assert.equal(harness.calls[1][1].intent.intent_state, 'ready');
    assert.equal(harness.calls[2][1].plan.schema_version, 'canonicalization_plan.v1');

    assert.equal(result.ok, true);
    assert.equal(result.applied, true);
    assert.equal(result.canonical_id, 'cq_redis_performance');
    assert.equal(result.canonical_resolution, 'absent');
    assert.deepEqual(result.question_ids, ['q_a', 'q_b']);
    assert.equal(result.commit.operation, 'canonicalize');
    for (const hidden of ['intent', 'canonicalization_plan', 'mutation_plan', 'plan']) {
        assert.equal(Object.hasOwn(result, hidden), false);
    }
});

test('stale Dedup source rejection stops before any Canonical resolution or mutation', async () => {
    let resolved = false;
    let executed = false;
    const harness = createHarness({
        prepareRelationApply: async () => {
            throw new Error('Dedup relation source changed: expected source-rev, got newer-rev');
        },
        resolveQuestionGroupCanonicalization: async () => {
            resolved = true;
        },
        executeQuestionGroupCanonicalization: async () => {
            executed = true;
        },
    });

    await assert.rejects(
        harness.apply({
            relation_candidate_key: 'entity|Redis|q_a,q_b',
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        }),
        /Dedup relation source changed/,
    );
    assert.equal(resolved, false);
    assert.equal(executed, false);
});

test('relation-record-only and unrelated Decisions return explicit no-op without crossing into Canonical', async () => {
    for (const [relation, intentKind, reasonCode] of [
        ['parent_child', 'relation_record_only', 'relation_graph_apply_not_supported'],
        ['followup', 'relation_record_only', 'relation_graph_apply_not_supported'],
        ['related', 'relation_record_only', 'relation_graph_apply_not_supported'],
        ['unrelated', 'no_apply', 'explicitly_unrelated'],
    ]) {
        let resolved = false;
        let executed = false;
        const harness = createHarness({
            prepareRelationApply: async () => prepared({
                relation,
                intent: canonicalIntent({
                    relation,
                    intent_kind: intentKind,
                    intent_state: 'complete',
                    apply_required: false,
                    required_inputs: [],
                    reason_code: reasonCode,
                    canonical_target: undefined,
                }),
            }),
            resolveQuestionGroupCanonicalization: async () => {
                resolved = true;
            },
            executeQuestionGroupCanonicalization: async () => {
                executed = true;
            },
        });

        const result = await harness.apply({
            relation_candidate_key: 'entity|Redis|q_a,q_b',
        });
        assert.equal(result.applied, false);
        assert.equal(result.relation, relation);
        assert.equal(result.reason_code, reasonCode);
        assert.equal(resolved, false);
        assert.equal(executed, false);
    }
});

test('same or alias Decision without required Canonical target refuses execution', async () => {
    let executed = false;
    const harness = createHarness({
        prepareRelationApply: async () => prepared({
            intent: canonicalIntent({
                intent_state: 'requires_input',
                canonical_target: undefined,
            }),
        }),
        executeQuestionGroupCanonicalization: async () => {
            executed = true;
        },
    });

    await assert.rejects(
        harness.apply({ relation_candidate_key: 'entity|Redis|q_a,q_b' }),
        /Relation apply intent is not ready: requires_input/,
    );
    assert.equal(executed, false);
});

test('caller cannot inject Decision, freshness, planning, mutation, or commit evidence', async () => {
    const harness = createHarness();
    for (const forged of [
        { decision: {} },
        { source_revisions: [] },
        { expected_revisions: [] },
        { intent: {} },
        { canonicalization_plan: {} },
        { mutation_plan: {} },
        { preflight: {} },
        { commit: {} },
    ]) {
        await assert.rejects(
            harness.apply({
                relation_candidate_key: 'entity|Redis|q_a,q_b',
                canonical_id: 'cq_redis_performance',
                canonical_title: 'Redis 为什么快？',
                ...forged,
            }),
            /Relation decision apply state is controlled by Application/,
        );
    }
    assert.deepEqual(harness.calls, []);
});
