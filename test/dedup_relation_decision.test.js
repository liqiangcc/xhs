'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    RELATION_TYPES,
    createRelationCandidate,
} = require('../src/domain/dedup/relation-candidate');
const {
    DECISION_ACTOR_TYPES,
    createRelationDecision,
} = require('../src/domain/dedup/relation-decision');

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

function candidate(overrides = {}) {
    return {
        ...createRelationCandidate({
            scope: 'entity',
            seed: 'Redis',
            cluster: cluster(),
        }),
        ...overrides,
    };
}

function sourceRevisions() {
    return [
        { resource: 'dedup-questions-by-refs:abc', revision: 'question-rev-1' },
        { resource: 'dedup-entity-index:Redis', revision: 'index-rev-1' },
    ];
}

test('relation decision is an immutable auditable fact rather than an Apply command', () => {
    const source = sourceRevisions();
    const relationCandidate = candidate();
    const decision = createRelationDecision({
        candidate: relationCandidate,
        relation: 'same',
        actor: { type: 'human', id: 'reviewer-1', display_name: 'Reviewer One' },
        rationale: 'Same Redis performance concept.',
        decided_at: '2026-08-13T10:00:00+08:00',
        source_revisions: source,
    });

    source[0].revision = 'mutated-after-decision';

    assert.equal(decision.schema_version, 'dedup_relation_decision.v1');
    assert.equal(decision.relation_candidate_key, 'entity|Redis|q_a,q_b');
    assert.equal(decision.relation, 'same');
    assert.equal(decision.decision_state, 'explicit');
    assert.deepEqual(decision.actor, {
        type: 'human',
        id: 'reviewer-1',
        display_name: 'Reviewer One',
    });
    assert.equal(decision.rationale, 'Same Redis performance concept.');
    assert.equal(decision.decided_at, '2026-08-13T10:00:00+08:00');
    assert.deepEqual(decision.source_revisions, [
        { resource: 'dedup-entity-index:Redis', revision: 'index-rev-1' },
        { resource: 'dedup-questions-by-refs:abc', revision: 'question-rev-1' },
    ]);
    assert.deepEqual(decision.candidate_snapshot.question_ids, ['q_a', 'q_b']);
    assert.deepEqual(decision.candidate_snapshot.evidence, relationCandidate.evidence);
    assert.equal(Object.isFrozen(decision), true);
    assert.equal(Object.isFrozen(decision.actor), true);
    assert.equal(Object.isFrozen(decision.source_revisions), true);
    assert.equal(Object.isFrozen(decision.candidate_snapshot), true);
    assert.equal(Object.isFrozen(decision.candidate_snapshot.evidence), true);

    for (const forbidden of [
        'canonical_id',
        'target_canonical_id',
        'mutation_plan',
        'plan',
        'commit',
        'command',
        'apply',
    ]) {
        assert.equal(Object.hasOwn(decision, forbidden), false);
    }
});

test('every relation type requires the same explicit review boundary', () => {
    for (const relation of RELATION_TYPES) {
        const decision = createRelationDecision({
            candidate: candidate(),
            relation,
            actor: { type: 'ai', id: 'review-agent-v1' },
            source_revisions: sourceRevisions(),
        });
        assert.equal(decision.relation, relation);
        assert.equal(decision.actor.type, 'ai');
        assert.equal(Object.hasOwn(decision, 'canonical_id'), false);
    }
    assert.deepEqual(DECISION_ACTOR_TYPES, ['human', 'ai']);
});

test('relation decision rejects implicit or invalid reviewer choices', () => {
    assert.throws(
        () => createRelationDecision({
            candidate: candidate(),
            relation: 'merge',
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: sourceRevisions(),
        }),
        /Unsupported dedup relation decision/,
    );

    assert.throws(
        () => createRelationDecision({
            candidate: candidate(),
            relation: 'same',
            actor: { type: 'system', id: 'auto-merge' },
            source_revisions: sourceRevisions(),
        }),
        /Unsupported dedup relation decision actor type/,
    );

    assert.throws(
        () => createRelationDecision({
            candidate: candidate(),
            relation: 'same',
            actor: { type: 'human', id: '' },
            source_revisions: sourceRevisions(),
        }),
        /actor id is required/,
    );
});

test('relation decision requires a pending candidate and the exact source revision set', () => {
    assert.throws(
        () => createRelationDecision({
            candidate: candidate({ review_state: 'decided' }),
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: sourceRevisions(),
        }),
        /must be pending/,
    );

    assert.throws(
        () => createRelationDecision({
            candidate: candidate(),
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: [],
        }),
        /source_revisions are required/,
    );

    assert.throws(
        () => createRelationDecision({
            candidate: candidate(),
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: [
                { resource: 'dedup-entity-index:Redis', revision: 'rev-1' },
                { resource: 'dedup-entity-index:Redis', revision: 'rev-2' },
            ],
        }),
        /Duplicate dedup relation decision source revision/,
    );
});

test('relation decision respects the candidate-specific allowed relation set', () => {
    assert.throws(
        () => createRelationDecision({
            candidate: candidate({ allowed_relations: ['related', 'unrelated'] }),
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: sourceRevisions(),
        }),
        /is not allowed/,
    );
});
