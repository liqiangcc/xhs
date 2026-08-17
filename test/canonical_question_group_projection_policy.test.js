'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    projectCanonicalQuestionGroup,
} = require('../src/domain/canonical/question-group-projection-policy');

const TAXONOMY = Object.freeze({
    domain_l1: ['缓存', '数据库', '其他'],
    domain_l2_by_l1: {
        缓存: ['Redis', '其他'],
        数据库: ['MySQL', '其他'],
        其他: ['其他'],
    },
    entity_synonyms: {
        redis: 'Redis',
        'redis缓存': 'Redis',
    },
});

function plan(overrides = {}) {
    return {
        schema_version: 'canonicalization_plan.v1',
        plan_state: 'resolved',
        plan_kind: 'create_canonical',
        relation_candidate_key: 'entity|Redis|q_a,q_b',
        relation: 'same',
        question_ids: ['q_a', 'q_b'],
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'absent',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 为什么快？',
            title_resolution: 'use_requested',
        },
        target_identity: {
            resource: 'canonical:cq_redis_performance',
            revision: 'canonical-rev-absent',
        },
        decision_provenance: {
            actor: { type: 'human', id: 'reviewer-1' },
            source_revisions: [{ resource: 'source', revision: 'source-rev' }],
        },
        mutation_authorized: false,
        ...overrides,
    };
}

function snapshot(record = null, revision = 'canonical-rev-absent') {
    return {
        record,
        resource: 'canonical:cq_redis_performance',
        revision,
    };
}

function question(overrides = {}) {
    return {
        question_id: 'q_a',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
        ...overrides,
    };
}

function existingCanonical(overrides = {}) {
    return {
        canonical_id: 'cq_redis_performance',
        canonical_title: 'Redis 性能原理',
        aliases: ['Redis 性能为什么高？'],
        question_ids: ['q_existing'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['阿里'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: 'curated',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

test('create projection builds a Canonical record from Question rows through existing Canonical SSOT policies', () => {
    const rows = [
        question(),
        question({
            question_id: 'q_b',
            source_note_id: 'note-b',
            original_question: 'Redis 为什么这么快？',
            company: '字节',
            tech_entities: ['Redis缓存'],
        }),
        question({
            question_id: 'q_b',
            source_note_id: 'note-c',
            source_question_index: 1,
            original_question: 'Redis 高性能的原因是什么？',
            company: '美团',
            tech_entities: ['Redis'],
        }),
    ];

    const record = projectCanonicalQuestionGroup({
        plan: plan(),
        canonical_snapshot: snapshot(),
        question_rows: rows,
        taxonomy: TAXONOMY,
    });

    assert.equal(record.canonical_id, 'cq_redis_performance');
    assert.equal(record.canonical_title, 'Redis 为什么快？');
    assert.deepEqual(record.question_ids, ['q_a', 'q_b']);
    assert.deepEqual(record.aliases, [
        'Redis 为什么快？',
        'Redis 为什么这么快？',
        'Redis 高性能的原因是什么？',
    ].sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh')));
    assert.deepEqual(record.primary_domain, { l1: '缓存', l2: 'Redis' });
    assert.deepEqual(record.primary_entities, ['Redis']);
    assert.deepEqual(record.companies, ['美团', '字节'].sort((a, b) => a.localeCompare(b, 'zh')));
    assert.equal(record.frequency, 3);
    assert.equal(record.review_priority, 'P1');
    assert.equal(record.answer_status, 'missing');
    assert.equal(record.schema_version, 'canonical_question.v1');

    for (const forbidden of ['candidate_id', 'operation', 'mutation_plan', 'plan', 'commit']) {
        assert.equal(Object.hasOwn(record, forbidden), false);
    }
});

test('extend projection refreshes from the full resulting Question set while preserving authoritative Canonical state', () => {
    const existing = existingCanonical();
    const extendPlan = plan({
        plan_kind: 'extend_existing_canonical',
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'existing',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 性能原理',
            title_resolution: 'preserve_existing',
        },
        target_identity: {
            resource: 'canonical:cq_redis_performance',
            revision: 'canonical-rev-existing',
        },
    });
    const rows = [
        question({
            question_id: 'q_existing',
            source_note_id: 'note-existing',
            original_question: 'Redis 底层性能原理是什么？',
            company: '阿里',
        }),
        question(),
        question({
            question_id: 'q_b',
            source_note_id: 'note-b',
            original_question: 'Redis 为什么这么快？',
            company: '字节',
        }),
    ];

    const record = projectCanonicalQuestionGroup({
        plan: extendPlan,
        canonical_snapshot: snapshot(existing, 'canonical-rev-existing'),
        question_rows: rows,
        taxonomy: TAXONOMY,
    });

    assert.equal(record.canonical_title, 'Redis 性能原理');
    assert.equal(record.answer_status, 'curated');
    assert.equal(record.review_priority, 'P0');
    assert.deepEqual(record.question_ids, ['q_a', 'q_b', 'q_existing']);
    assert.deepEqual(record.companies, ['阿里', '美团', '字节'].sort((a, b) => a.localeCompare(b, 'zh')));
    assert.equal(record.frequency, 3);
    assert.ok(record.aliases.includes('Redis 性能为什么高？'));
    assert.ok(record.aliases.includes('Redis 为什么快？'));
    assert.ok(record.aliases.includes('Redis 为什么这么快？'));
    assert.equal(record.aliases.includes('Redis 底层性能原理是什么？'), false);
});

test('extend projection requires current rows for existing and planned Canonical membership', () => {
    const existing = existingCanonical();
    const extendPlan = plan({
        plan_kind: 'extend_existing_canonical',
        canonical_target: {
            canonical_id: 'cq_redis_performance',
            resolution: 'existing',
            requested_title: 'Redis 为什么快？',
            effective_title: 'Redis 性能原理',
            title_resolution: 'preserve_existing',
        },
        target_identity: {
            resource: 'canonical:cq_redis_performance',
            revision: 'canonical-rev-existing',
        },
    });

    assert.throws(
        () => projectCanonicalQuestionGroup({
            plan: extendPlan,
            canonical_snapshot: snapshot(existing, 'canonical-rev-existing'),
            question_rows: [question(), question({ question_id: 'q_b' })],
            taxonomy: TAXONOMY,
        }),
        /missing required question_id: q_existing/,
    );
});

test('projection rejects a Canonical snapshot that no longer matches the resolved plan identity', () => {
    assert.throws(
        () => projectCanonicalQuestionGroup({
            plan: plan(),
            canonical_snapshot: snapshot(null, 'newer-revision'),
            question_rows: [question(), question({ question_id: 'q_b' })],
            taxonomy: TAXONOMY,
        }),
        /snapshot revision does not match CanonicalizationPlan/,
    );

    assert.throws(
        () => projectCanonicalQuestionGroup({
            plan: plan(),
            canonical_snapshot: snapshot(existingCanonical()),
            question_rows: [question(), question({ question_id: 'q_b' })],
            taxonomy: TAXONOMY,
        }),
        /must still be absent for create projection/,
    );
});

test('projection is deterministic and does not mutate plan, snapshot, or Question rows', () => {
    const sourcePlan = plan();
    const sourceSnapshot = snapshot();
    const rows = [question(), question({ question_id: 'q_b', original_question: 'Redis 为什么这么快？' })];
    const beforePlan = structuredClone(sourcePlan);
    const beforeSnapshot = structuredClone(sourceSnapshot);
    const beforeRows = structuredClone(rows);

    const first = projectCanonicalQuestionGroup({
        plan: sourcePlan,
        canonical_snapshot: sourceSnapshot,
        question_rows: rows,
        taxonomy: TAXONOMY,
    });
    const second = projectCanonicalQuestionGroup({
        plan: sourcePlan,
        canonical_snapshot: sourceSnapshot,
        question_rows: rows,
        taxonomy: TAXONOMY,
    });

    assert.deepEqual(first, second);
    assert.deepEqual(sourcePlan, beforePlan);
    assert.deepEqual(sourceSnapshot, beforeSnapshot);
    assert.deepEqual(rows, beforeRows);
});

test('projection only accepts resolved non-authorizing CanonicalizationPlans', () => {
    assert.throws(
        () => projectCanonicalQuestionGroup({
            plan: plan({ mutation_authorized: true }),
            canonical_snapshot: snapshot(),
            question_rows: [question(), question({ question_id: 'q_b' })],
            taxonomy: TAXONOMY,
        }),
        /must not authorize mutation/,
    );
});
