'use strict';

const {
    assertCanonicalIdentityRepository,
} = require('../../ports/repositories/canonical-identity-repository');

const CANONICALIZATION_RELATIONS = Object.freeze(['same', 'alias']);

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

function assertReadyCanonicalizationIntent(intent) {
    if (!intent || typeof intent !== 'object' || Array.isArray(intent)) {
        throw new Error('Relation apply intent is required');
    }
    if (intent.schema_version !== 'dedup_relation_apply_intent.v1') {
        throw new Error('Canonicalization planning requires dedup_relation_apply_intent.v1');
    }
    if (intent.intent_kind !== 'canonicalize_question_group') {
        throw new Error(`Unsupported relation apply intent kind: ${intent.intent_kind}`);
    }
    if (intent.intent_state !== 'ready') {
        throw new Error(`Canonicalization planning requires a ready intent: ${intent.intent_state}`);
    }
    if (intent.apply_required !== true) {
        throw new Error('Canonicalization planning requires apply_required=true');
    }
    if (!CANONICALIZATION_RELATIONS.includes(intent.relation)) {
        throw new Error(`Unsupported canonicalization relation: ${intent.relation}`);
    }
    if (!intent.relation_candidate_key) {
        throw new Error('Canonicalization planning requires relation_candidate_key');
    }
    if (!Array.isArray(intent.question_ids) || intent.question_ids.length === 0) {
        throw new Error('Canonicalization planning requires question_ids');
    }
    if (!intent.canonical_target || typeof intent.canonical_target !== 'object') {
        throw new Error('Canonicalization planning requires canonical_target');
    }
    const canonicalId = String(intent.canonical_target.canonical_id || '').trim();
    const canonicalTitle = String(intent.canonical_target.canonical_title || '').trim();
    if (!canonicalId || !canonicalTitle) {
        throw new Error('Canonicalization planning requires canonical_id and canonical_title');
    }
    return intent;
}

function assertTargetIdentity(snapshot, canonicalId) {
    if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
        throw new Error('Canonical target identity snapshot is required');
    }
    if (!snapshot.resource || typeof snapshot.resource !== 'string') {
        throw new Error('Canonical target identity resource is required');
    }
    if (!snapshot.revision || typeof snapshot.revision !== 'string') {
        throw new Error('Canonical target identity revision is required');
    }
    if (!Object.hasOwn(snapshot, 'record')) {
        throw new Error('Canonical target identity record is required');
    }
    if (snapshot.record != null) {
        if (typeof snapshot.record !== 'object' || Array.isArray(snapshot.record)) {
            throw new Error('Canonical target identity record is invalid');
        }
        if (snapshot.record.canonical_id !== canonicalId) {
            throw new Error(`Canonical target identity mismatch: expected ${canonicalId}`);
        }
        if (!String(snapshot.record.canonical_title || '').trim()) {
            throw new Error(`Existing Canonical ${canonicalId} is missing canonical_title`);
        }
    }
    return snapshot;
}

function createCanonicalizationPlan(input = {}) {
    const intent = assertReadyCanonicalizationIntent(input.intent);
    const canonicalId = String(intent.canonical_target.canonical_id).trim();
    const requestedTitle = String(intent.canonical_target.canonical_title).trim();
    const identity = assertTargetIdentity(input.target_identity, canonicalId);
    const existing = identity.record;
    const resolution = existing ? 'existing' : 'absent';
    const planKind = existing ? 'extend_existing_canonical' : 'create_canonical';
    const effectiveTitle = existing ? String(existing.canonical_title).trim() : requestedTitle;

    return deepFreeze({
        schema_version: 'canonicalization_plan.v1',
        plan_state: 'resolved',
        plan_kind: planKind,
        relation_candidate_key: intent.relation_candidate_key,
        relation: intent.relation,
        question_ids: uniqueSorted(intent.question_ids),
        canonical_target: {
            canonical_id: canonicalId,
            resolution,
            requested_title: requestedTitle,
            effective_title: effectiveTitle,
            title_resolution: existing ? 'preserve_existing' : 'use_requested',
        },
        target_identity: {
            resource: identity.resource,
            revision: identity.revision,
        },
        decision_provenance: clone(intent.decision_provenance || null),
        mutation_authorized: false,
    });
}

function createResolveQuestionGroupCanonicalizationUseCase(dependencies = {}) {
    const canonicalIdentityRepository = assertCanonicalIdentityRepository(
        dependencies.canonicalIdentityRepository,
    );

    return async function resolveQuestionGroupCanonicalization(input = {}) {
        if (Object.hasOwn(input, 'target_identity') || Object.hasOwn(input, 'canonical_record')) {
            throw new Error('Canonical target state is controlled by Application');
        }
        const intent = assertReadyCanonicalizationIntent(input.intent);
        const canonicalId = String(intent.canonical_target.canonical_id).trim();
        const targetIdentity = await canonicalIdentityRepository.inspect(canonicalId);
        const plan = createCanonicalizationPlan({
            intent,
            target_identity: targetIdentity,
        });

        return {
            ok: true,
            relation_candidate_key: intent.relation_candidate_key,
            canonical_id: canonicalId,
            resolution: plan.canonical_target.resolution,
            plan,
        };
    };
}

module.exports = {
    CANONICALIZATION_RELATIONS,
    assertReadyCanonicalizationIntent,
    createCanonicalizationPlan,
    createResolveQuestionGroupCanonicalizationUseCase,
};
