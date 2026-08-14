'use strict';

function presentDedupApplyResult(result) {
    if (!result || typeof result !== 'object' || result.ok !== true) {
        throw new Error('Dedup apply presenter requires a successful Application result');
    }

    if (result.applied !== true) {
        return {
            schema_version: 'dedup_relation_apply_result.v1',
            ok: true,
            applied: false,
            relation_candidate_key: result.relation_candidate_key,
            relation: result.relation,
            reason_code: result.reason_code || 'apply_not_required',
        };
    }

    return {
        schema_version: 'dedup_relation_apply_result.v1',
        ok: true,
        applied: true,
        relation_candidate_key: result.relation_candidate_key,
        relation: result.relation,
        canonical_id: result.canonical_id,
        canonical_resolution: result.canonical_resolution,
        question_ids: [...(result.question_ids || [])],
        updated_question_rows: result.updated_question_rows ?? 0,
        canonical_count: result.canonical_count ?? null,
        committed: result.commit?.committed === true,
        operation: result.commit?.operation || null,
    };
}

module.exports = {
    presentDedupApplyResult,
};
