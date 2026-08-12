'use strict';

const crypto = require('crypto');
const path = require('path');
const { readJsonl, writeJsonl } = require('./io');
const {
    makeCanonicalFromCandidate,
    extendCanonicalWithCandidate,
} = require('../../src/domain/canonical/accept-policy');

const DEFAULT_CANONICAL_PATH = path.resolve(__dirname, '..', '..', 'data', 'questions', 'canonical_questions.jsonl');

function loadCanonicalQuestions(options = {}) {
    return readJsonl(options.filePath || DEFAULT_CANONICAL_PATH, []);
}

function saveCanonicalQuestions(records, options = {}) {
    const filePath = options.filePath || DEFAULT_CANONICAL_PATH;
    const sorted = [...records].sort((a, b) => a.canonical_id.localeCompare(b.canonical_id));
    writeJsonl(filePath, sorted);
}

function findCanonicalById(canonicalId, options = {}) {
    const records = options.records || loadCanonicalQuestions(options);
    return records.find((record) => record.canonical_id === canonicalId) || null;
}

function normalizeIdPart(value) {
    const normalized = String(value || '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_+|_+$/g, '')
        .replace(/_+/g, '_');
    return normalized || 'topic';
}

function shortHash(value, length = 8) {
    return crypto.createHash('md5').update(String(value), 'utf8').digest('hex').slice(0, length);
}

function suggestCanonicalId(seed, questionIds = []) {
    const base = normalizeIdPart(seed);
    const suffix = shortHash([...questionIds].sort().join('|') || seed);
    return `cq_${base}_${suffix}`;
}

function makeCanonicalRecord(candidate, canonicalId, overrides = {}) {
    return makeCanonicalFromCandidate(candidate, canonicalId, overrides);
}

function mergeCanonicalRecord(existing, incoming) {
    return extendCanonicalWithCandidate(existing, incoming);
}

function buildQuestionToCanonicalMap(records) {
    const map = new Map();
    for (const record of records) {
        for (const questionId of record.question_ids || []) {
            map.set(questionId, record.canonical_id);
        }
    }
    return map;
}

module.exports = {
    DEFAULT_CANONICAL_PATH,
    loadCanonicalQuestions,
    saveCanonicalQuestions,
    findCanonicalById,
    suggestCanonicalId,
    makeCanonicalRecord,
    mergeCanonicalRecord,
    buildQuestionToCanonicalMap,
    shortHash,
};
