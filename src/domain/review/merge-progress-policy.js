'use strict';

function maxValue(...values) {
    return values.filter(Boolean).sort().at(-1) || null;
}

function minValue(...values) {
    return values.filter(Boolean).sort()[0] || null;
}

function uniqueSorted(values) {
    return [...new Set((values || []).filter(Boolean))]
        .sort((a, b) => String(a).localeCompare(String(b)));
}

/**
 * Merge ReviewProgress when one Canonical is merged into another.
 *
 * This preserves the current review semantics while removing filesystem/date
 * dependencies from the rule itself. The caller supplies updatedAtFallback so
 * the Domain remains deterministic and clock-free.
 */
function mergeReviewProgress(target, source, targetCanonicalId, options = {}) {
    if (!source || typeof source !== 'object') {
        throw new Error('source review progress is required');
    }
    if (!targetCanonicalId) throw new Error('target canonical_id is required');
    if (!source.canonical_id) throw new Error('source review canonical_id is required');

    if (!target) {
        return {
            ...source,
            canonical_id: targetCanonicalId,
            migrated_from_canonical_ids: uniqueSorted([
                ...(source.migrated_from_canonical_ids || []),
                source.canonical_id,
            ]),
        };
    }

    const level = Math.min(Number(target.level || 0), Number(source.level || 0));
    const mistakeCount = Number(target.mistake_count || 0) + Number(source.mistake_count || 0);

    return {
        ...target,
        canonical_id: targetCanonicalId,
        status: mistakeCount > 0 ? 'weak' : (level >= 5 ? 'mastered' : 'learning'),
        level,
        review_count: Number(target.review_count || 0) + Number(source.review_count || 0),
        last_reviewed_at: maxValue(target.last_reviewed_at, source.last_reviewed_at),
        next_review_at: minValue(target.next_review_at, source.next_review_at),
        confidence: Math.min(Number(target.confidence ?? 0.5), Number(source.confidence ?? 0.5)),
        difficulty: Math.max(Number(target.difficulty || 3), Number(source.difficulty || 3)),
        mistake_count: mistakeCount,
        updated_at: maxValue(target.updated_at, source.updated_at) || options.updatedAtFallback || null,
        migrated_from_canonical_ids: uniqueSorted([
            ...(target.migrated_from_canonical_ids || []),
            ...(source.migrated_from_canonical_ids || []),
            source.canonical_id,
        ]),
    };
}

module.exports = {
    mergeReviewProgress,
};
