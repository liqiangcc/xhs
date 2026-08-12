'use strict';

const crypto = require('crypto');
const {
    readJson,
    readJsonl,
    stableStringify,
    writeJson,
} = require('../../../scripts/lib/io');
const { createDedupFsPaths } = require('./dedup-paths');

function clone(value) {
    return structuredClone(value);
}

function hashValue(value) {
    return crypto.createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function refKey(ref) {
    return [
        ref?.question_id,
        ref?.source_note_id,
        ref?.source_question_index ?? '',
    ].join('::');
}

function compareRefs(left, right) {
    return String(left?.question_id || '').localeCompare(String(right?.question_id || ''))
        || String(left?.source_note_id || '').localeCompare(String(right?.source_note_id || ''), 'zh')
        || Number(left?.source_question_index ?? 0) - Number(right?.source_question_index ?? 0);
}

function normalizeRefs(refs) {
    const byKey = new Map();
    for (const ref of refs || []) {
        if (!ref || !ref.question_id || !ref.source_note_id) continue;
        const normalized = {
            question_id: ref.question_id,
            source_note_id: ref.source_note_id,
            source_question_index: ref.source_question_index,
        };
        byKey.set(refKey(normalized), normalized);
    }
    return [...byKey.values()].sort(compareRefs);
}

function entityIndexResource(seed) {
    return `dedup-entity-index:${String(seed)}`;
}

function questionSnapshotResource(refs) {
    return `dedup-questions-by-refs:${hashValue(normalizeRefs(refs)).slice(0, 20)}`;
}

function relationQueueKey(mode, seed) {
    return `${String(mode)}|${String(seed)}`;
}

function relationQueueResource(mode, seed) {
    return `dedup-relation-queue:${String(mode)}:${String(seed)}`;
}

function readEntityIndex(paths) {
    return readJson(paths.entityIndex, {
        schema_version: 'entity_index.v1',
        entries: {},
    });
}

function matchingEntityRefs(paths, seed) {
    const index = readEntityIndex(paths);
    const normalizedSeed = String(seed || '');
    const lowerSeed = normalizedSeed.toLowerCase();
    const refs = [];
    for (const [key, bucket] of Object.entries(index.entries || {})) {
        if (key === normalizedSeed || key.toLowerCase().includes(lowerSeed)) {
            refs.push(...(bucket?.refs || []));
        }
    }
    return normalizeRefs(refs);
}

function readQuestions(paths) {
    return readJsonl(paths.questions, []);
}

function resolveQuestionsByRefs(paths, refs) {
    const normalizedRefs = normalizeRefs(refs);
    const requested = new Set(normalizedRefs.map(refKey));
    return readQuestions(paths)
        .filter((question) => requested.has(refKey(question)))
        .sort((left, right) => compareRefs(left, right))
        .map(clone);
}

function readQueueManifest(paths) {
    return readJson(paths.relationCandidateQueues, {
        schema_version: 'dedup_relation_candidate_queues.v1',
        queues: {},
    });
}

function createFsDedupSuggestionRepositories(options = {}) {
    if (!options.root) throw new Error('Filesystem dedup suggestion repository root is required');
    const paths = options.paths || createDedupFsPaths(options.root);

    const indexRepository = {
        async findEntityRefs(seed) {
            const refs = matchingEntityRefs(paths, seed);
            return {
                refs: refs.map(clone),
                resource: entityIndexResource(seed),
                revision: hashValue(refs),
            };
        },
    };

    const questionRepository = {
        async findByRefs(refs) {
            if (!Array.isArray(refs)) throw new Error('refs must be an array');
            const normalizedRefs = normalizeRefs(refs);
            const questions = resolveQuestionsByRefs(paths, normalizedRefs);
            return {
                questions,
                resource: questionSnapshotResource(normalizedRefs),
                revision: hashValue(questions),
            };
        },
    };

    const relationCandidateStore = {
        async replaceQueue(queue) {
            if (!queue || typeof queue !== 'object' || Array.isArray(queue)) {
                throw new Error('relation candidate queue is required');
            }
            if (!queue.mode || !queue.seed) {
                throw new Error('relation candidate queue mode and seed are required');
            }
            const manifest = readQueueManifest(paths);
            const key = relationQueueKey(queue.mode, queue.seed);
            const storedQueue = clone(queue);
            const next = {
                ...manifest,
                schema_version: 'dedup_relation_candidate_queues.v1',
                queues: {
                    ...(manifest.queues || {}),
                    [key]: storedQueue,
                },
            };
            writeJson(paths.relationCandidateQueues, next);
            return {
                resource: relationQueueResource(queue.mode, queue.seed),
                revision: hashValue(storedQueue),
                candidate_count: Number(storedQueue.candidate_count || 0),
            };
        },
    };

    return {
        indexRepository,
        questionRepository,
        relationCandidateStore,
    };
}

module.exports = {
    entityIndexResource,
    questionSnapshotResource,
    relationQueueKey,
    relationQueueResource,
    normalizeRefs,
    matchingEntityRefs,
    resolveQuestionsByRefs,
    createFsDedupSuggestionRepositories,
};
