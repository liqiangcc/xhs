'use strict';

const fs = require('fs');
const path = require('path');
const { readJson, writeJson, ensureDir } = require('./io');
const { defaultDate } = require('./date');

const DEFAULT_REVIEW_DIR = path.resolve(__dirname, '..', '..', 'review');
const DEFAULT_PROGRESS_PATH = path.join(DEFAULT_REVIEW_DIR, 'progress.json');

function todayString(options = {}) {
    return defaultDate(options);
}

function addDays(dateString, days) {
    const date = new Date(`${dateString}T00:00:00Z`);
    date.setUTCDate(date.getUTCDate() + days);
    return date.toISOString().slice(0, 10);
}

function loadProgress(options = {}) {
    const filePath = options.progressPath || DEFAULT_PROGRESS_PATH;
    return readJson(filePath, {
        schema_version: 'review_progress_store.v1',
        updated_at: todayString(options),
        items: [],
    });
}

function saveProgress(progress, options = {}) {
    const filePath = options.progressPath || DEFAULT_PROGRESS_PATH;
    const sorted = {
        schema_version: 'review_progress_store.v1',
        updated_at: todayString(options),
        items: [...(progress.items || [])].sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)),
    };
    writeJson(filePath, sorted);
    return sorted;
}

function defaultProgressItem(canonicalId, options = {}) {
    const date = todayString(options);
    return {
        canonical_id: canonicalId,
        status: 'new',
        level: 0,
        review_count: 0,
        last_reviewed_at: null,
        next_review_at: date,
        confidence: 0.5,
        difficulty: 3,
        mistake_count: 0,
        updated_at: date,
    };
}

function ensureProgressItems(progress, canonicalRecords, options = {}) {
    const byId = new Map((progress.items || []).map((item) => [item.canonical_id, item]));
    for (const record of canonicalRecords) {
        if (!byId.has(record.canonical_id)) {
            byId.set(record.canonical_id, defaultProgressItem(record.canonical_id, options));
        }
    }
    return {
        ...progress,
        updated_at: todayString(options),
        items: [...byId.values()],
    };
}

function progressMap(progress) {
    return new Map((progress.items || []).map((item) => [item.canonical_id, item]));
}

function isDue(item, date) {
    return !item.next_review_at || item.next_review_at <= date;
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function applyReviewResult(item, result, options = {}) {
    const date = todayString(options);
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
    } else if (result === 'easy') {
        level = clamp(beforeLevel + 2, 0, 5);
        nextReviewAt = addDays(date, easyIntervals[Math.min(beforeLevel, easyIntervals.length - 1)]);
        confidence = clamp(confidence + 0.25, 0, 1);
        difficulty = clamp(difficulty - 1, 1, 5);
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

function appendSessionEvent(event, options = {}) {
    const reviewDir = options.reviewDir || DEFAULT_REVIEW_DIR;
    const date = todayString(options);
    const filePath = path.join(reviewDir, 'sessions', `${date}.json`);
    const session = readJson(filePath, {
        schema_version: 'review_session.v1',
        date,
        events: [],
    });
    session.events.push(event);
    session.events.sort((a, b) => a.canonical_id.localeCompare(b.canonical_id) || a.result.localeCompare(b.result));
    ensureDir(path.dirname(filePath));
    writeJson(filePath, session);
    return filePath;
}

module.exports = {
    DEFAULT_REVIEW_DIR,
    DEFAULT_PROGRESS_PATH,
    todayString,
    addDays,
    loadProgress,
    saveProgress,
    defaultProgressItem,
    ensureProgressItems,
    progressMap,
    isDue,
    applyReviewResult,
    appendSessionEvent,
};
