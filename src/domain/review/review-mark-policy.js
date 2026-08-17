'use strict';

function uniqueNonEmpty(values) {
    return [...new Set(values || [])].filter(Boolean);
}

function normalizeReviewMarkInput(input = {}) {
    const oralVersion = input.oral_version || null;
    if (oralVersion && oralVersion !== 'one_minute') {
        throw new Error('oral-version must be one_minute');
    }

    const qualityDefects = uniqueNonEmpty(input.quality_defects);
    const hardFailures = uniqueNonEmpty(input.hard_failures);
    const feedbackClosedAt = input.feedback_closed_at || null;
    if (feedbackClosedAt && !/^\d{4}-\d{2}-\d{2}$/.test(feedbackClosedAt)) {
        throw new Error('feedback-closed-at must use YYYY-MM-DD');
    }
    if (feedbackClosedAt && qualityDefects.length === 0) {
        throw new Error('feedback-closed-at requires at least one quality-defect');
    }

    return Object.freeze({
        oral_version: oralVersion,
        followup_answered: Boolean(input.followup_answered),
        quality_defects: Object.freeze(qualityDefects),
        hard_failures: Object.freeze(hardFailures),
        feedback_closed_at: feedbackClosedAt,
        notes: input.notes || '',
    });
}

function createReviewSessionEvent(input = {}) {
    if (!input.canonical_id) throw new Error('Review session event canonical_id is required');
    if (!input.result) throw new Error('Review session event result is required');
    if (!input.progress || typeof input.progress !== 'object') {
        throw new Error('Review session event progress is required');
    }
    if (!input.date) throw new Error('Review session event date is required');
    const mark = input.mark || normalizeReviewMarkInput();

    return Object.freeze({
        canonical_id: input.canonical_id,
        result: input.result,
        notes: mark.notes || '',
        reviewed_at: input.date,
        next_review_at: input.progress.next_review_at,
        oral_version: mark.oral_version,
        followup_answered: Boolean(mark.followup_answered),
        quality_defects: [...(mark.quality_defects || [])],
        hard_failures: [...(mark.hard_failures || [])],
        feedback_closed_at: mark.feedback_closed_at,
    });
}

module.exports = {
    normalizeReviewMarkInput,
    createReviewSessionEvent,
};
