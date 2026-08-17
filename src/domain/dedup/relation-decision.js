'use strict';

const { RELATION_TYPES } = require('./relation-candidate');

const DECISION_ACTOR_TYPES = Object.freeze(['human', 'ai']);

function clone(value) {
    return structuredClone(value);
}

function deepFreeze(value) {
    if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
    Object.freeze(value);
    for (const item of Object.values(value)) deepFreeze(item);
    return value;
}

function assertRelationCandidate(candidate) {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) {
        throw new Error('Dedup relation candidate is required');
    }
    if (candidate.schema_version !== 'dedup_relation_candidate.v1') {
        throw new Error('Dedup relation candidate schema_version is invalid');
    }
    if (!candidate.relation_candidate_key) {
        throw new Error('Dedup relation candidate key is required');
    }
    if (candidate.review_state !== 'pending') {
        throw new Error(`Dedup relation candidate must be pending: ${candidate.relation_candidate_key}`);
    }
    if (!Array.isArray(candidate.question_ids) || candidate.question_ids.length === 0) {
        throw new Error('Dedup relation candidate question_ids are required');
    }
    if (!candidate.anchor_question_id || !candidate.question_ids.includes(candidate.anchor_question_id)) {
        throw new Error('Dedup relation candidate anchor must belong to question_ids');
    }
    if (!Array.isArray(candidate.evidence) || candidate.evidence.length === 0) {
        throw new Error('Dedup relation candidate evidence is required');
    }
    if (!Array.isArray(candidate.allowed_relations) || candidate.allowed_relations.length === 0) {
        throw new Error('Dedup relation candidate allowed_relations are required');
    }
    return candidate;
}

function normalizeSourceRevisions(sourceRevisions) {
    if (!Array.isArray(sourceRevisions) || sourceRevisions.length === 0) {
        throw new Error('Dedup relation decision source_revisions are required');
    }

    const seen = new Set();
    const normalized = sourceRevisions.map((item) => {
        if (!item || typeof item !== 'object' || Array.isArray(item)) {
            throw new Error('Dedup relation decision source revision is invalid');
        }
        const resource = String(item.resource || '').trim();
        const revision = String(item.revision || '').trim();
        if (!resource || !revision) {
            throw new Error('Dedup relation decision source revision resource and revision are required');
        }
        if (seen.has(resource)) {
            throw new Error(`Duplicate dedup relation decision source revision: ${resource}`);
        }
        seen.add(resource);
        return { resource, revision };
    });

    return normalized.sort((left, right) => left.resource.localeCompare(right.resource));
}

function normalizeDecisionActor(actor) {
    if (!actor || typeof actor !== 'object' || Array.isArray(actor)) {
        throw new Error('Dedup relation decision actor is required');
    }
    const type = String(actor.type || '').trim();
    const id = String(actor.id || '').trim();
    if (!DECISION_ACTOR_TYPES.includes(type)) {
        throw new Error(`Unsupported dedup relation decision actor type: ${type}`);
    }
    if (!id) throw new Error('Dedup relation decision actor id is required');

    return {
        type,
        id,
        ...(actor.display_name == null ? {} : { display_name: String(actor.display_name) }),
    };
}

function candidateSnapshot(candidate) {
    return {
        relation_candidate_key: candidate.relation_candidate_key,
        scope: candidate.scope,
        seed: candidate.seed,
        anchor_question_id: candidate.anchor_question_id,
        question_ids: [...candidate.question_ids],
        member_count: candidate.member_count,
        distinct_source_count: candidate.distinct_source_count,
        members: (candidate.members || []).map(clone),
        evidence: candidate.evidence.map(clone),
    };
}

/**
 * Record an explicit reviewer decision for a previously detected relation
 * candidate.
 *
 * A RelationDecision is an auditable fact, not an Apply command. Even `same`
 * or `alias` does not authorize Canonical mutation by itself. A later
 * Application use case must validate freshness and translate an explicit
 * decision into an allowed Canonical command through the normal mutation
 * boundary.
 */
function createRelationDecision(input = {}) {
    const candidate = assertRelationCandidate(input.candidate);
    const relation = String(input.relation || '').trim();
    if (!RELATION_TYPES.includes(relation)) {
        throw new Error(`Unsupported dedup relation decision: ${relation}`);
    }
    if (!candidate.allowed_relations.includes(relation)) {
        throw new Error(
            `Relation ${relation} is not allowed for ${candidate.relation_candidate_key}`,
        );
    }

    const sourceRevisions = normalizeSourceRevisions(input.source_revisions);
    const actor = normalizeDecisionActor(input.actor);
    const rationale = input.rationale == null ? null : String(input.rationale).trim();
    const decidedAt = input.decided_at == null ? null : String(input.decided_at).trim();

    return deepFreeze({
        schema_version: 'dedup_relation_decision.v1',
        relation_candidate_key: candidate.relation_candidate_key,
        relation,
        decision_state: 'explicit',
        actor,
        rationale: rationale || null,
        decided_at: decidedAt || null,
        source_revisions: sourceRevisions,
        candidate_snapshot: candidateSnapshot(candidate),
    });
}

module.exports = {
    DECISION_ACTOR_TYPES,
    createRelationDecision,
    normalizeSourceRevisions,
};
