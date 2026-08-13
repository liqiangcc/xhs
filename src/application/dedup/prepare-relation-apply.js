'use strict';

const { createRelationApplyIntent } = require('../../domain/dedup/relation-apply-intent');
const {
    assertRelationDecisionRepository,
} = require('../../ports/repositories/relation-decision-repository');
const {
    assertDedupIndexRetrievalRepository,
} = require('../../ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../../ports/repositories/dedup-question-retrieval-repository');
const {
    revisionOf,
    assertSourcesFresh,
} = require('./relation-source-freshness');

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

function canonicalTargetFromInput(input) {
    const hasId = Object.hasOwn(input, 'canonical_id');
    const hasTitle = Object.hasOwn(input, 'canonical_title');
    if (!hasId && !hasTitle) return null;
    if (!hasId || !hasTitle) {
        throw new Error('canonical_id and canonical_title must be provided together');
    }
    return {
        canonical_id: input.canonical_id,
        canonical_title: input.canonical_title,
    };
}

function createPrepareRelationApplyUseCase(dependencies = {}) {
    const relationDecisionRepository = assertRelationDecisionRepository(
        dependencies.relationDecisionRepository,
    );
    const indexRepository = assertDedupIndexRetrievalRepository(dependencies.indexRepository);
    const questionRepository = assertDedupQuestionRetrievalRepository(dependencies.questionRepository);

    return async function prepareRelationApplyUseCase(input = {}) {
        const relationCandidateKey = String(input.relation_candidate_key || '').trim();
        if (!relationCandidateKey) throw new Error('relation_candidate_key is required');
        for (const forbidden of ['decision', 'source_revisions', 'expected_revisions']) {
            if (Object.hasOwn(input, forbidden)) {
                throw new Error('relation apply evidence is controlled by Application');
            }
        }

        const decisionSnapshot = await relationDecisionRepository.get(relationCandidateKey);
        if (!decisionSnapshot) {
            throw new Error(`Relation decision not found: ${relationCandidateKey}`);
        }
        assertSnapshot(decisionSnapshot, 'relation decision', 'decision');
        const decision = decisionSnapshot.decision;
        if (decision.relation_candidate_key !== relationCandidateKey) {
            throw new Error(`Relation decision snapshot key mismatch: expected ${relationCandidateKey}`);
        }
        if (decision.decision_state !== 'explicit') {
            throw new Error(`Relation decision must be explicit: ${relationCandidateKey}`);
        }
        if (!Array.isArray(decision.source_revisions)) {
            throw new Error('relation decision source_revisions are required');
        }
        if (decision.candidate_snapshot?.scope !== 'entity') {
            throw new Error(
                `Unsupported relation decision scope: ${decision.candidate_snapshot?.scope || 'missing'}`,
            );
        }

        const indexSnapshot = assertSnapshot(
            await indexRepository.findEntityRefs(decision.candidate_snapshot.seed),
            'current dedup entity index',
            'refs',
        );
        if (!Array.isArray(indexSnapshot.refs)) {
            throw new Error('current dedup entity index refs must be an array');
        }
        const questionSnapshot = assertSnapshot(
            await questionRepository.findByRefs(indexSnapshot.refs),
            'current dedup questions',
            'questions',
        );
        if (!Array.isArray(questionSnapshot.questions)) {
            throw new Error('current dedup question snapshot questions must be an array');
        }

        const currentSourceRevisions = [revisionOf(indexSnapshot), revisionOf(questionSnapshot)];
        assertSourcesFresh(decision.source_revisions, currentSourceRevisions);

        const canonicalTarget = canonicalTargetFromInput(input);
        const intent = createRelationApplyIntent(
            decision,
            canonicalTarget ? { canonical_target: canonicalTarget } : {},
        );

        return {
            ok: true,
            relation_candidate_key: relationCandidateKey,
            relation: decision.relation,
            intent,
            decision_snapshot: {
                resource: decisionSnapshot.resource,
                revision: decisionSnapshot.revision,
            },
            current_source_revisions: currentSourceRevisions,
        };
    };
}

module.exports = {
    createPrepareRelationApplyUseCase,
    canonicalTargetFromInput,
};
