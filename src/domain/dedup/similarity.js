'use strict';

const { normalizeQuestionText } = require('../question/normalization-policy');

/**
 * Build the token signal historically used by Canonical entity suggestions.
 *
 * This is intentionally a pure similarity primitive. It does not decide a
 * relation and it never authorizes Canonical mutation.
 */
function tokenizeSimilarityText(text) {
    const normalized = normalizeQuestionText(text);
    const tokens = new Set();

    for (const word of normalized.match(/[a-z0-9_]+/g) || []) {
        if (word.length >= 2) tokens.add(word);
    }

    for (const chunk of normalized.match(/[\u4e00-\u9fa5]+/g) || []) {
        if (chunk.length === 1) tokens.add(chunk);
        for (let index = 0; index < chunk.length - 1; index += 1) {
            tokens.add(chunk.slice(index, index + 2));
        }
    }

    return tokens;
}

function jaccardSimilarity(leftTokens, rightTokens) {
    if (!(leftTokens instanceof Set) || !(rightTokens instanceof Set)) {
        throw new Error('Jaccard similarity requires token sets');
    }
    if (!leftTokens.size || !rightTokens.size) return 0;

    let intersection = 0;
    for (const token of leftTokens) {
        if (rightTokens.has(token)) intersection += 1;
    }
    return intersection / (leftTokens.size + rightTokens.size - intersection);
}

function measureQuestionSimilarity(leftText, rightText, options = {}) {
    const threshold = Number(options.threshold ?? 0.38);
    if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
        throw new Error(`Invalid similarity threshold: ${options.threshold}`);
    }

    const score = jaccardSimilarity(
        tokenizeSimilarityText(leftText),
        tokenizeSimilarityText(rightText),
    );

    return Object.freeze({
        metric: 'jaccard',
        score,
        threshold,
        matched: score >= threshold,
    });
}

module.exports = {
    tokenizeSimilarityText,
    jaccardSimilarity,
    measureQuestionSimilarity,
};
