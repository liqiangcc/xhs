'use strict';

const { createRelationDecision } = require('../../domain/dedup/relation-decision');
const {
    assertRelationCandidateRepository,
} = require('../../ports/repositories/relation-candidate-repository');
const { assertRelationDecisionGateway } = require('../../ports/relation-decision-gateway');
const {
    revisionOf,
    assertSourcesFresh,
} = require('./relation-source-freshness');
const { createRelationSourceLoader } = require('./relation-source-retrieval');

function assertSnapshot(snapshot, label, valueKey) {
    if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
        throw new Error(`${label} snapshot is required`);
    }
    if (!snapshot.resource || typeof snapshot.resource !== 'string') {
        throw new Error(`${label} snapshot resource is required`);
    }
    if (!snapshot.revision || typeof snapshot.revision !== 'string') {
        throw new Error(`${label} snapshot revision is required`);
    }
    if (!(valueKey in snapshot)) {
        throw new Error(`${label} snapshot ${valueKey} is required`);
    }
    return snapshot;
}

function createRecordRelationDecisionUseCase(dependencies = {}) {
    const relationCandidateRepository = assertRelationCandidateRepository(
        dependencies.relationCandidateRepository,
    );
    const relationDecisionGateway = assertRelationDecisionGateway(dependencies.relationDecisionGateway);
    const loadRelationSource = createRelationSourceLoader(dependencies);

    return async function recordRelationDecisionUseCase(input = {}) {
        const relationCandidateKey = String(input.relation_candidate_key || '').trim();
        if (!relationCandidateKey) throw new Error('relation_candidate_key is required');
        if (Object.hasOwn(input, 'candidate')) {
            throw new Error('relation candidate must be loaded through RelationCandidateRepository');
        }
        if (Object.hasOwn(input, 'source_revisions') || Object.hasOwn(input, 'expected_revisions')) {
            throw new Error('relation decision revisions are controlled by Application');
        }

        const candidateSnapshot = await relationCandidateRepository.get(relationCandidateKey);
        if (!candidateSnapshot) {
            throw new Error(`Relation candidate not found: ${relationCandidateKey}`);
        }
        assertSnapshot(candidateSnapshot, 'relation candidate', 'candidate');
        if (!Array.isArray(candidateSnapshot.source_revisions)) {
            throw new Error('relation candidate snapshot source_revisions are required');
        }
        if (candidateSnapshot.candidate.relation_candidate_key !== relationCandidateKey) {
            throw new Error(
                `Relation candidate snapshot key mismatch: expected ${relationCandidateKey}`,
            );
        }

        const currentSource = await loadRelationSource(candidateSnapshot.candidate);
        assertSourcesFresh(
            candidateSnapshot.source_revisions,
            currentSource.current_source_revisions,
        );

        const decision = createRelationDecision({
            candidate: candidateSnapshot.candidate,
            relation: input.relation,
            actor: input.actor,
            rationale: input.rationale,
            decided_at: input.decided_at,
            source_revisions: candidateSnapshot.source_revisions,
        });
        const expectedRevisions = [
            revisionOf(candidateSnapshot),
            ...candidateSnapshot.source_revisions,
        ];
        const stored = await relationDecisionGateway.record(decision, {
            expected_revisions: expectedRevisions,
        });
        if (!stored || stored.recorded !== true || !stored.resource || !stored.revision) {
            throw new Error('RelationDecisionGateway returned invalid record metadata');
        }

        return {
            ok: true,
            relation_candidate_key: relationCandidateKey,
            relation: decision.relation,
            decision,
            store: {
                resource: stored.resource,
                revision: stored.revision,
            },
        };
    };
}

module.exports = {
    createRecordRelationDecisionUseCase,
    assertSourcesFresh,
};
