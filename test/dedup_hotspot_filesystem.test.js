'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { readJson, writeJson, writeJsonl, readJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { createApplication } = require('../src/bootstrap/create-application');
const { createDedupFsPaths } = require('../src/infrastructure/filesystem/dedup-paths');
const {
    createFsDedupSuggestionRepositories,
} = require('../src/infrastructure/filesystem/dedup-suggestion-repositories');
const {
    createFsDedupDecisionRepositories,
} = require('../src/infrastructure/filesystem/dedup-decision-repositories');
const {
    createSuggestCanonicalRelationsUseCase,
} = require('../src/application/dedup/suggest-canonical-relations');
const {
    createRecordRelationDecisionUseCase,
} = require('../src/application/dedup/record-relation-decision');
const taxonomy = require('../config/taxonomy.json');

function question(overrides = {}) {
    return {
        question_id: 'q_hot',
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

function fixture(root) {
    const questions = [
        question(),
        question({ source_note_id: 'note-b', company: '字节' }),
    ];
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const indexDir = path.join(root, 'data', 'indexes');
    writeJsonl(questionsPath, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), indexDir);
    return {
        questions,
        questionsPath,
        hotspotIndex: path.join(indexDir, 'hotspot_index.json'),
        canonicalPath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        decisionsPath: path.join(root, 'data', 'manifests', 'dedup', 'relation_decisions.jsonl'),
    };
}

function mutateHotspotIndex(hotspotIndex) {
    const current = readJson(hotspotIndex);
    current.entries[0] = {
        ...current.entries[0],
        frequency: Number(current.entries[0].frequency || 0) + 1,
    };
    writeJson(hotspotIndex, current);
}

test('hotspot Decision rejects hotspot-index drift after Suggest before audit persistence', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-hotspot-decision-stale-'));
    try {
        const paths = fixture(root);
        const app = createApplication({ root });
        const suggestions = await app.dedup.suggest({ mode: 'hotspot' });
        const key = suggestions.relation_candidates[0].relation_candidate_key;

        mutateHotspotIndex(paths.hotspotIndex);

        await assert.rejects(
            app.dedup.recordDecision({
                relation_candidate_key: key,
                relation: 'same',
                actor: { type: 'human', id: 'reviewer-hotspot' },
                decided_at: '2026-08-14T14:50:00+08:00',
            }),
            /Stale relation candidate source dedup-hotspot-index/,
        );
        assert.equal(fs.existsSync(paths.decisionsPath), false);
        assert.equal(fs.existsSync(paths.canonicalPath), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('hotspot Apply rejects Question drift after persisted Decision before Canonical mutation', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-hotspot-apply-stale-'));
    try {
        const paths = fixture(root);
        const app = createApplication({ root });
        const suggestions = await app.dedup.suggest({ mode: 'hotspot' });
        const key = suggestions.relation_candidates[0].relation_candidate_key;
        await app.dedup.recordDecision({
            relation_candidate_key: key,
            relation: 'same',
            actor: { type: 'human', id: 'reviewer-hotspot' },
            decided_at: '2026-08-14T14:51:00+08:00',
        });

        writeJsonl(paths.questionsPath, paths.questions.map((row, index) =>
            index === 0 ? { ...row, original_question: 'Redis 为什么具有高性能？' } : row));

        await assert.rejects(
            app.dedup.applyDecision({
                relation_candidate_key: key,
                canonical_id: 'cq_redis_hotspot',
                canonical_title: 'Redis 为什么快？',
            }),
            /Stale relation candidate source dedup-questions-by-refs:/,
        );
        assert.equal(fs.existsSync(paths.canonicalPath), false);
        assert.ok(readJsonl(paths.questionsPath, []).every((row) => row.canonical_id === null));
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('filesystem DecisionStore CAS rejects hotspot-index race after Application freshness validation', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-hotspot-decision-cas-'));
    try {
        const paths = fixture(root);
        const dedupPaths = createDedupFsPaths(root);
        const suggestionRepositories = createFsDedupSuggestionRepositories({
            root,
            paths: dedupPaths,
        });
        const decisionRepositories = createFsDedupDecisionRepositories({
            root,
            paths: dedupPaths,
        });
        const suggest = createSuggestCanonicalRelationsUseCase({
            taxonomy,
            indexRepository: suggestionRepositories.indexRepository,
            hotspotRepository: suggestionRepositories.hotspotRepository,
            questionRepository: suggestionRepositories.questionRepository,
            relationCandidatePublisher: suggestionRepositories.relationCandidatePublisher,
        });
        const wrappedStore = {
            async record(decision, options) {
                mutateHotspotIndex(paths.hotspotIndex);
                return decisionRepositories.relationDecisionGateway.record(decision, options);
            },
        };
        const recordDecision = createRecordRelationDecisionUseCase({
            relationCandidateRepository: decisionRepositories.relationCandidateRepository,
            indexRepository: suggestionRepositories.indexRepository,
            hotspotRepository: suggestionRepositories.hotspotRepository,
            questionRepository: suggestionRepositories.questionRepository,
            relationDecisionGateway: wrappedStore,
        });

        const suggestions = await suggest({ mode: 'hotspot' });
        const key = suggestions.relation_candidates[0].relation_candidate_key;

        await assert.rejects(
            recordDecision({
                relation_candidate_key: key,
                relation: 'same',
                actor: { type: 'human', id: 'reviewer-hotspot' },
                decided_at: '2026-08-14T14:52:00+08:00',
            }),
            /Revision mismatch for dedup-hotspot-index/,
        );
        assert.equal(fs.existsSync(paths.decisionsPath), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
