'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { RELATION_TYPES, createRelationCandidate } = require('../src/domain/dedup/relation-candidate');
const { createRelationDecision } = require('../src/domain/dedup/relation-decision');
const {
    RELATION_APPLY_POLICIES,
    classifyRelationApply,
    createRelationApplyIntent,
} = require('../src/domain/dedup/relation-apply-intent');

function cluster() {
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
    };
}

function decision(relation = 'same') {
    const candidate = createRelationCandidate({
        scope: 'entity',
        seed: 'Redis',
        cluster: cluster(),
    });
    return createRelationDecision({
        candidate,
        relation,
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: 'reviewed explicitly',
        decided_at: '2026-08-13T13:00:00+08:00',
        source_revisions: [
            { resource: 'dedup-entity-index:Redis', revision: 'index-rev-1' },
            { resource: 'dedup-questions-by-refs:abc', revision: 'question-rev-1' },
        ],
    });
}

test('relation apply policy covers every explicit relation type from the shared SSOT', () => {
    assert.deepEqual(Object.keys(RELATION_APPLY_POLICIES).sort(), [...RELATION_TYPES].sort());
    assert.equal(Object.isFrozen(RELATION_APPLY_POLICIES), true);
    for (const relation of RELATION_TYPES) {
        assert.equal(Object.isFrozen(RELATION_APPLY_POLICIES[relation]), true);
        assert.equal(classifyRelationApply(decision(relation)), RELATION_APPLY_POLICIES[relation]);
    }
});

test('same decision becomes a canonicalization intent that still requires explicit target input', () => {
    const sourceDecision = decision('same');
    const intent = createRelationApplyIntent(sourceDecision);

    assert.equal(intent.schema_version, 'dedup_relation_apply_intent.v1');
    assert.equal(intent.relation_candidate_key, 'entity|Redis|q_a,q_b');
    assert.equal(intent.relation, 'same');
    assert.equal(intent.intent_kind, 'canonicalize_question_group');
    assert.equal(intent.intent_state, 'requires_input');
    assert.equal(intent.apply_required, true);
    assert.deepEqual(intent.required_inputs, ['canonical_id', 'canonical_title']);
    assert.deepEqual(intent.question_ids, ['q_a', 'q_b']);
    assert.equal(Object.hasOwn(intent, 'canonical_target'), false);
    assert.deepEqual(intent.decision_provenance, {
        actor: { type: 'human', id: 'reviewer-1' },
        decided_at: '2026-08-13T13:00:00+08:00',
        source_revisions: sourceDecision.source_revisions,
    });

    for (const forbidden of [
        'candidate_id',
        'command',
        'mutation_plan',
        'plan',
        'commit',
        'merge',
        'accept',
    ]) {
        assert.equal(Object.hasOwn(intent, forbidden), false);
    }
});

test('same and alias can become ready intents without becoming Canonical commands', () => {
    for (const relation of ['same', 'alias']) {
        const target = {
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        };
        const intent = createRelationApplyIntent(decision(relation), {
            canonical_target: target,
        });

        target.canonical_title = 'mutated after intent';
        assert.equal(intent.relation, relation);
        assert.equal(intent.intent_kind, 'canonicalize_question_group');
        assert.equal(intent.intent_state, 'ready');
        assert.equal(intent.apply_required, true);
        assert.deepEqual(intent.canonical_target, {
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        });
        assert.equal(Object.isFrozen(intent), true);
        assert.equal(Object.isFrozen(intent.canonical_target), true);
        assert.equal(Object.isFrozen(intent.decision_provenance), true);
        assert.equal(Object.hasOwn(intent, 'operation'), false);
        assert.equal(Object.hasOwn(intent, 'mutation_plan'), false);
    }
});

test('relationship-only decisions cannot smuggle a Canonical target into Apply', () => {
    for (const relation of ['parent_child', 'followup', 'related']) {
        const intent = createRelationApplyIntent(decision(relation));
        assert.equal(intent.intent_kind, 'relation_record_only');
        assert.equal(intent.intent_state, 'complete');
        assert.equal(intent.apply_required, false);
        assert.equal(intent.reason_code, 'relation_graph_apply_not_supported');
        assert.deepEqual(intent.required_inputs, []);
        assert.equal(Object.hasOwn(intent, 'canonical_target'), false);

        assert.throws(
            () => createRelationApplyIntent(decision(relation), {
                canonical_target: {
                    canonical_id: 'cq_forbidden',
                    canonical_title: 'Forbidden target',
                },
            }),
            new RegExp(`Relation ${relation} cannot target Canonical apply`),
        );
    }
});

test('unrelated decision is an explicit no-op', () => {
    const intent = createRelationApplyIntent(decision('unrelated'));
    assert.equal(intent.intent_kind, 'no_apply');
    assert.equal(intent.intent_state, 'complete');
    assert.equal(intent.apply_required, false);
    assert.equal(intent.reason_code, 'explicitly_unrelated');
    assert.deepEqual(intent.required_inputs, []);
});

test('ready canonicalization intent requires a complete target DTO', () => {
    assert.throws(
        () => createRelationApplyIntent(decision('same'), { canonical_target: {} }),
        /canonical_id and canonical_title are required/,
    );
    assert.throws(
        () => createRelationApplyIntent(decision('alias'), {
            canonical_target: { canonical_id: 'cq_redis', canonical_title: '' },
        }),
        /canonical_id and canonical_title are required/,
    );
});

test('apply intent rejects forged or implicit relation decisions', () => {
    const valid = decision('same');

    assert.throws(
        () => createRelationApplyIntent({ ...valid, decision_state: 'suggested' }),
        /requires an explicit decision/,
    );
    assert.throws(
        () => createRelationApplyIntent({ ...valid, schema_version: 'other.v1' }),
        /requires dedup_relation_decision.v1/,
    );
    assert.throws(
        () => createRelationApplyIntent({
            ...valid,
            candidate_snapshot: {
                ...valid.candidate_snapshot,
                relation_candidate_key: 'entity|Redis|other',
            },
        }),
        /candidate key mismatch/,
    );
    assert.throws(
        () => createRelationApplyIntent({ ...valid, relation: 'merge' }),
        /Unsupported dedup relation apply intent/,
    );
});
