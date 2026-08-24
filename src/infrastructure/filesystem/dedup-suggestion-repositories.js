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

function normalizeQuestionIds(questionIds) {
    return [...new Set((questionIds || [])
        .map((questionId) => String(questionId || '').trim())
        .filter(Boolean))]
        .sort((left, right) => left.localeCompare(right));
}

function entityIndexResource(seed) {
    return `dedup-entity-index:${String(seed)}`;
}

function hotspotIndexResource() {
    return 'dedup-hotspot-index';
}

function questionSnapshotResource(refs) {
    return `dedup-questions-by-refs:${hashValue(normalizeRefs(refs)).slice(0, 20)}`;
}

function questionSelectionResource(questionIds) {
    return `dedup-questions-by-ids:${hashValue(normalizeQuestionIds(questionIds)).slice(0, 20)}`;
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

function readHotspotIndex(paths) {
    return readJson(paths.hotspotIndex, {
        schema_version: 'hotspot_index.v1',
        entries: [],
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

function listHotspots(paths) {
    const index = readHotspotIndex(paths);
    return (index.entries || []).map(clone);
}

function hotspotRefs(hotspots) {
    return normalizeRefs((hotspots || []).flatMap((hotspot) => hotspot?.refs || []));
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

function resolveQuestionsByQuestionIds(paths, questionIds) {
    const normalizedQuestionIds = normalizeQuestionIds(questionIds);
    const requested = new Set(normalizedQuestionIds);
    return readQuestions(paths)
        .filter((question) => requested.has(String(question?.question_id || '')))
        .sort((left, right) => compareRefs(left, right))
        .map(clone);
}

function readQueueManifest(paths) {
    return readJson(paths.relationCandidateQueues, {
        schema_version: 'dedup_relation_candidate_queues.v1',
        queues: {},
    });
}

function relationQueueSnapshot(paths, mode, seed) {
    const resource = relationQueueResource(mode, seed);
    const manifest = readQueueManifest(paths);
    const queue = manifest.queues?.[relationQueueKey(mode, seed)] || null;
    return {
        queue: queue ? clone(queue) : null,
        resource,
        revision: hashValue(queue),
    };
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

    const hotspotRepository = {
        async listHotspots() {
            const hotspots = listHotspots(paths);
            return {
                hotspots,
                resource: hotspotIndexResource(),
                revision: hashValue(hotspots),
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

    const questionSelectionRepository = {
        async findByQuestionIds(questionIds) {
            if (!Array.isArray(questionIds)) throw new Error('questionIds must be an array');
            const normalizedQuestionIds = normalizeQuestionIds(questionIds);
            const questions = resolveQuestionsByQuestionIds(paths, normalizedQuestionIds);
            return {
                questions,
                resource: questionSelectionResource(normalizedQuestionIds),
                revision: hashValue(questions),
            };
        },
    };

    const relationCandidatePublisher = {
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
        hotspotRepository,
        questionRepository,
        questionSelectionRepository,
        relationCandidatePublisher,
    };
}

module.exports = {
    hashValue,
    entityIndexResource,
    hotspotIndexResource,
    questionSnapshotResource,
    questionSelectionResource,
    relationQueueKey,
    relationQueueResource,
    normalizeRefs,
    normalizeQuestionIds,
    matchingEntityRefs,
    listHotspots,
    hotspotRefs,
    resolveQuestionsByRefs,
    resolveQuestionsByQuestionIds,
    readQueueManifest,
    relationQueueSnapshot,
    createFsDedupSuggestionRepositories,
};
