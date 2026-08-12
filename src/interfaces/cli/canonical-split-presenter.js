'use strict';

/**
 * Preserve the legacy canonical split CLI JSON shape while keeping Application
 * diagnostics (integrity report, mutation plan, commit metadata) behind the
 * interface boundary.
 */
function presentCanonicalSplitResult(result) {
    if (!result || typeof result !== 'object') {
        throw new Error('canonical split application result is required');
    }

    return {
        ok: result.ok,
        source: result.source,
        new_canonical_id: result.new_canonical_id,
        question_id: result.question_id,
        canonical_count: result.canonical_count,
    };
}

module.exports = {
    presentCanonicalSplitResult,
};
