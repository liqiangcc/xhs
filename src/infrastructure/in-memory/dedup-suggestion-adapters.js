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

function queueResource(mode, seed) {
    return `dedup-relation-queue:${String(mode)}:${String(seed)}`;
}

function decisionLogResource() {
    return 'dedup-relation-decisions';
}

function decisionSnapshotResource(relationCandidateKey) {
    return `dedup-relation-decision:${String(relationCandidateKey)}`;
}

function createInMemoryDedupSuggestionAdapters(seed = {}) {
    let questions = (seed.questions || []).map(clone);
    let hotspots = (seed.hotspots || []).map(clone);
    const entityRefs = new Map(
        Object.entries(seed.entity_refs || {}).map(([key, refs]) => [key, (refs || []).map(clone)]),
    );
    const queues = new Map();
    const decisions = [];
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

    function assertExpectedRevisions(expectedRevisions) {
        if (!Array.isArray(expectedRevisions) || expectedRevisions.length === 0) {
            throw new Error('Dedup decision expected_revisions are required');
        }
        for (const expected of expectedRevisions) {
            if (!expected?.resource || !expected?.revision) {
                throw new Error('Dedup decision expected revision resource and revision are required');
            }
            const actual = revision(expected.resource);
            if (actual !== expected.revision) {
                throw new Error(
                    `Revision mismatch for ${expected.resource}: expected ${expected.revision}, got ${actual}`,
                );
            }
        }
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

    const hotspotRepository = {
        async listHotspots() {
            const resource = hotspotIndexResource();
            return {
                hotspots: hotspots.map(clone),
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

    const questionSelectionRepository = {
        async findByQuestionIds(questionIds) {
            if (!Array.isArray(questionIds)) throw new Error('questionIds must be an array');
            const requested = new Set(normalizeQuestionIds(questionIds));
            const resolved = questions
                .filter((question) => requested.has(String(question?.question_id || '')))
                .map(clone);
            const resource = 'dedup-question-catalog';
            return {
                questions: resolved,
                resource,
                revision: revision(resource),
            };
        },
    };

    const relationCandidatePublisher = {
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

    const relationCandidateRepository = {
        async get(relationCandidateKey) {
            for (const [resource, queue] of queues.entries()) {
                const candidate = (queue.relation_candidates || []).find(
                    (item) => item.relation_candidate_key === relationCandidateKey,
                );
                if (!candidate) continue;
                return {
                    candidate: clone(candidate),
                    source_revisions: clone(queue.source_revisions || []),
                    resource,
                    revision: revision(resource),
                };
            }
            return null;
        },
    };

    const relationDecisionRepository = {
        async get(relationCandidateKey) {
            const key = String(relationCandidateKey || '').trim();
            if (!key) throw new Error('relationCandidateKey is required');
            for (let index = decisions.length - 1; index >= 0; index--) {
                const decision = decisions[index];
                if (decision.relation_candidate_key !== key) continue;
                const resource = decisionSnapshotResource(key);
                return {
                    decision: clone(decision),
                    resource,
                    revision: revision(resource),
                };
            }
            return null;
        },
    };

    const relationDecisionGateway = {
        async record(decision, options = {}) {
            if (!decision || typeof decision !== 'object' || Array.isArray(decision)) {
                throw new Error('relation decision is required');
            }
            assertExpectedRevisions(options.expected_revisions);
            decisions.push(clone(decision));
            bump(decisionSnapshotResource(decision.relation_candidate_key));
            const resource = decisionLogResource();
            bump(resource);
            return {
                recorded: true,
                resource,
                revision: revision(resource),
            };
        },
    };

    const testSupport = Object.freeze({
        replaceEntityRefs(entitySeed, refs) {
            const key = String(entitySeed);
            entityRefs.set(key, (refs || []).map(clone));
            bump(entityIndexResource(key));
        },

        replaceHotspots(nextHotspots) {
            hotspots = (nextHotspots || []).map(clone);
            bump(hotspotIndexResource());
        },

        replaceQuestions(nextQuestions) {
            questions = (nextQuestions || []).map(clone);
            bump('dedup-question-catalog');
        },
    });

    function snapshot() {
        return {
            questions: questions.map(clone),
            hotspots: hotspots.map(clone),
            entity_refs: Object.fromEntries(
                [...entityRefs.entries()].map(([key, refs]) => [key, refs.map(clone)]),
            ),
            queues: Object.fromEntries(
                [...queues.entries()].map(([resource, queue]) => [resource, clone(queue)]),
            ),
            decisions: decisions.map(clone),
        };
    }

    return {
        indexRepository,
        hotspotRepository,
        questionRepository,
        questionSelectionRepository,
        relationCandidatePublisher,
        relationCandidateRepository,
        relationDecisionRepository,
        relationDecisionGateway,
        testSupport,
        snapshot,
    };
}

module.exports = {
    createInMemoryDedupSuggestionAdapters,
};
