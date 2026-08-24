'use strict';

const { detectEntityQuestionClusters } = require('../../domain/dedup/entity-cluster-detection');
const { detectHotspotQuestionClusters } = require('../../domain/dedup/hotspot-cluster-detection');
const { detectExplicitQuestionPair } = require('../../domain/dedup/explicit-question-pair-detection');
const { createRelationCandidate } = require('../../domain/dedup/relation-candidate');
const { validateDomain, normalizeEntity } = require('../../domain/question/taxonomy-normalization');
const {
    assertDedupIndexRetrievalRepository,
} = require('../../ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupHotspotRetrievalRepository,
} = require('../../ports/repositories/dedup-hotspot-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../../ports/repositories/dedup-question-retrieval-repository');
const {
    assertDedupQuestionSelectionRepository,
} = require('../../ports/repositories/dedup-question-selection-repository');
const { assertRelationCandidatePublisher } = require('../../ports/relation-candidate-publisher');
const { hotspotRefs } = require('./relation-source-retrieval');

function normalizeDetectionQuestion(question, taxonomy) {
    if (!question || typeof question !== 'object' || Array.isArray(question)) {
        throw new Error('Suggestion question is required');
    }
    const domainResult = validateDomain(question.domain || {}, taxonomy);
    const domain = domainResult.valid
        ? domainResult.normalized_domain
        : (question.domain || { l1: '其他', l2: '其他' });

    return {
        ...structuredClone(question),
        domain_key: `${domain.l1}/${domain.l2}`,
    };
}

function compareCandidates(left, right) {
    return right.member_count - left.member_count
        || right.distinct_source_count - left.distinct_source_count
        || right.question_ids.length - left.question_ids.length
        || String(left.anchor_question_id).localeCompare(String(right.anchor_question_id));
}

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

function sourceRevision(snapshot) {
    return {
        resource: snapshot.resource,
        revision: snapshot.revision,
    };
}

function normalizeQuestionIds(questionIds) {
    return [...new Set((questionIds || [])
        .map((questionId) => String(questionId || '').trim())
        .filter(Boolean))]
        .sort((left, right) => left.localeCompare(right));
}

function normalizeSuggestionInput(input, taxonomy) {
    const mode = input.mode || 'entity';
    if (mode === 'entity') {
        const rawSeed = String(input.seed || '').trim();
        if (!rawSeed) throw new Error('entity suggestion seed is required');
        const seed = normalizeEntity(rawSeed, taxonomy) || rawSeed;
        const limit = Number(input.limit ?? 50);
        if (!Number.isInteger(limit) || limit < 0) {
            throw new Error(`Invalid suggestion limit: ${input.limit}`);
        }
        return { mode, seed, limit };
    }

    if (mode === 'hotspot') {
        const limit = Number(input.limit ?? 100);
        if (!Number.isInteger(limit) || limit < 0) {
            throw new Error(`Invalid suggestion limit: ${input.limit}`);
        }
        return { mode, seed: 'hotspot', limit };
    }

    if (mode === 'pair') {
        const questionIds = normalizeQuestionIds(input.question_ids);
        if (questionIds.length !== 2) {
            throw new Error('pair suggestion requires exactly two distinct question_ids');
        }
        return {
            mode,
            seed: questionIds.join(','),
            limit: 1,
            question_ids: questionIds,
        };
    }

    throw new Error(`Unsupported dedup suggestion mode: ${mode}`);
}

/**
 * Pure planning core. It receives already retrieved Question/index facts and
 * returns pending RelationCandidates only; it performs no persistence or
 * retrieval.
 */
function planRelationSuggestions(input, dependencies = {}) {
    const taxonomy = dependencies.taxonomy;
    const entityDetector = dependencies.detectEntityQuestionClusters || detectEntityQuestionClusters;
    const hotspotDetector = dependencies.detectHotspotQuestionClusters || detectHotspotQuestionClusters;
    const pairDetector = dependencies.detectExplicitQuestionPair || detectExplicitQuestionPair;
    const normalized = normalizeSuggestionInput(input, taxonomy);
    const { mode, seed, limit } = normalized;

    if (!Array.isArray(input.questions)) {
        throw new Error('suggestion questions must be an array');
    }
    const detectionQuestions = input.questions.map(
        (question) => normalizeDetectionQuestion(question, taxonomy),
    );

    let clusters;
    if (mode === 'entity') {
        if (typeof entityDetector !== 'function') {
            throw new Error('detectEntityQuestionClusters dependency is required');
        }
        clusters = entityDetector(detectionQuestions, {
            ...(input.similarity_threshold == null
                ? {}
                : { similarity_threshold: input.similarity_threshold }),
        });
    } else if (mode === 'hotspot') {
        if (typeof hotspotDetector !== 'function') {
            throw new Error('detectHotspotQuestionClusters dependency is required');
        }
        if (!Array.isArray(input.hotspots)) {
            throw new Error('hotspot suggestion facts must be an array');
        }
        clusters = hotspotDetector(input.hotspots, detectionQuestions);
    } else {
        if (typeof pairDetector !== 'function') {
            throw new Error('detectExplicitQuestionPair dependency is required');
        }
        clusters = pairDetector(detectionQuestions, {
            question_ids: normalized.question_ids,
        });
    }

    if (!Array.isArray(clusters)) {
        throw new Error('Dedup detector must return an array');
    }

    const projectedCandidates = clusters.map((cluster) => createRelationCandidate({
        scope: mode,
        seed,
        cluster,
    }));
    const allCandidates = mode === 'entity'
        ? projectedCandidates.sort(compareCandidates)
        : projectedCandidates;
    const relationCandidates = allCandidates.slice(0, limit);

    return {
        schema_version: 'dedup_relation_suggestions.v1',
        mode,
        seed,
        detection_count: clusters.length,
        candidate_count: relationCandidates.length,
        relation_candidates: relationCandidates,
    };
}

function createSuggestCanonicalRelationsUseCase(dependencies = {}) {
    const taxonomy = dependencies.taxonomy;
    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }

    const indexRepository = assertDedupIndexRetrievalRepository(dependencies.indexRepository);
    const hotspotRepository = dependencies.hotspotRepository == null
        ? null
        : assertDedupHotspotRetrievalRepository(dependencies.hotspotRepository);
    const questionRepository = assertDedupQuestionRetrievalRepository(dependencies.questionRepository);
    const questionSelectionRepository = dependencies.questionSelectionRepository == null
        ? null
        : assertDedupQuestionSelectionRepository(dependencies.questionSelectionRepository);
    const relationCandidatePublisher = assertRelationCandidatePublisher(dependencies.relationCandidatePublisher);
    const entityDetector = dependencies.detectEntityQuestionClusters || detectEntityQuestionClusters;
    const hotspotDetector = dependencies.detectHotspotQuestionClusters || detectHotspotQuestionClusters;
    const pairDetector = dependencies.detectExplicitQuestionPair || detectExplicitQuestionPair;

    return async function suggestCanonicalRelationsUseCase(input = {}) {
        if (Object.hasOwn(input, 'questions') || Object.hasOwn(input, 'hotspots')) {
            throw new Error('suggestion source facts must be retrieved through Dedup repositories');
        }

        const normalized = normalizeSuggestionInput(input, taxonomy);
        let retrievalSnapshot;
        let questionSnapshot;
        let refs;
        let hotspots;

        if (normalized.mode === 'pair') {
            if (!questionSelectionRepository) {
                throw new Error('DedupQuestionSelectionRepository is required for pair suggestions');
            }
            questionSnapshot = assertSnapshot(
                await questionSelectionRepository.findByQuestionIds(normalized.question_ids),
                'dedup selected questions',
                'questions',
            );
            if (!Array.isArray(questionSnapshot.questions)) {
                throw new Error('dedup selected question snapshot questions must be an array');
            }
        } else {
            if (normalized.mode === 'entity') {
                retrievalSnapshot = assertSnapshot(
                    await indexRepository.findEntityRefs(normalized.seed),
                    'dedup entity index',
                    'refs',
                );
                if (!Array.isArray(retrievalSnapshot.refs)) {
                    throw new Error('dedup entity index snapshot refs must be an array');
                }
                refs = retrievalSnapshot.refs;
            } else {
                if (!hotspotRepository) {
                    throw new Error('DedupHotspotRetrievalRepository is required for hotspot suggestions');
                }
                retrievalSnapshot = assertSnapshot(
                    await hotspotRepository.listHotspots(),
                    'dedup hotspot index',
                    'hotspots',
                );
                if (!Array.isArray(retrievalSnapshot.hotspots)) {
                    throw new Error('dedup hotspot index snapshot hotspots must be an array');
                }
                hotspots = retrievalSnapshot.hotspots;
                refs = hotspotRefs(hotspots);
            }

            questionSnapshot = assertSnapshot(
                await questionRepository.findByRefs(refs),
                'dedup questions',
                'questions',
            );
            if (!Array.isArray(questionSnapshot.questions)) {
                throw new Error('dedup question snapshot questions must be an array');
            }
        }

        const planned = planRelationSuggestions({
            ...input,
            mode: normalized.mode,
            seed: normalized.seed,
            limit: normalized.limit,
            ...(normalized.question_ids ? { question_ids: normalized.question_ids } : {}),
            questions: questionSnapshot.questions,
            ...(normalized.mode === 'hotspot' ? { hotspots } : {}),
        }, {
            taxonomy,
            detectEntityQuestionClusters: entityDetector,
            detectHotspotQuestionClusters: hotspotDetector,
            detectExplicitQuestionPair: pairDetector,
        });
        const sourceRevisions = normalized.mode === 'pair'
            ? [sourceRevision(questionSnapshot)]
            : [sourceRevision(retrievalSnapshot), sourceRevision(questionSnapshot)];
        const queue = {
            schema_version: 'dedup_relation_candidate_queue.v1',
            mode: planned.mode,
            seed: planned.seed,
            source_revisions: sourceRevisions,
            detection_count: planned.detection_count,
            candidate_count: planned.candidate_count,
            relation_candidates: planned.relation_candidates,
        };
        const storedQueue = await relationCandidatePublisher.replaceQueue(queue);
        assertSnapshot(storedQueue, 'relation candidate queue', 'candidate_count');
        if (Number(storedQueue.candidate_count) !== planned.candidate_count) {
            throw new Error('relation candidate queue candidate_count mismatch');
        }

        return {
            ...planned,
            source_revisions: sourceRevisions,
            queue: {
                resource: storedQueue.resource,
                revision: storedQueue.revision,
                candidate_count: storedQueue.candidate_count,
            },
        };
    };
}

module.exports = {
    createSuggestCanonicalRelationsUseCase,
    normalizeDetectionQuestion,
    normalizeSuggestionInput,
    planRelationSuggestions,
};
