'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const {
    readJson,
    readJsonl,
    writeJson,
    writeJsonl,
} = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { createApplication } = require('../src/bootstrap/create-application');
const {
    createRecordRelationDecisionUseCase,
} = require('../src/application/dedup/record-relation-decision');
const {
    createFsDedupSuggestionRepositories,
} = require('../src/infrastructure/filesystem/dedup-suggestion-repositories');
const {
    createFsDedupDecisionRepositories,
} = require('../src/infrastructure/filesystem/dedup-decision-repositories');
const { createDedupFsPaths } = require('../src/infrastructure/filesystem/dedup-paths');

function question(overrides = {}) {
    return {
        question_id: 'q_default',
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '美团',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2026',
        date: '未知',
        domain: { l1: '缓存', l2: 'Redis' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: ['Redis'],
        business_context: [],
        is_valid_for_library: true,
        canonical_id: null,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
        ...overrides,
    };
}

function makeRoot(prefix) {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeFixture(root) {
    const q1 = question({
        question_id: 'q_redis_a',
        source_note_id: 'note-a',
        original_question: 'Redis 为什么快？',
    });
    const q2 = question({
        question_id: 'q_redis_b',
        source_note_id: 'note-b',
        company: '字节',
        original_question: 'Redis 为什么这么快？',
    });
    const questions = [q1, q2];
    const paths = createDedupFsPaths(root);
    writeJsonl(paths.questions, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), path.dirname(paths.entityIndex));
    return { paths, q1, q2 };
}

async function suggest(root) {
    const app = createApplication({ root });
    return app.dedup.suggest({ mode: 'entity', seed: 'redis', limit: 10 });
}

function decisionUseCase(root, relationDecisionStoreOverride = null) {
    const suggestionRepositories = createFsDedupSuggestionRepositories({ root });
    const decisionRepositories = createFsDedupDecisionRepositories({ root });
    return createRecordRelationDecisionUseCase({
        relationCandidateRepository: decisionRepositories.relationCandidateRepository,
        indexRepository: suggestionRepositories.indexRepository,
        questionRepository: suggestionRepositories.questionRepository,
        relationDecisionStore: relationDecisionStoreOverride || decisionRepositories.relationDecisionStore,
    });
}

test('production composition root records an explicit dedup decision in a separate audit log', async () => {
    const root = makeRoot('xhs-dedup-decision-fs-');
    try {
        const { paths } = writeFixture(root);
        const suggestions = await suggest(root);
        const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
        const app = createApplication({ root });

        const result = await app.dedup.recordDecision({
            relation_candidate_key: relationCandidateKey,
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-1' },
            rationale: '两道题表达同一知识点',
            decided_at: '2026-08-13T12:30:00+08:00',
        });

        assert.equal(result.ok, true);
        assert.equal(result.relation, 'same');
        assert.equal(result.store.resource, 'dedup-relation-decisions');
        assert.match(result.store.revision, /^[0-9a-f]{64}$/);
        assert.equal(Object.hasOwn(result, 'plan'), false);
        assert.equal(Object.hasOwn(result, 'commit'), false);

        const decisions = readJsonl(paths.relationDecisions, []);
        assert.equal(decisions.length, 1);
        assert.equal(decisions[0].schema_version, 'dedup_relation_decision.v1');
        assert.equal(decisions[0].relation_candidate_key, relationCandidateKey);
        assert.equal(decisions[0].relation, 'same');
        assert.equal(decisions[0].decision_state, 'explicit');
        assert.equal(Object.hasOwn(decisions[0], 'canonical_id'), false);
        assert.equal(Object.hasOwn(decisions[0], 'mutation_plan'), false);

        const canonicalCandidateManifest = path.join(
            root,
            'data',
            'manifests',
            'canonical',
            'canonical_candidates.json',
        );
        assert.equal(fs.existsSync(canonicalCandidateManifest), false);
        assert.equal(fs.existsSync(paths.relationDecisionLock), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('filesystem decision store rejects a Question race after Application freshness validation', async () => {
    const root = makeRoot('xhs-dedup-decision-question-race-');
    try {
        const { paths, q1, q2 } = writeFixture(root);
        const suggestions = await suggest(root);
        const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
        const decisionRepositories = createFsDedupDecisionRepositories({ root });
        const racingStore = {
            async record(decision, options) {
                writeJsonl(paths.questions, [
                    q1,
                    { ...q2, original_question: 'Redis 为什么会这么快？' },
                ]);
                return decisionRepositories.relationDecisionStore.record(decision, options);
            },
        };

        await assert.rejects(
            decisionUseCase(root, racingStore)({
                relation_candidate_key: relationCandidateKey,
                relation: 'same',
                actor: { type: 'ai', id: 'review-agent' },
            }),
            /Revision mismatch for dedup-questions-by-refs:/,
        );
        assert.equal(fs.existsSync(paths.relationDecisions), false);
        assert.equal(fs.existsSync(paths.relationDecisionLock), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('filesystem decision store rejects a review queue race after the candidate was loaded', async () => {
    const root = makeRoot('xhs-dedup-decision-queue-race-');
    try {
        const { paths } = writeFixture(root);
        const suggestions = await suggest(root);
        const relationCandidateKey = suggestions.relation_candidates[0].relation_candidate_key;
        const decisionRepositories = createFsDedupDecisionRepositories({ root });
        const racingStore = {
            async record(decision, options) {
                const manifest = readJson(paths.relationCandidateQueues);
                manifest.queues['entity|Redis'] = {
                    ...manifest.queues['entity|Redis'],
                    review_note: 'queue changed after candidate load',
                };
                writeJson(paths.relationCandidateQueues, manifest);
                return decisionRepositories.relationDecisionStore.record(decision, options);
            },
        };

        await assert.rejects(
            decisionUseCase(root, racingStore)({
                relation_candidate_key: relationCandidateKey,
                relation: 'related',
                actor: { type: 'human', id: 'reviewer-2' },
            }),
            /Revision mismatch for dedup-relation-queue:entity:Redis/,
        );
        assert.equal(fs.existsSync(paths.relationDecisions), false);
        assert.equal(fs.existsSync(paths.relationDecisionLock), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
