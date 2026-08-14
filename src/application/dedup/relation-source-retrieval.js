'use strict';

const {
    assertDedupIndexRetrievalRepository,
} = require('../../ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupHotspotRetrievalRepository,
} = require('../../ports/repositories/dedup-hotspot-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../../ports/repositories/dedup-question-retrieval-repository');
const { revisionOf } = require('./relation-source-freshness');

const SUPPORTED_RELATION_SOURCE_SCOPES = Object.freeze(['entity', 'hotspot']);

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

function hotspotRefs(hotspots) {
    return (hotspots || []).flatMap((hotspot) => hotspot?.refs || []);
}

function createRelationSourceLoader(dependencies = {}) {
    const indexRepository = assertDedupIndexRetrievalRepository(dependencies.indexRepository);
    const questionRepository = assertDedupQuestionRetrievalRepository(dependencies.questionRepository);
    const hotspotRepository = dependencies.hotspotRepository == null
        ? null
        : assertDedupHotspotRetrievalRepository(dependencies.hotspotRepository);

    return async function loadRelationSource(candidate = {}) {
        const scope = String(candidate.scope || '').trim();
        if (!SUPPORTED_RELATION_SOURCE_SCOPES.includes(scope)) {
            throw new Error(`Unsupported relation source scope: ${scope || 'missing'}`);
        }

        let retrievalSnapshot;
        let refs;
        if (scope === 'entity') {
            const seed = String(candidate.seed || '').trim();
            if (!seed) throw new Error('entity relation source seed is required');
            retrievalSnapshot = assertSnapshot(
                await indexRepository.findEntityRefs(seed),
                'current dedup entity index',
                'refs',
            );
            if (!Array.isArray(retrievalSnapshot.refs)) {
                throw new Error('current dedup entity index refs must be an array');
            }
            refs = retrievalSnapshot.refs;
        } else {
            if (!hotspotRepository) {
                throw new Error('DedupHotspotRetrievalRepository is required for hotspot scope');
            }
            retrievalSnapshot = assertSnapshot(
                await hotspotRepository.listHotspots(),
                'current dedup hotspot index',
                'hotspots',
            );
            if (!Array.isArray(retrievalSnapshot.hotspots)) {
                throw new Error('current dedup hotspot index hotspots must be an array');
            }
            refs = hotspotRefs(retrievalSnapshot.hotspots);
        }

        const questionSnapshot = assertSnapshot(
            await questionRepository.findByRefs(refs),
            'current dedup questions',
            'questions',
        );
        if (!Array.isArray(questionSnapshot.questions)) {
            throw new Error('current dedup question snapshot questions must be an array');
        }

        return {
            scope,
            retrieval_snapshot: retrievalSnapshot,
            question_snapshot: questionSnapshot,
            current_source_revisions: [
                revisionOf(retrievalSnapshot),
                revisionOf(questionSnapshot),
            ],
        };
    };
}

module.exports = {
    SUPPORTED_RELATION_SOURCE_SCOPES,
    hotspotRefs,
    createRelationSourceLoader,
};
