'use strict';

/**
 * Preserve the legacy canonical accept CLI JSON shape while keeping Application
 * diagnostics (mutation plan and commit metadata) behind the interface boundary.
 */
function presentCanonicalAcceptResult(result) {
    if (!result || typeof result !== 'object') {
        throw new Error('canonical accept application result is required');
    }

    return {
        ok: result.ok,
        canonical_id: result.canonical_id,
        accepted_candidate_id: result.accepted_candidate_id,
        question_ids: result.question_ids,
        updated_question_rows: result.updated_question_rows,
        canonical_count: result.canonical_count,
    };
}

module.exports = {
    presentCanonicalAcceptResult,
};
