'use strict';

const { computePriority } = require('./priority-policy');

function assertCanonicalRecord(record) {
    if (!record || typeof record !== 'object') {
        throw new Error('source canonical is required');
    }
    if (!record.canonical_id) {
        throw new Error('source canonical_id is required');
    }
}

function assertSplitCanonical(source, questionId, newCanonicalId, title) {
    assertCanonicalRecord(source);
    if (!questionId) throw new Error('question_id is required');
    if (!newCanonicalId) throw new Error('new canonical_id is required');
    if (!title) throw new Error('canonical title is required');
    if (source.canonical_id === newCanonicalId) {
        throw new Error('new-canonical-id must differ from canonical-id');
    }
    if (!(source.question_ids || []).includes(questionId)) {
        throw new Error(`Question ${questionId} is not part of ${source.canonical_id}`);
    }
}

function unique(values) {
    return [...new Set((values || []).filter((value) => value !== undefined && value !== null))];
}

/**
 * Build the pure in-memory Canonical result of splitting one question from a
 * source Canonical into a new Canonical.
 *
 * `questionFacts` must already be normalized by the caller. Domain deliberately
 * does not know how Question rows are loaded, how taxonomy values are
 * normalized, or how the result is persisted.
 */
function splitCanonical(source, options = {}) {
    const {
        questionId,
        newCanonicalId,
        title,
        questionFacts = {},
    } = options;

    assertSplitCanonical(source, questionId, newCanonicalId, title);

    const remainingQuestionIds = (source.question_ids || []).filter((id) => id !== questionId);
    const companies = unique(questionFacts.companies || [])
        .sort((a, b) => String(a).localeCompare(String(b), 'zh'));
    const frequency = Number(questionFacts.frequency || 0);

    const remainingSource = remainingQuestionIds.length
        ? {
            ...source,
            question_ids: remainingQuestionIds,
        }
        : null;

    const newCanonical = {
        canonical_id: newCanonicalId,
        canonical_title: title,
        aliases: unique([title, ...(questionFacts.aliases || [])]),
        question_ids: [questionId],
        primary_domain: questionFacts.primary_domain || { l1: '其他', l2: '其他' },
        primary_entities: unique(questionFacts.primary_entities || []),
        companies,
        frequency,
        review_priority: computePriority(frequency, companies.length),
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };

    return {
        remaining_source: remainingSource,
        new_canonical: newCanonical,
    };
}

module.exports = {
    assertSplitCanonical,
    splitCanonical,
};
