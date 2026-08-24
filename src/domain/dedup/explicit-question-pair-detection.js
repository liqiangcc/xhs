'use strict';

function clone(value) {
    return structuredClone(value);
}

function uniqueSorted(values) {
    return [...new Set((values || []).map((value) => String(value || '').trim()).filter(Boolean))]
        .sort((left, right) => left.localeCompare(right));
}

function compareMembers(left, right) {
    return String(left?.question_id || '').localeCompare(String(right?.question_id || ''))
        || String(left?.source_note_id || '').localeCompare(String(right?.source_note_id || ''), 'zh')
        || Number(left?.source_question_index ?? 0) - Number(right?.source_question_index ?? 0);
}

function memberRef(question) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
    };
}

/**
 * Build one review candidate from an explicitly selected Question pair.
 *
 * This policy deliberately performs no similarity scoring and infers no
 * semantic relation. It exists for source-first review of relationships that
 * involve already-canonicalized Questions, which the entity/hotspot discovery
 * policies intentionally exclude. The explicit selection is evidence that the
 * pair must be reviewed, not evidence that it is `same`/`alias`/`related`.
 */
function detectExplicitQuestionPair(questions, options = {}) {
    if (!Array.isArray(questions)) throw new Error('Explicit relation review questions must be an array');
    const requestedQuestionIds = uniqueSorted(options.question_ids);
    if (requestedQuestionIds.length !== 2) {
        throw new Error('Explicit relation review requires exactly two distinct question_ids');
    }

    const requested = new Set(requestedQuestionIds);
    const selected = questions
        .filter((question) => requested.has(String(question?.question_id || '')))
        .sort(compareMembers);

    for (const questionId of requestedQuestionIds) {
        const rows = selected.filter((question) => question.question_id === questionId);
        if (rows.length === 0) {
            throw new Error(`Explicit relation review Question not found: ${questionId}`);
        }
        if (rows.some((question) => question.is_valid_for_library !== true)) {
            throw new Error(`Explicit relation review Question is not reviewable: ${questionId}`);
        }
    }

    const sourceNoteIds = uniqueSorted(selected.map((question) => question.source_note_id));
    return [Object.freeze({
        anchor_question_id: requestedQuestionIds[0],
        question_ids: requestedQuestionIds,
        member_count: selected.length,
        distinct_source_count: sourceNoteIds.length,
        members: selected.map(memberRef),
        evidence: [{
            signal: 'explicit_review_selection',
            question_ids: [...requestedQuestionIds],
            relation_inference: 'none',
        }].map(clone),
    })];
}

module.exports = {
    detectExplicitQuestionPair,
};
