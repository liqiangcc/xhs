'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { readJsonl, writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { createApplication } = require('../src/bootstrap/create-application');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');

function makeQuestion(id, note, text, company = '美团') {
    return {
        question_id: id,
        original_question: text,
        source_note_id: note,
        source_question_index: 0,
        company,
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
    };
}

function fixture(root) {
    const questions = [
        makeQuestion('q_redis_a', 'note-a', 'Redis 为什么快？'),
        makeQuestion('q_redis_b', 'note-b', 'Redis 为什么这么快？', '字节'),
    ];
    const paths = createCanonicalFsPaths(root);
    writeJsonl(paths.questions, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), paths.indexDir);
    return { paths, questions };
}

async function decide(app, relation) {
    const suggestions = await app.dedup.suggest({ mode: 'entity', seed: 'redis', limit: 10 });
    const key = suggestions.relation_candidates[0].relation_candidate_key;
    await app.dedup.recordDecision({
        relation_candidate_key: key,
        relation,
        actor: { type: 'human', id: 'reviewer-1' },
        rationale: `${relation} Redis relation`,
        decided_at: '2026-08-13T17:58:00+08:00',
    });
    return key;
}

function assertNoCanonicalWrite(paths) {
    assert.equal(fs.existsSync(paths.canonicalQuestions), false);
    assert.equal(fs.existsSync(paths.lock), false);
    assert.equal(fs.existsSync(paths.journal), false);
    assert.equal(fs.existsSync(paths.candidateManifest), false);
}

test('production applyDecision revalidates Decision then executes canonicalization without exposing intermediates', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-apply-decision-fs-'));
    try {
        const { paths } = fixture(root);
        const app = createApplication({ root });
        const key = await decide(app, 'same');
        const result = await app.dedup.applyDecision({
            relation_candidate_key: key,
            canonical_id: 'cq_redis_performance',
            canonical_title: 'Redis 为什么快？',
        });

        assert.equal(result.applied, true);
        assert.equal(result.commit.operation, 'canonicalize');
        assert.equal(result.canonical_resolution, 'absent');
        assert.deepEqual(result.question_ids, ['q_redis_a', 'q_redis_b']);
        assert.ok(readJsonl(paths.questions, []).every((row) =>
            row.canonical_id === 'cq_redis_performance'));
        assert.deepEqual(readJsonl(paths.canonicalQuestions, [])[0].question_ids, [
            'q_redis_a', 'q_redis_b',
        ]);
        for (const hidden of ['intent', 'canonicalization_plan', 'mutation_plan', 'plan']) {
            assert.equal(Object.hasOwn(result, hidden), false);
        }
        assert.equal(fs.existsSync(paths.lock), false);
        assert.equal(fs.existsSync(paths.journal), false);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('production applyDecision rejects stale Dedup Question source before Canonical mutation', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-apply-decision-stale-fs-'));
    try {
        const { paths, questions } = fixture(root);
        const app = createApplication({ root });
        const key = await decide(app, 'same');
        writeJsonl(paths.questions, questions.map((row) => row.question_id === 'q_redis_a'
            ? { ...row, original_question: 'Redis 为什么具有高性能？' }
            : row));

        await assert.rejects(
            app.dedup.applyDecision({
                relation_candidate_key: key,
                canonical_id: 'cq_redis_performance',
                canonical_title: 'Redis 为什么快？',
            }),
            /Stale relation candidate source/,
        );
        assertNoCanonicalWrite(paths);
        assert.ok(readJsonl(paths.questions, []).every((row) => row.canonical_id === null));
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('production applyDecision returns no-op for unrelated Decision', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-apply-decision-noop-fs-'));
    try {
        const { paths } = fixture(root);
        const app = createApplication({ root });
        const key = await decide(app, 'unrelated');
        const result = await app.dedup.applyDecision({ relation_candidate_key: key });

        assert.equal(result.applied, false);
        assert.equal(result.reason_code, 'explicitly_unrelated');
        assert.equal(Object.hasOwn(result, 'commit'), false);
        assertNoCanonicalWrite(paths);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
