'use strict';

const fs = require('fs');
const path = require('path');
const { readJson, writeJson, ensureDir } = require('./io');
const { defaultDate } = require('./date');
const {
    addDays,
    defaultProgressItem: defaultProgressItemPolicy,
    ensureProgressItems: ensureProgressItemsPolicy,
    isDue,
} = require('../../src/domain/review/progress-policy');
const {
    applyReviewResult: applyReviewResultPolicy,
} = require('../../src/domain/review/review-result-policy');

const DEFAULT_REVIEW_DIR = path.resolve(__dirname, '..', '..', 'review');
const DEFAULT_PROGRESS_PATH = path.join(DEFAULT_REVIEW_DIR, 'progress.json');

function todayString(options = {}) {
    return defaultDate(options);
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
    return defaultProgressItemPolicy(canonicalId, todayString(options));
}

function ensureProgressItems(progress, canonicalRecords, options = {}) {
    return ensureProgressItemsPolicy(progress, canonicalRecords, todayString(options));
}

function progressMap(progress) {
    return new Map((progress.items || []).map((item) => [item.canonical_id, item]));
}

function applyReviewResult(item, result, options = {}) {
    return applyReviewResultPolicy(item, result, todayString(options));
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
