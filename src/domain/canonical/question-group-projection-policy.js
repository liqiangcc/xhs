'use strict';

const { acceptCanonicalCandidate } = require('./accept-policy');
const { refreshCanonicalFromQuestions } = require('./refresh-policy');

const CANONICALIZATION_PLAN_KINDS = Object.freeze([
    'create_canonical',
    'extend_existing_canonical',
]);

function uniqueSorted(values, comparator) {
    const items = [...new Set(values || [])];
    return comparator ? items.sort(comparator) : items.sort();
}

function assertCanonicalizationPlan(plan) {
    if (!plan || typeof plan !== 'object' || Array.isArray(plan)) {
        throw new Error('CanonicalizationPlan is required');
    }
    if (plan.schema_version !== 'canonicalization_plan.v1') {
        throw new Error('Canonical question group projection requires canonicalization_plan.v1');
    }
    if (plan.plan_state !== 'resolved') {
        throw new Error(`CanonicalizationPlan must be resolved: ${plan.plan_state}`);
    }
    if (!CANONICALIZATION_PLAN_KINDS.includes(plan.plan_kind)) {
        throw new Error(`Unsupported CanonicalizationPlan kind: ${plan.plan_kind}`);
    }
    if (plan.mutation_authorized !== false) {
        throw new Error('CanonicalizationPlan must not authorize mutation');
    }
    if (!Array.isArray(plan.question_ids) || plan.question_ids.length === 0) {
        throw new Error('CanonicalizationPlan question_ids are required');
    }
    if (!plan.canonical_target || typeof plan.canonical_target !== 'object') {
        throw new Error('CanonicalizationPlan canonical_target is required');
    }
    const canonicalId = String(plan.canonical_target.canonical_id || '').trim();
    const effectiveTitle = String(plan.canonical_target.effective_title || '').trim();
    if (!canonicalId || !effectiveTitle) {
        throw new Error('CanonicalizationPlan canonical_id and effective_title are required');
    }
    if (!plan.target_identity?.resource || !plan.target_identity?.revision) {
        throw new Error('CanonicalizationPlan target_identity resource and revision are required');
    }

    const resolution = plan.canonical_target.resolution;
    if (plan.plan_kind === 'create_canonical' && resolution !== 'absent') {
        throw new Error('create_canonical plan requires an absent target');
    }
    if (plan.plan_kind === 'extend_existing_canonical' && resolution !== 'existing') {
        throw new Error('extend_existing_canonical plan requires an existing target');
    }
    return plan;
}

function assertCanonicalSnapshot(snapshot, plan) {
    if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
        throw new Error('Canonical identity snapshot is required');
    }
    if (snapshot.resource !== plan.target_identity.resource) {
        throw new Error('Canonical identity snapshot resource does not match CanonicalizationPlan');
    }
    if (snapshot.revision !== plan.target_identity.revision) {
        throw new Error('Canonical identity snapshot revision does not match CanonicalizationPlan');
    }
    if (!Object.hasOwn(snapshot, 'record')) {
        throw new Error('Canonical identity snapshot record is required');
    }

    const canonicalId = String(plan.canonical_target.canonical_id).trim();
    if (plan.plan_kind === 'create_canonical') {
        if (snapshot.record !== null) {
            throw new Error(`Canonical ${canonicalId} must still be absent for create projection`);
        }
        return snapshot;
    }

    if (!snapshot.record || typeof snapshot.record !== 'object' || Array.isArray(snapshot.record)) {
        throw new Error(`Canonical ${canonicalId} must exist for extend projection`);
    }
    if (snapshot.record.canonical_id !== canonicalId) {
        throw new Error(`Canonical identity mismatch: expected ${canonicalId}`);
    }
    return snapshot;
}

function selectQuestionRows(questionRows, questionIds) {
    if (!Array.isArray(questionRows)) throw new Error('question_rows must be an array');
    const requiredIds = uniqueSorted(questionIds);
    const required = new Set(requiredIds);
    const rows = questionRows.filter((row) => required.has(row?.question_id));
    const presentIds = new Set(rows.map((row) => row.question_id));

    for (const questionId of requiredIds) {
        if (!presentIds.has(questionId)) {
            throw new Error(`Question rows are missing required question_id: ${questionId}`);
        }
    }
    for (const row of rows) {
        if (!String(row.original_question || '').trim()) {
            throw new Error(`Question ${row.question_id} original_question is required for Canonical projection`);
        }
    }
    return rows;
}

function questionAliases(questionRows) {
    return uniqueSorted(
        questionRows.map((row) => String(row.original_question).trim()).filter(Boolean),
        (left, right) => left.length - right.length || left.localeCompare(right, 'zh'),
    );
}

/**
 * Project a resolved, side-effect-free CanonicalizationPlan into the Canonical
 * record that a later mutation use case may choose to persist.
 *
 * This policy intentionally does not build or execute a MutationPlan. It
 * reuses Canonical accept/refresh rules as the SSOT for extending an existing
 * record and for recomputing aggregate fields from the full current Question
 * row set that will belong to the resulting Canonical.
 */
function projectCanonicalQuestionGroup(input = {}) {
    const plan = assertCanonicalizationPlan(input.plan);
    const snapshot = assertCanonicalSnapshot(input.canonical_snapshot, plan);
    const taxonomy = input.taxonomy;
    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }

    const plannedQuestionIds = uniqueSorted(plan.question_ids);
    const resultingQuestionIds = uniqueSorted([
        ...(snapshot.record?.question_ids || []),
        ...plannedQuestionIds,
    ]);
    const fullRows = selectQuestionRows(input.question_rows, resultingQuestionIds);
    const planned = new Set(plannedQuestionIds);
    const plannedRows = fullRows.filter((row) => planned.has(row.question_id));

    const canonicalId = String(plan.canonical_target.canonical_id).trim();
    const effectiveTitle = String(plan.canonical_target.effective_title).trim();
    const aliases = questionAliases(plannedRows);

    const projectionSeed = {
        canonical_title: effectiveTitle,
        aliases,
        question_ids: plannedQuestionIds,
        primary_domain: { l1: '其他', l2: '其他' },
        primary_entities: [],
        companies: [],
        frequency: plannedRows.length,
        review_priority: 'P2',
    };

    const accepted = acceptCanonicalCandidate(
        snapshot.record,
        projectionSeed,
        canonicalId,
        { title: effectiveTitle },
    );
    return refreshCanonicalFromQuestions(accepted, fullRows, taxonomy);
}

module.exports = {
    CANONICALIZATION_PLAN_KINDS,
    assertCanonicalizationPlan,
    selectQuestionRows,
    projectCanonicalQuestionGroup,
};
