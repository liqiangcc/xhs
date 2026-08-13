'use strict';

const { createRelationDecision } = require('../../domain/dedup/relation-decision');
const {
    assertRelationCandidateRepository,
} = require('../../ports/repositories/relation-candidate-repository');
const {
    assertDedupIndexRetrievalRepository,
} = require('../../ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../../ports/repositories/dedup-question-retrieval-repository');
const { assertRelationDecisionStore } = require('../../ports/relation-decision-store');

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

function revisionOf(snapshot) {
    return {
        resource: snapshot.resource,
        revision: snapshot.revision,
    };
}

function normalizeRevisionSet(revisions, label) {
    if (!Array.isArray(revisions) || revisions.length === 0) {
        throw new Error(`${label} revisions are required`);
    }
    const map = new Map();
    for (const item of revisions) {
        const resource = String(item?.resource || '').trim();
        const revision = String(item?.revision || '').trim();
        if (!resource || !revision) {
            throw new Error(`${label} revision resource and revision are required`);
        }
        if (map.has(resource)) throw new Error(`Duplicate ${label} revision: ${resource}`);
        map.set(resource, revision);
    }
    return map;
}

function assertSourcesFresh(expectedRevisions, currentRevisions) {
    const expected = normalizeRevisionSet(expectedRevisions, 'relation candidate source');
    const current = normalizeRevisionSet(currentRevisions, 'current relation source');
    if (expected.size !== current.size) {
        throw new Error('Stale relation candidate sources: source set changed');
    }
    for (const [resource, expectedRevision] of expected.entries()) {
        const currentRevision = current.get(resource);
        if (currentRevision !== expectedRevision) {
            throw new Error(
                `Stale relation candidate source ${resource}: expected ${expectedRevision}, got ${currentRevision || 'missing'}`,
            );
        }
    }
}

function createRecordRelationDecisionUseCase(dependencies = {}) {
    const relationCandidateRepository = assertRelationCandidateRepository(
        dependencies.relationCandidateRepository,
    );
    const indexRepository = assertDedupIndexRetrievalRepository(dependencies.indexRepository);
    const questionRepository = assertDedupQuestionRetrievalRepository(dependencies.questionRepository);
    const relationDecisionStore = assertRelationDecisionStore(dependencies.relationDecisionStore);

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
        if (candidateSnapshot.candidate.scope !== 'entity') {
            throw new Error(
                `Unsupported relation candidate scope: ${candidateSnapshot.candidate.scope}`,
            );
        }

        const indexSnapshot = assertSnapshot(
            await indexRepository.findEntityRefs(candidateSnapshot.candidate.seed),
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
        assertSourcesFresh(candidateSnapshot.source_revisions, currentSourceRevisions);

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
        const stored = await relationDecisionStore.record(decision, {
            expected_revisions: expectedRevisions,
        });
        if (!stored || stored.recorded !== true || !stored.resource || !stored.revision) {
            throw new Error('RelationDecisionStore returned invalid record metadata');
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
