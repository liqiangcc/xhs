'use strict';

const { addDays } = require('./progress-policy');

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function applyReviewResult(item, result, date) {
    if (!item || typeof item !== 'object') {
        throw new Error('Review progress item is required');
    }
    if (!date || typeof date !== 'string') {
        throw new Error('Review result date is required');
    }

    const goodIntervals = [1, 3, 7, 14, 30, 60];
    const easyIntervals = [3, 7, 14, 30, 60, 90];
    const beforeLevel = Number(item.level || 0);
    let level = beforeLevel;
    let nextReviewAt = date;
    let confidence = Number(item.confidence || 0);
    let difficulty = Number(item.difficulty || 3);
    let mistakeCount = Number(item.mistake_count || 0);

    if (result === 'again') {
        level = clamp(beforeLevel - 1, 0, 5);
        nextReviewAt = date;
        confidence = clamp(confidence - 0.2, 0, 1);
        difficulty = clamp(difficulty + 1, 1, 5);
        mistakeCount++;
    } else if (result === 'hard') {
        level = beforeLevel;
        nextReviewAt = addDays(date, 1);
        confidence = clamp(confidence - 0.1, 0, 1);
        difficulty = clamp(difficulty + 1, 1, 5);
        mistakeCount++;
    } else if (result === 'good') {
        level = clamp(beforeLevel + 1, 0, 5);
        nextReviewAt = addDays(date, goodIntervals[Math.min(beforeLevel, goodIntervals.length - 1)]);
        confidence = clamp(confidence + 0.15, 0, 1);
        mistakeCount = Math.max(0, mistakeCount - 1);
    } else if (result === 'easy') {
        level = clamp(beforeLevel + 2, 0, 5);
        nextReviewAt = addDays(date, easyIntervals[Math.min(beforeLevel, easyIntervals.length - 1)]);
        confidence = clamp(confidence + 0.25, 0, 1);
        difficulty = clamp(difficulty - 1, 1, 5);
        mistakeCount = Math.max(0, mistakeCount - 1);
    } else {
        throw new Error(`Invalid review result: ${result}`);
    }

    return {
        ...item,
        status: level >= 5 ? 'mastered' : (mistakeCount > 0 ? 'weak' : 'learning'),
        level,
        review_count: Number(item.review_count || 0) + 1,
        last_reviewed_at: date,
        next_review_at: nextReviewAt,
        confidence,
        difficulty,
        mistake_count: mistakeCount,
        updated_at: date,
    };
}

module.exports = {
    applyReviewResult,
};
