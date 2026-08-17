'use strict';

function answerPath(canonicalId) {
    return `review/answers/${canonicalId}.md`;
}

function archivedAnswerPath(canonicalId) {
    return `review/archive/answers/${canonicalId}.md`;
}

/**
 * Preserve the legacy canonical merge CLI JSON shape without teaching the
 * Application layer about CLI path strings or presentation details.
 */
function presentCanonicalMergeResult(result) {
    if (!result || typeof result !== 'object') {
        throw new Error('canonical merge application result is required');
    }

    return {
        ok: result.ok,
        target: result.target,
        source: result.source,
        reason: result.reason,
        canonical_count: result.canonical_count,
        moved_question_ids: result.moved_question_ids,
        assigned_question_rows: result.assigned_question_rows,
        review_migration: result.review_migration,
        invalidated_target_answer: result.invalidated_target_answer
            ? {
                answer_path: answerPath(result.target),
                version: result.invalidated_target_answer.version,
            }
            : null,
        archived_source_answer: result.archived_source_answer
            ? {
                source_answer_path: answerPath(result.source),
                archived_answer_path: archivedAnswerPath(result.source),
                source_answer_status: result.archived_source_answer.source_answer_status,
                target_canonical_id: result.archived_source_answer.target_canonical_id,
            }
            : null,
    };
}

module.exports = {
    presentCanonicalMergeResult,
};
