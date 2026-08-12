'use strict';

const { detectEntityQuestionClusters } = require('../../domain/dedup/entity-cluster-detection');
const { createRelationCandidate } = require('../../domain/dedup/relation-candidate');
const { validateDomain, normalizeEntity } = require('../../domain/question/taxonomy-normalization');
const {
    assertDedupIndexRetrievalRepository,
} = require('../../ports/repositories/dedup-index-retrieval-repository');
const {
    assertDedupQuestionRetrievalRepository,
} = require('../../ports/repositories/dedup-question-retrieval-repository');
const { assertRelationCandidateStore } = require('../../ports/relation-candidate-store');

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

function normalizeSuggestionInput(input, taxonomy) {
    const mode = input.mode || 'entity';
    if (mode !== 'entity') {
        throw new Error(`Unsupported dedup suggestion mode: ${mode}`);
    }

    const rawSeed = String(input.seed || '').trim();
    if (!rawSeed) throw new Error('entity suggestion seed is required');
    const seed = normalizeEntity(rawSeed, taxonomy) || rawSeed;

    const limit = Number(input.limit ?? 50);
    if (!Number.isInteger(limit) || limit < 0) {
        throw new Error(`Invalid suggestion limit: ${input.limit}`);
    }

    return { mode, seed, limit };
}

/**
 * Pure planning core. It receives already retrieved Question facts and returns
 * pending RelationCandidates only; it performs no persistence or retrieval.
 */
function planRelationSuggestions(input, dependencies = {}) {
    const taxonomy = dependencies.taxonomy;
    const detector = dependencies.detectEntityQuestionClusters || detectEntityQuestionClusters;
    const { mode, seed, limit } = normalizeSuggestionInput(input, taxonomy);

    if (!Array.isArray(input.questions)) {
        throw new Error('suggestion questions must be an array');
    }
    if (typeof detector !== 'function') {
        throw new Error('detectEntityQuestionClusters dependency is required');
    }

    const detectionQuestions = input.questions.map(
        (question) => normalizeDetectionQuestion(question, taxonomy),
    );
    const clusters = detector(detectionQuestions, {
        ...(input.similarity_threshold == null
            ? {}
            : { similarity_threshold: input.similarity_threshold }),
    });
    if (!Array.isArray(clusters)) {
        throw new Error('Dedup detector must return an array');
    }

    const allCandidates = clusters
        .map((cluster) => createRelationCandidate({
            scope: mode,
            seed,
            cluster,
        }))
        .sort(compareCandidates);
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
    const questionRepository = assertDedupQuestionRetrievalRepository(dependencies.questionRepository);
    const relationCandidateStore = assertRelationCandidateStore(dependencies.relationCandidateStore);
    const detector = dependencies.detectEntityQuestionClusters || detectEntityQuestionClusters;

    return async function suggestCanonicalRelationsUseCase(input = {}) {
        if (Object.hasOwn(input, 'questions')) {
            throw new Error('suggestion questions must be retrieved through DedupQuestionRetrievalRepository');
        }

        const normalized = normalizeSuggestionInput(input, taxonomy);
        const indexSnapshot = assertSnapshot(
            await indexRepository.findEntityRefs(normalized.seed),
            'dedup entity index',
            'refs',
        );
        if (!Array.isArray(indexSnapshot.refs)) {
            throw new Error('dedup entity index snapshot refs must be an array');
        }

        const questionSnapshot = assertSnapshot(
            await questionRepository.findByRefs(indexSnapshot.refs),
            'dedup questions',
            'questions',
        );
        if (!Array.isArray(questionSnapshot.questions)) {
            throw new Error('dedup question snapshot questions must be an array');
        }

        const planned = planRelationSuggestions({
            ...input,
            mode: normalized.mode,
            seed: normalized.seed,
            limit: normalized.limit,
            questions: questionSnapshot.questions,
        }, {
            taxonomy,
            detectEntityQuestionClusters: detector,
        });
        const sourceRevisions = [
            sourceRevision(indexSnapshot),
            sourceRevision(questionSnapshot),
        ];
        const queue = {
            schema_version: 'dedup_relation_candidate_queue.v1',
            mode: planned.mode,
            seed: planned.seed,
            source_revisions: sourceRevisions,
            detection_count: planned.detection_count,
            candidate_count: planned.candidate_count,
            relation_candidates: planned.relation_candidates,
        };
        const storedQueue = await relationCandidateStore.replaceQueue(queue);
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
    planRelationSuggestions,
};
