'use strict';

const { mergeReviewProgress } = require('../../domain/review/merge-progress-policy');

function assertRows(rows, label) {
    if (!Array.isArray(rows)) throw new Error(`${label} must be an array`);
}

/**
 * Build a storage-agnostic review mutation intent for Canonical merge.
 *
 * The planner decides review semantics; Infrastructure later maps this intent
 * to progress/session persistence without reimplementing merge policy.
 */
function planCanonicalReviewMigration(input = {}) {
    const targetCanonicalId = input.targetCanonicalId;
    const sourceCanonicalId = input.sourceCanonicalId;
    const targetItems = input.targetItems || [];
    const sourceItems = input.sourceItems || [];

    if (!targetCanonicalId || !sourceCanonicalId) {
        throw new Error('targetCanonicalId and sourceCanonicalId are required');
    }
    if (targetCanonicalId === sourceCanonicalId) {
        throw new Error('review migration source and target must be different');
    }
    assertRows(targetItems, 'targetItems');
    assertRows(sourceItems, 'sourceItems');

    if (targetItems.length > 1 || sourceItems.length > 1) {
        throw new Error(
            `Cannot merge review progress with duplicate rows: ${targetCanonicalId}=${targetItems.length}, ${sourceCanonicalId}=${sourceItems.length}`,
        );
    }

    const target = targetItems[0] || null;
    const source = sourceItems[0] || null;
    const mergedProgress = source
        ? mergeReviewProgress(target, source, targetCanonicalId, {
            updatedAtFallback: input.updatedAtFallback || null,
        })
        : null;

    return Object.freeze({
        from_canonical_id: sourceCanonicalId,
        to_canonical_id: targetCanonicalId,
        progress: Object.freeze({
            source_found: Boolean(source),
            target_found: Boolean(target),
            remove_canonical_ids: Object.freeze(
                source ? [targetCanonicalId, sourceCanonicalId] : [],
            ),
            upsert: mergedProgress ? Object.freeze(structuredClone(mergedProgress)) : null,
        }),
        session_events: Object.freeze({
            rebind_from_canonical_id: sourceCanonicalId,
            rebind_to_canonical_id: targetCanonicalId,
            annotate_migrated_from: true,
        }),
    });
}

module.exports = {
    planCanonicalReviewMigration,
};
