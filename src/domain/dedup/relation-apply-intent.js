'use strict';

const { RELATION_TYPES } = require('./relation-candidate');

const RELATION_APPLY_POLICIES = deepFreeze({
    same: {
        intent_kind: 'canonicalize_question_group',
        apply_required: true,
        required_inputs: ['canonical_id', 'canonical_title'],
    },
    alias: {
        intent_kind: 'canonicalize_question_group',
        apply_required: true,
        required_inputs: ['canonical_id', 'canonical_title'],
    },
    parent_child: {
        intent_kind: 'relation_record_only',
        apply_required: false,
        required_inputs: [],
        reason_code: 'relation_graph_apply_not_supported',
    },
    followup: {
        intent_kind: 'relation_record_only',
        apply_required: false,
        required_inputs: [],
        reason_code: 'relation_graph_apply_not_supported',
    },
    related: {
        intent_kind: 'relation_record_only',
        apply_required: false,
        required_inputs: [],
        reason_code: 'relation_graph_apply_not_supported',
    },
    unrelated: {
        intent_kind: 'no_apply',
        apply_required: false,
        required_inputs: [],
        reason_code: 'explicitly_unrelated',
    },
});

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
    return [...new Set(values || [])].sort((left, right) => String(left).localeCompare(String(right)));
}

function assertExplicitRelationDecision(decision) {
    if (!decision || typeof decision !== 'object' || Array.isArray(decision)) {
        throw new Error('Dedup relation decision is required for apply intent');
    }
    if (decision.schema_version !== 'dedup_relation_decision.v1') {
        throw new Error('Dedup relation apply intent requires dedup_relation_decision.v1');
    }
    if (decision.decision_state !== 'explicit') {
        throw new Error('Dedup relation apply intent requires an explicit decision');
    }
    if (!RELATION_TYPES.includes(decision.relation)) {
        throw new Error(`Unsupported dedup relation apply intent: ${decision.relation}`);
    }
    if (!decision.relation_candidate_key) {
        throw new Error('Dedup relation apply intent requires relation_candidate_key');
    }
    if (!decision.candidate_snapshot || typeof decision.candidate_snapshot !== 'object') {
        throw new Error('Dedup relation apply intent requires candidate_snapshot');
    }
    if (decision.candidate_snapshot.relation_candidate_key !== decision.relation_candidate_key) {
        throw new Error('Dedup relation apply intent candidate key mismatch');
    }
    if (!Array.isArray(decision.candidate_snapshot.question_ids)
        || decision.candidate_snapshot.question_ids.length === 0) {
        throw new Error('Dedup relation apply intent requires candidate question_ids');
    }
    if (!Array.isArray(decision.source_revisions) || decision.source_revisions.length === 0) {
        throw new Error('Dedup relation apply intent requires source_revisions');
    }
    if (!decision.actor || typeof decision.actor !== 'object') {
        throw new Error('Dedup relation apply intent requires decision actor');
    }
    return decision;
}

function normalizeCanonicalTarget(target) {
    if (!target || typeof target !== 'object' || Array.isArray(target)) {
        throw new Error('canonical_target must be an object');
    }
    const canonicalId = String(target.canonical_id || '').trim();
    const canonicalTitle = String(target.canonical_title || '').trim();
    if (!canonicalId || !canonicalTitle) {
        throw new Error('canonical_target canonical_id and canonical_title are required');
    }
    return {
        canonical_id: canonicalId,
        canonical_title: canonicalTitle,
    };
}

function classifyRelationApply(decision) {
    const validDecision = assertExplicitRelationDecision(decision);
    return RELATION_APPLY_POLICIES[validDecision.relation];
}

/**
 * Normalize an explicit RelationDecision into a side-effect-free ApplyIntent.
 *
 * This object does not authorize or perform a Canonical mutation. For `same`
 * and `alias`, it only captures the question group and optional Canonical
 * target required by a later Application Apply use case. The Apply use case
 * must still load current Canonical state and pass through Canonical policies
 * and the normal mutation boundary.
 *
 * `parent_child`, `followup`, and `related` remain review facts until a
 * dedicated relation-graph Apply capability exists. `unrelated` is an
 * explicit no-op.
 */
function createRelationApplyIntent(decision, options = {}) {
    const validDecision = assertExplicitRelationDecision(decision);
    const policy = RELATION_APPLY_POLICIES[validDecision.relation];
    const hasCanonicalTarget = Object.hasOwn(options, 'canonical_target');

    if (!policy.apply_required && hasCanonicalTarget) {
        throw new Error(
            `Relation ${validDecision.relation} cannot target Canonical apply`,
        );
    }

    const canonicalTarget = hasCanonicalTarget
        ? normalizeCanonicalTarget(options.canonical_target)
        : null;
    const intentState = policy.apply_required
        ? (canonicalTarget ? 'ready' : 'requires_input')
        : 'complete';

    return deepFreeze({
        schema_version: 'dedup_relation_apply_intent.v1',
        relation_candidate_key: validDecision.relation_candidate_key,
        relation: validDecision.relation,
        intent_kind: policy.intent_kind,
        intent_state: intentState,
        apply_required: policy.apply_required,
        required_inputs: [...policy.required_inputs],
        question_ids: uniqueSorted(validDecision.candidate_snapshot.question_ids),
        ...(canonicalTarget ? { canonical_target: canonicalTarget } : {}),
        ...(policy.reason_code ? { reason_code: policy.reason_code } : {}),
        decision_provenance: {
            actor: clone(validDecision.actor),
            decided_at: validDecision.decided_at || null,
            source_revisions: clone(validDecision.source_revisions),
        },
    });
}

module.exports = {
    RELATION_APPLY_POLICIES,
    classifyRelationApply,
    createRelationApplyIntent,
};
