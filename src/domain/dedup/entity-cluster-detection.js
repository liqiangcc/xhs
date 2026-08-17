'use strict';

const { jaccardSimilarity, tokenizeSimilarityText } = require('./similarity');

function clone(value) {
    return structuredClone(value);
}

function sortedDetectionQuestions(questions) {
    return [...questions].sort((a, b) =>
        String(a.question_id || '').localeCompare(String(b.question_id || ''))
        || String(a.source_note_id || '').localeCompare(String(b.source_note_id || ''), 'zh')
        || Number(a.source_question_index ?? 0) - Number(b.source_question_index ?? 0)
    );
}

function assertDetectionQuestion(question) {
    if (!question || typeof question !== 'object') {
        throw new Error('Dedup detection question is required');
    }
    if (!question.question_id) throw new Error('Dedup detection question_id is required');
    if (typeof question.original_question !== 'string') {
        throw new Error(`Dedup detection original_question is required for ${question.question_id}`);
    }
    if (!question.domain_key) {
        throw new Error(`Dedup detection domain_key is required for ${question.question_id}`);
    }
}

function memberRef(question) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
    };
}

/**
 * Detect groups of unassigned library questions that exhibit duplicate-like
 * signals inside an entity-scoped retrieval set.
 *
 * Input questions must already carry a normalized `domain_key`. Taxonomy
 * normalization and retrieval belong outside this Domain policy.
 *
 * The result is detection evidence only. It intentionally contains no
 * Canonical ID assignment, candidate ID, relation decision, or mutation plan.
 */
function detectEntityQuestionClusters(questions, options = {}) {
    if (!Array.isArray(questions)) throw new Error('Dedup detection questions must be an array');
    const threshold = Number(options.similarity_threshold ?? 0.38);
    if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
        throw new Error(`Invalid similarity threshold: ${options.similarity_threshold}`);
    }

    const eligible = sortedDetectionQuestions(
        questions.filter((question) => question?.is_valid_for_library && !question?.canonical_id),
    );
    eligible.forEach(assertDetectionQuestion);

    const clusters = [];
    for (const question of eligible) {
        const questionTokens = tokenizeSimilarityText(question.original_question);
        let target = null;
        let evidence = null;

        for (const cluster of clusters) {
            const sameQuestionId = question.question_id === cluster.anchor_question_id;
            if (cluster.domain_key !== question.domain_key && !sameQuestionId) continue;

            if (sameQuestionId) {
                target = cluster;
                evidence = {
                    signal: 'same_question_id',
                    left_question_id: cluster.anchor_question_id,
                    right_question_id: question.question_id,
                    matched: true,
                };
                break;
            }

            const score = jaccardSimilarity(cluster.anchor_tokens, questionTokens);
            if (score >= threshold) {
                target = cluster;
                evidence = {
                    signal: 'jaccard',
                    left_question_id: cluster.anchor_question_id,
                    right_question_id: question.question_id,
                    score,
                    threshold,
                    matched: true,
                };
                break;
            }
        }

        if (!target) {
            clusters.push({
                domain_key: question.domain_key,
                anchor_question_id: question.question_id,
                anchor_tokens: questionTokens,
                question_ids: [question.question_id],
                members: [memberRef(question)],
                source_note_ids: [question.source_note_id],
                evidence: [],
            });
            continue;
        }

        target.members.push(memberRef(question));
        if (!target.question_ids.includes(question.question_id)) {
            target.question_ids.push(question.question_id);
        }
        if (!target.source_note_ids.includes(question.source_note_id)) {
            target.source_note_ids.push(question.source_note_id);
        }
        target.evidence.push(evidence);
    }

    return clusters
        .filter((cluster) =>
            cluster.members.length >= 2
            && (cluster.question_ids.length >= 2 || cluster.source_note_ids.length >= 2)
        )
        .map((cluster) => Object.freeze({
            domain_key: cluster.domain_key,
            anchor_question_id: cluster.anchor_question_id,
            question_ids: [...cluster.question_ids].sort((a, b) => String(a).localeCompare(String(b))),
            member_count: cluster.members.length,
            distinct_source_count: cluster.source_note_ids.length,
            members: cluster.members.map(clone),
            evidence: cluster.evidence.map(clone),
        }));
}

module.exports = {
    detectEntityQuestionClusters,
    sortedDetectionQuestions,
};
