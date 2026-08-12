'use strict';

function clone(value) {
    return structuredClone(value);
}

function refKey(ref) {
    return [
        ref?.question_id,
        ref?.source_note_id,
        ref?.source_question_index ?? '',
    ].join('::');
}

function entityIndexResource(seed) {
    return `dedup-entity-index:${String(seed)}`;
}

function queueResource(mode, seed) {
    return `dedup-relation-queue:${String(mode)}:${String(seed)}`;
}

function createInMemoryDedupSuggestionAdapters(seed = {}) {
    let questions = (seed.questions || []).map(clone);
    const entityRefs = new Map(
        Object.entries(seed.entity_refs || {}).map(([key, refs]) => [key, (refs || []).map(clone)]),
    );
    const queues = new Map();
    let revisionSequence = 0;
    const revisions = new Map();

    function revision(resource) {
        if (!revisions.has(resource)) revisions.set(resource, 'rev-0');
        return revisions.get(resource);
    }

    function bump(resource) {
        revisionSequence += 1;
        revisions.set(resource, `rev-${revisionSequence}`);
    }

    const indexRepository = {
        async findEntityRefs(entitySeed) {
            const key = String(entitySeed);
            const resource = entityIndexResource(key);
            return {
                refs: (entityRefs.get(key) || []).map(clone),
                resource,
                revision: revision(resource),
            };
        },
    };

    const questionRepository = {
        async findByRefs(refs) {
            if (!Array.isArray(refs)) throw new Error('refs must be an array');
            const byRef = new Map(questions.map((question) => [refKey(question), question]));
            const resolved = [];
            const seen = new Set();
            for (const ref of refs) {
                const key = refKey(ref);
                if (seen.has(key)) continue;
                seen.add(key);
                const question = byRef.get(key);
                if (question) resolved.push(clone(question));
            }
            const resource = 'dedup-question-catalog';
            return {
                questions: resolved,
                resource,
                revision: revision(resource),
            };
        },
    };

    const relationCandidateStore = {
        async replaceQueue(queue) {
            if (!queue || typeof queue !== 'object' || Array.isArray(queue)) {
                throw new Error('relation candidate queue is required');
            }
            const resource = queueResource(queue.mode, queue.seed);
            queues.set(resource, clone(queue));
            bump(resource);
            return {
                resource,
                revision: revision(resource),
                candidate_count: Number(queue.candidate_count || 0),
            };
        },
    };

    const testSupport = Object.freeze({
        replaceEntityRefs(entitySeed, refs) {
            const key = String(entitySeed);
            entityRefs.set(key, (refs || []).map(clone));
            bump(entityIndexResource(key));
        },

        replaceQuestions(nextQuestions) {
            questions = (nextQuestions || []).map(clone);
            bump('dedup-question-catalog');
        },
    });

    function snapshot() {
        return {
            questions: questions.map(clone),
            entity_refs: Object.fromEntries(
                [...entityRefs.entries()].map(([key, refs]) => [key, refs.map(clone)]),
            ),
            queues: Object.fromEntries(
                [...queues.entries()].map(([resource, queue]) => [resource, clone(queue)]),
            ),
        };
    }

    return {
        indexRepository,
        questionRepository,
        relationCandidateStore,
        testSupport,
        snapshot,
    };
}

module.exports = {
    createInMemoryDedupSuggestionAdapters,
};
