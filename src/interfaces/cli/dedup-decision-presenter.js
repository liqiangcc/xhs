'use strict';

function presentDedupDecisionResult(result) {
    if (!result || typeof result !== 'object' || result.ok !== true || !result.decision) {
        throw new Error('Dedup decision presenter requires a successful Application result');
    }
    const decision = result.decision;
    return {
        schema_version: 'dedup_relation_decision_result.v1',
        ok: true,
        relation_candidate_key: result.relation_candidate_key,
        relation: result.relation,
        decision_state: decision.decision_state,
        actor: structuredClone(decision.actor),
        rationale: decision.rationale ?? null,
        decided_at: decision.decided_at ?? null,
    };
}

module.exports = {
    presentDedupDecisionResult,
};
