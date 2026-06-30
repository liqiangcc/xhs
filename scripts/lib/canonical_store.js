'use strict';

const crypto = require('crypto');
const path = require('path');
const { readJsonl, writeJsonl } = require('./io');

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
    const questionIds = [...new Set(candidate.question_ids || [])].sort();
    const companies = [...new Set(candidate.companies || [])].sort((a, b) => a.localeCompare(b, 'zh'));
    const aliases = [...new Set(candidate.aliases || [candidate.canonical_title].filter(Boolean))]
        .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh'));
    return {
        canonical_id: canonicalId,
        canonical_title: overrides.title || candidate.canonical_title,
        aliases,
        question_ids: questionIds,
        primary_domain: candidate.primary_domain || { l1: '其他', l2: '其他' },
        primary_entities: [...new Set(candidate.primary_entities || [])].sort((a, b) => a.localeCompare(b, 'zh')),
        companies,
        frequency: Number(candidate.frequency || questionIds.length),
        review_priority: candidate.review_priority || 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

function mergeCanonicalRecord(existing, incoming) {
    return {
        ...existing,
        canonical_title: existing.canonical_title || incoming.canonical_title,
        aliases: [...new Set([...(existing.aliases || []), ...(incoming.aliases || [])])]
            .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh')),
        question_ids: [...new Set([...(existing.question_ids || []), ...(incoming.question_ids || [])])].sort(),
        primary_entities: [...new Set([...(existing.primary_entities || []), ...(incoming.primary_entities || [])])]
            .sort((a, b) => a.localeCompare(b, 'zh')),
        companies: [...new Set([...(existing.companies || []), ...(incoming.companies || [])])]
            .sort((a, b) => a.localeCompare(b, 'zh')),
        frequency: Math.max(Number(existing.frequency || 0), Number(incoming.frequency || 0)),
        answer_status: existing.answer_status || incoming.answer_status || 'missing',
        schema_version: 'canonical_question.v1',
    };
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
