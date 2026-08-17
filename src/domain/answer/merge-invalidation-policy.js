'use strict';

function assertMetadata(metadata, label) {
    if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
        throw new Error(`${label} metadata is required`);
    }
}

/**
 * Decide whether a target Answer must be invalidated after Canonical merge and,
 * if so, return its next metadata.
 *
 * The rule intentionally preserves legacy behavior:
 * - invalidate when status is `ready` OR quality_tier is `curated`;
 * - set both status and quality_tier to `needs_update`;
 * - increment version;
 * - annotate the source Canonical that caused invalidation.
 *
 * Markdown parsing/writing is not a Domain concern.
 */
function invalidateAnswerForCanonicalMerge(metadata, sourceCanonicalId, updatedAt) {
    if (metadata == null) return null;
    assertMetadata(metadata, 'answer');
    if (!sourceCanonicalId) throw new Error('source canonical_id is required');
    if (!updatedAt) throw new Error('updatedAt is required');

    if (metadata.status !== 'ready' && metadata.quality_tier !== 'curated') {
        return null;
    }

    return {
        ...metadata,
        status: 'needs_update',
        quality_tier: 'needs_update',
        version: Number(metadata.version || 0) + 1,
        updated_at: updatedAt,
        invalidated_by_canonical_merge: sourceCanonicalId,
    };
}

/**
 * Decide whether the source Answer can be archived.
 *
 * Archive location/existence checks are supplied as semantic facts by the
 * caller; Domain never sees filesystem paths.
 */
function planSourceAnswerArchive(sourceAnswer, sourceArchiveExists, targetCanonicalId) {
    if (sourceAnswer == null) return null;
    if (!sourceAnswer || typeof sourceAnswer !== 'object' || Array.isArray(sourceAnswer)) {
        throw new Error('source answer is invalid');
    }
    if (!sourceAnswer.canonical_id) throw new Error('source answer canonical_id is required');
    if (!targetCanonicalId) throw new Error('target canonical_id is required');
    if (sourceAnswer.canonical_id === targetCanonicalId) {
        throw new Error('source and target canonical_id must be different');
    }
    if (sourceArchiveExists) {
        throw new Error(`Source answer archive already exists for ${sourceAnswer.canonical_id}`);
    }

    return {
        canonical_id: sourceAnswer.canonical_id,
        target_canonical_id: targetCanonicalId,
        source_answer_status: sourceAnswer.metadata?.status || 'draft',
        reason: 'canonical_merge',
    };
}

module.exports = {
    invalidateAnswerForCanonicalMerge,
    planSourceAnswerArchive,
};
