'use strict';

const {
    invalidateAnswerForCanonicalMerge,
    planSourceAnswerArchive,
} = require('../../domain/answer/merge-invalidation-policy');

function clone(value) {
    return structuredClone(value);
}

function freeze(value) {
    if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
    Object.freeze(value);
    for (const child of Object.values(value)) freeze(child);
    return value;
}

/**
 * Build storage-agnostic Answer mutation intent for Canonical merge.
 *
 * The planner decides whether the target needs invalidation and whether the
 * source should be archived. Infrastructure later updates Markdown metadata or
 * moves files without reimplementing these rules.
 */
function planCanonicalAnswerMerge(input = {}) {
    const targetCanonicalId = input.targetCanonicalId;
    const sourceCanonicalId = input.sourceCanonicalId;
    if (!targetCanonicalId || !sourceCanonicalId) {
        throw new Error('targetCanonicalId and sourceCanonicalId are required');
    }
    if (targetCanonicalId === sourceCanonicalId) {
        throw new Error('answer merge source and target must be different');
    }
    if (!input.updatedAt) throw new Error('updatedAt is required');

    const targetAnswer = input.targetAnswer || null;
    const sourceAnswer = input.sourceAnswer || null;

    if (targetAnswer && targetAnswer.canonical_id !== targetCanonicalId) {
        throw new Error(`Target answer canonical_id mismatch: expected ${targetCanonicalId}`);
    }
    if (sourceAnswer && sourceAnswer.canonical_id !== sourceCanonicalId) {
        throw new Error(`Source answer canonical_id mismatch: expected ${sourceCanonicalId}`);
    }

    const nextTargetMetadata = invalidateAnswerForCanonicalMerge(
        targetAnswer?.metadata || null,
        sourceCanonicalId,
        input.updatedAt,
    );
    const archive = planSourceAnswerArchive(
        sourceAnswer,
        Boolean(input.sourceArchiveExists),
        targetCanonicalId,
    );

    return freeze({
        target_invalidation: nextTargetMetadata
            ? {
                canonical_id: targetCanonicalId,
                reason: 'canonical_merge',
                source_canonical_id: sourceCanonicalId,
                next_metadata: clone(nextTargetMetadata),
            }
            : null,
        source_archive: archive ? clone(archive) : null,
    });
}

module.exports = {
    planCanonicalAnswerMerge,
};
