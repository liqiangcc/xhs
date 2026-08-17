'use strict';

const { pickPriority } = require('./priority-policy');

function assertCanonicalRecord(record, role) {
    if (!record || typeof record !== 'object') {
        throw new Error(`${role} canonical is required`);
    }
    if (!record.canonical_id) {
        throw new Error(`${role} canonical_id is required`);
    }
}

function assertMergeableCanonical(target, source) {
    assertCanonicalRecord(target, 'target');
    assertCanonicalRecord(source, 'source');
    if (target.canonical_id === source.canonical_id) {
        throw new Error('target and source must be different');
    }
}

function uniqueSorted(values, compare) {
    return [...new Set(values.filter((value) => value !== undefined && value !== null))]
        .sort(compare);
}

/**
 * Build the pure in-memory Canonical result of merging source into target.
 *
 * This policy intentionally has no knowledge of questions persistence,
 * ReviewProgress migration, Answer archival/invalidation, indexes, history, or
 * filesystem transactions. Those effects belong to Application/Infrastructure.
 *
 * The returned shape preserves the current pre-refresh merge behavior so the
 * legacy command can be migrated without changing observable semantics.
 */
function mergeCanonical(target, source) {
    assertMergeableCanonical(target, source);

    return {
        ...target,
        canonical_title: target.canonical_title || source.canonical_title,
        aliases: uniqueSorted(
            [
                ...(target.aliases || []),
                source.canonical_title,
                ...(source.aliases || []),
            ],
            (a, b) => String(a).length - String(b).length || String(a).localeCompare(String(b), 'zh'),
        ),
        question_ids: uniqueSorted(
            [...(target.question_ids || []), ...(source.question_ids || [])],
            (a, b) => String(a).localeCompare(String(b)),
        ),
        primary_entities: uniqueSorted(
            [...(target.primary_entities || []), ...(source.primary_entities || [])],
            (a, b) => String(a).localeCompare(String(b), 'zh'),
        ),
        companies: uniqueSorted(
            [...(target.companies || []), ...(source.companies || [])],
            (a, b) => String(a).localeCompare(String(b), 'zh'),
        ),
        frequency: Math.max(Number(target.frequency || 0), Number(source.frequency || 0)),
        review_priority: pickPriority(target.review_priority, source.review_priority),
        answer_status: 'needs_update',
        schema_version: 'canonical_question.v1',
    };
}

module.exports = {
    assertMergeableCanonical,
    mergeCanonical,
};
