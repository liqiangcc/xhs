'use strict';

const RELATION_TYPES = Object.freeze([
    'same',
    'alias',
    'parent_child',
    'followup',
    'related',
    'unrelated',
]);

function clone(value) {
    return structuredClone(value);
}

function deepFreeze(value) {
    if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
    Object.freeze(value);
    for (const item of Object.values(value)) deepFreeze(item);
    return value;
}

function uniqueSorted(values) {
    return [...new Set(values || [])].sort((a, b) => String(a).localeCompare(String(b)));
}

function assertDetectionCluster(cluster) {
    if (!cluster || typeof cluster !== 'object' || Array.isArray(cluster)) {
        throw new Error('Dedup detection cluster is required');
    }
    if (!cluster.anchor_question_id) {
        throw new Error('Dedup detection cluster anchor_question_id is required');
    }
    if (!Array.isArray(cluster.question_ids) || cluster.question_ids.length === 0) {
        throw new Error('Dedup detection cluster question_ids are required');
    }
    if (!Array.isArray(cluster.members) || cluster.members.length < 2) {
        throw new Error('Dedup relation candidate requires at least two detected members');
    }
    if (!Array.isArray(cluster.evidence) || cluster.evidence.length === 0) {
        throw new Error('Dedup relation candidate evidence is required');
    }
}

/**
 * Project detection evidence into an explicit review candidate.
 *
 * A RelationCandidate is deliberately not a relation decision. Reviewers may
 * choose one of RELATION_TYPES later, but this object cannot authorize a
 * Canonical mutation and therefore carries no canonical_id or MutationPlan.
 */
function createRelationCandidate(input = {}) {
    const cluster = input.cluster;
    assertDetectionCluster(cluster);

    const scope = String(input.scope || '').trim();
    if (!scope) throw new Error('Dedup relation candidate scope is required');

    const questionIds = uniqueSorted(cluster.question_ids);
    if (!questionIds.includes(cluster.anchor_question_id)) {
        throw new Error('Dedup relation candidate anchor must belong to question_ids');
    }

    return deepFreeze({
        schema_version: 'dedup_relation_candidate.v1',
        review_state: 'pending',
        scope,
        seed: input.seed == null ? null : String(input.seed),
        anchor_question_id: cluster.anchor_question_id,
        question_ids: questionIds,
        member_count: cluster.members.length,
        distinct_source_count: Number(cluster.distinct_source_count || 0),
        members: cluster.members.map(clone),
        evidence: cluster.evidence.map(clone),
        allowed_relations: [...RELATION_TYPES],
    });
}

module.exports = {
    RELATION_TYPES,
    createRelationCandidate,
};
