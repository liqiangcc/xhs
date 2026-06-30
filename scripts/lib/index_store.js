'use strict';

const fs = require('fs');
const path = require('path');
const { normalizeEntity } = require('./taxonomy');
const { questionRef, refKey } = require('./question_store');
const { readJson, writeJson, stablePrettyStringify } = require('./io');
const { loadCanonicalQuestions } = require('./canonical_store');

const DEFAULT_INDEX_DIR = path.resolve(__dirname, '..', '..', 'data', 'indexes');

function getIndexPaths(indexDir = DEFAULT_INDEX_DIR) {
    return {
        entity: path.join(indexDir, 'entity_index.json'),
        company: path.join(indexDir, 'company_index.json'),
        domain: path.join(indexDir, 'domain_index.json'),
        hotspot: path.join(indexDir, 'hotspot_index.json'),
    };
}

function createBucket() {
    return {
        count: 0,
        valid_count: 0,
        invalid_count: 0,
        question_ids: [],
        companies: [],
        refs: [],
    };
}

function addToBucket(bucket, question) {
    const ref = questionRef(question);
    const key = refKey(ref);
    if (!bucket.__seenRefs) bucket.__seenRefs = new Set();
    if (!bucket.__seenRefs.has(key)) {
        bucket.__seenRefs.add(key);
        bucket.refs.push(ref);
        bucket.count++;
        if (question.is_valid_for_library) bucket.valid_count++;
        else bucket.invalid_count++;
    }
    if (!bucket.__seenQuestionIds) bucket.__seenQuestionIds = new Set(bucket.question_ids);
    if (!bucket.__seenQuestionIds.has(question.question_id)) {
        bucket.__seenQuestionIds.add(question.question_id);
        bucket.question_ids.push(question.question_id);
    }
    const company = String(question.company || '未知');
    if (!bucket.__seenCompanies) bucket.__seenCompanies = new Set(bucket.companies);
    if (!bucket.__seenCompanies.has(company)) {
        bucket.__seenCompanies.add(company);
        bucket.companies.push(company);
    }
}

function finalizeBucket(bucket) {
    delete bucket.__seenRefs;
    delete bucket.__seenQuestionIds;
    delete bucket.__seenCompanies;
    bucket.question_ids.sort();
    bucket.companies.sort((a, b) => a.localeCompare(b, 'zh'));
    bucket.refs.sort((a, b) =>
        a.question_id.localeCompare(b.question_id)
        || a.source_note_id.localeCompare(b.source_note_id, 'zh')
        || (a.source_question_index ?? 0) - (b.source_question_index ?? 0)
    );
    return bucket;
}

function addEntry(entries, key, question) {
    if (!key) return;
    if (!entries[key]) entries[key] = createBucket();
    addToBucket(entries[key], question);
}

function finalizeEntries(entries) {
    const out = {};
    for (const key of Object.keys(entries).sort((a, b) => a.localeCompare(b, 'zh'))) {
        out[key] = finalizeBucket(entries[key]);
    }
    return out;
}

function baseIndex(schemaVersion, questions) {
    return {
        schema_version: schemaVersion,
        source: 'data/questions/questions.jsonl',
        question_count: questions.length,
    };
}

function buildIndexes(questions, options = {}) {
    const canonicalRecords = options.canonicalQuestions || loadCanonicalQuestions(options);
    const canonicalById = new Map(canonicalRecords.map((record) => [record.canonical_id, record]));
    const entityEntries = {};
    const companyEntries = {};
    const domainL1Entries = {};
    const domainL2Entries = {};
    const byHotspotKey = {};

    for (const question of questions) {
        const entities = new Set((question.tech_entities || []).map((entity) => normalizeEntity(entity)).filter(Boolean));
        for (const entity of entities) addEntry(entityEntries, entity, question);

        addEntry(companyEntries, String(question.company || '未知'), question);

        const l1 = String(question.domain?.l1 || '其他');
        const l2 = String(question.domain?.l2 || '其他');
        addEntry(domainL1Entries, l1, question);
        addEntry(domainL2Entries, `${l1}/${l2}`, question);

        const canonical = question.canonical_id ? canonicalById.get(question.canonical_id) : null;
        const hotspotKey = question.canonical_id ? `canonical:${question.canonical_id}` : `question:${question.question_id}`;
        if (!byHotspotKey[hotspotKey]) {
            byHotspotKey[hotspotKey] = {
                canonical_id: question.canonical_id || null,
                question_id: question.question_id,
                question_ids: new Set(),
                original_question: canonical?.canonical_title || question.original_question,
                domain: question.domain || { l1: '', l2: '' },
                question_type: question.question_type || '',
                cognitive_depth: question.cognitive_depth || '',
                refs_bucket: createBucket(),
            };
        }
        byHotspotKey[hotspotKey].question_ids.add(question.question_id);
        addToBucket(byHotspotKey[hotspotKey].refs_bucket, question);
    }

    const hotspotEntries = Object.values(byHotspotKey)
        .map((item) => {
            const bucket = finalizeBucket(item.refs_bucket);
            return {
                canonical_id: item.canonical_id,
                question_id: item.question_id,
                question_ids: [...item.question_ids].sort(),
                original_question: item.original_question,
                frequency: bucket.count,
                valid_count: bucket.valid_count,
                invalid_count: bucket.invalid_count,
                companies: bucket.companies,
                source_note_ids: [...new Set(bucket.refs.map((ref) => ref.source_note_id))].sort((a, b) => a.localeCompare(b, 'zh')),
                refs: bucket.refs,
                domain: item.domain,
                question_type: item.question_type,
                cognitive_depth: item.cognitive_depth,
            };
        })
        .filter((item) => item.frequency >= 2)
        .sort((a, b) =>
            b.frequency - a.frequency
            || b.companies.length - a.companies.length
            || a.question_id.localeCompare(b.question_id)
        );

    return {
        entity: {
            ...baseIndex('entity_index.v1', questions),
            total_keys: Object.keys(entityEntries).length,
            entries: finalizeEntries(entityEntries),
        },
        company: {
            ...baseIndex('company_index.v1', questions),
            total_keys: Object.keys(companyEntries).length,
            entries: finalizeEntries(companyEntries),
        },
        domain: {
            ...baseIndex('domain_index.v1', questions),
            total_l1_keys: Object.keys(domainL1Entries).length,
            total_l2_keys: Object.keys(domainL2Entries).length,
            l1: finalizeEntries(domainL1Entries),
            l2: finalizeEntries(domainL2Entries),
        },
        hotspot: {
            ...baseIndex('hotspot_index.v1', questions),
            total_hotspots: hotspotEntries.length,
            entries: hotspotEntries,
        },
    };
}

function writeIndexes(indexes, indexDir = DEFAULT_INDEX_DIR) {
    const paths = getIndexPaths(indexDir);
    writeJson(paths.entity, indexes.entity);
    writeJson(paths.company, indexes.company);
    writeJson(paths.domain, indexes.domain);
    writeJson(paths.hotspot, indexes.hotspot);
    return paths;
}

function loadIndexes(indexDir = DEFAULT_INDEX_DIR) {
    const paths = getIndexPaths(indexDir);
    return {
        entity: readJson(paths.entity),
        company: readJson(paths.company),
        domain: readJson(paths.domain),
        hotspot: readJson(paths.hotspot),
    };
}

function checkIndexes(indexes, indexDir = DEFAULT_INDEX_DIR) {
    const paths = getIndexPaths(indexDir);
    const pairs = [
        ['entity', paths.entity],
        ['company', paths.company],
        ['domain', paths.domain],
        ['hotspot', paths.hotspot],
    ];
    const diffs = [];
    for (const [key, filePath] of pairs) {
        const actual = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : null;
        const expected = stablePrettyStringify(indexes[key]);
        if (actual !== expected) diffs.push(filePath);
    }
    return {
        ok: diffs.length === 0,
        diffs,
    };
}

module.exports = {
    DEFAULT_INDEX_DIR,
    getIndexPaths,
    buildIndexes,
    writeIndexes,
    loadIndexes,
    checkIndexes,
};
