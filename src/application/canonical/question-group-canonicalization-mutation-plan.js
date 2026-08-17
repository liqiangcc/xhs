'use strict';

const { createCanonicalMutationPlan } = require('./mutation-plan');
const {
    assertCanonicalizationPlan,
} = require('../../domain/canonical/question-group-projection-policy');

function assertObject(value, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        throw new Error(`${label} must be an object`);
    }
    return value;
}

function uniqueSorted(values) {
    return [...new Set(values || [])].sort((left, right) => String(left).localeCompare(String(right)));
}

function sameStringSet(left, right) {
    const leftValues = uniqueSorted(left);
    const rightValues = uniqueSorted(right);
    return leftValues.length === rightValues.length
        && leftValues.every((value, index) => value === rightValues[index]);
}

function assertExpectedRevisions(revisions, plan) {
    if (!Array.isArray(revisions) || revisions.length === 0) {
        throw new Error('Canonicalization preparation expected_revisions are required');
    }
    const byResource = new Map();
    for (const item of revisions) {
        assertObject(item, 'Canonicalization expected revision');
        const resource = String(item.resource || '').trim();
        const revision = String(item.revision || '').trim();
        if (!resource || !revision) {
            throw new Error('Canonicalization expected revision resource and revision are required');
        }
        if (byResource.has(resource)) {
            throw new Error(`Duplicate Canonicalization expected revision: ${resource}`);
        }
        byResource.set(resource, revision);
    }
    const targetRevision = byResource.get(plan.target_identity.resource);
    if (targetRevision !== plan.target_identity.revision) {
        throw new Error('Canonicalization expected revisions do not preserve target identity');
    }
    return revisions;
}

function assertProjectedRecord(record, plan, resultingQuestionIds) {
    assertObject(record, 'Canonicalization projected_record');
    const canonicalId = String(plan.canonical_target.canonical_id).trim();
    if (record.canonical_id !== canonicalId) {
        throw new Error(`Canonicalization projected record id mismatch: expected ${canonicalId}`);
    }
    if (!sameStringSet(record.question_ids, resultingQuestionIds)) {
        throw new Error('Canonicalization projected record question_ids do not match prepared membership');
    }
    if (!String(record.canonical_title || '').trim()) {
        throw new Error('Canonicalization projected record canonical_title is required');
    }
    return record;
}

function normalizeBindingStates(states, plan, canonicalId) {
    if (!Array.isArray(states)) {
        throw new Error('Canonicalization planned_question_binding_states are required');
    }
    const plannedQuestionIds = uniqueSorted(plan.question_ids);
    const byQuestionId = new Map();

    for (const state of states) {
        assertObject(state, 'Canonicalization planned Question binding state');
        const questionId = String(state.question_id || '').trim();
        if (!questionId) {
            throw new Error('Canonicalization binding state question_id is required');
        }
        if (byQuestionId.has(questionId)) {
            throw new Error(`Duplicate Canonicalization binding state: ${questionId}`);
        }
        if (!Array.isArray(state.from_canonical_ids) || state.from_canonical_ids.length === 0) {
            throw new Error(`Canonicalization binding state ${questionId} from_canonical_ids are required`);
        }

        const normalized = [];
        for (const value of state.from_canonical_ids) {
            if (value !== null && (!value || typeof value !== 'string')) {
                throw new Error(
                    `Canonicalization binding state ${questionId} must contain canonical ids or null`,
                );
            }
            if (!normalized.some((item) => item === value)) normalized.push(value);
        }
        const foreign = normalized.find((value) => value !== null && value !== canonicalId);
        if (foreign) {
            throw new Error(`Question ${questionId} already belongs to ${foreign}`);
        }
        if (plan.plan_kind === 'create_canonical' && normalized.includes(canonicalId)) {
            throw new Error(`Question ${questionId} binds to absent Canonical ${canonicalId}`);
        }
        byQuestionId.set(questionId, normalized);
    }

    if (!sameStringSet([...byQuestionId.keys()], plannedQuestionIds)) {
        throw new Error('Canonicalization binding states must cover exactly the planned question_ids');
    }
    return byQuestionId;
}

function canonicalizationRebindings(plan, bindingStates) {
    const canonicalId = String(plan.canonical_target.canonical_id).trim();
    const byQuestionId = normalizeBindingStates(bindingStates, plan, canonicalId);
    return uniqueSorted(plan.question_ids)
        .filter((questionId) => byQuestionId.get(questionId).includes(null))
        .map((questionId) => ({
            question_id: questionId,
            from_canonical_id: null,
            to_canonical_id: canonicalId,
        }));
}

/**
 * Convert a fully prepared CanonicalizationPlan into the shared
 * canonical_mutation_plan.v1 envelope without executing it.
 */
function createQuestionGroupCanonicalizationMutationPlan(preparation = {}) {
    assertObject(preparation, 'Canonicalization preparation');
    if (preparation.ok !== true) {
        throw new Error('Canonicalization preparation must be successful');
    }

    const plan = assertCanonicalizationPlan(preparation.plan);
    const canonicalId = String(plan.canonical_target.canonical_id).trim();
    if (preparation.canonical_id !== canonicalId) {
        throw new Error(`Canonicalization preparation canonical_id mismatch: expected ${canonicalId}`);
    }
    if (!Array.isArray(preparation.question_ids) || preparation.question_ids.length === 0) {
        throw new Error('Canonicalization preparation question_ids are required');
    }
    if (!preparation.question_ids.every((questionId) =>
        plan.question_ids.includes(questionId) || preparation.projected_record?.question_ids?.includes(questionId))) {
        throw new Error('Canonicalization preparation contains unknown question_ids');
    }

    const projectedRecord = assertProjectedRecord(
        preparation.projected_record,
        plan,
        preparation.question_ids,
    );
    const expectedRevisions = assertExpectedRevisions(preparation.expected_revisions, plan);
    const questionRebindings = canonicalizationRebindings(
        plan,
        preparation.planned_question_binding_states,
    );

    return createCanonicalMutationPlan({
        operation: 'canonicalize',
        expected_revisions: expectedRevisions,
        changes: {
            canonical_upserts: [projectedRecord],
            canonical_removals: [],
            question_rebindings: questionRebindings,
            review_migrations: [],
            answer_invalidations: [],
            answer_archives: [],
            rebuild_indexes: true,
            history_entry: null,
        },
    });
}

module.exports = {
    createQuestionGroupCanonicalizationMutationPlan,
    canonicalizationRebindings,
};
