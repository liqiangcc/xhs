'use strict';

const { detectEntityQuestionClusters } = require('../../domain/dedup/entity-cluster-detection');
const { createRelationCandidate } = require('../../domain/dedup/relation-candidate');
const { validateDomain } = require('../../domain/question/taxonomy-normalization');

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

function createSuggestCanonicalRelationsUseCase(dependencies = {}) {
    const taxonomy = dependencies.taxonomy;
    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }

    const detector = dependencies.detectEntityQuestionClusters || detectEntityQuestionClusters;
    if (typeof detector !== 'function') {
        throw new Error('detectEntityQuestionClusters dependency is required');
    }

    return async function suggestCanonicalRelationsUseCase(input = {}) {
        const mode = input.mode || 'entity';
        if (mode !== 'entity') {
            throw new Error(`Unsupported dedup suggestion mode: ${mode}`);
        }
        const seed = String(input.seed || '').trim();
        if (!seed) throw new Error('entity suggestion seed is required');
        if (!Array.isArray(input.questions)) {
            throw new Error('suggestion questions must be an array');
        }

        const limit = Number(input.limit ?? 50);
        if (!Number.isInteger(limit) || limit < 0) {
            throw new Error(`Invalid suggestion limit: ${input.limit}`);
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
    };
}

module.exports = {
    createSuggestCanonicalRelationsUseCase,
    normalizeDetectionQuestion,
};
