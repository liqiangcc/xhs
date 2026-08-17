'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJsonl, readJsonl } = require('../scripts/lib/io');
const { buildIndexes, writeIndexes } = require('../scripts/lib/index_store');
const { runSuggest } = require('../scripts/commands/canonical');
const { runDecide, runApply, main: dedupMain } = require('../scripts/commands/dedup');
const { main: xhsMain } = require('../scripts/xhs');

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

function fixture(root) {
    const questions = [
        question({ question_id: 'q_redis_a', source_note_id: 'note-a' }),
        question({
            question_id: 'q_redis_b',
            source_note_id: 'note-b',
            original_question: 'Redis 为什么这么快？',
            company: '字节',
        }),
    ];
    const questionsPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const indexDir = path.join(root, 'data', 'indexes');
    writeJsonl(questionsPath, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: [] }), indexDir);
    return {
        questionsPath,
        canonicalPath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
    };
}

async function suggestKey(root) {
    const result = await runSuggest({ root, entity: 'redis', limit: 10 });
    return result.relation_candidates[0].relation_candidate_key;
}

test('thin dedup CLI records an explicit decision then applies it without exposing internal evidence', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-dedup-cli-'));
    try {
        const paths = fixture(root);
        const key = await suggestKey(root);
        const decision = await runDecide({
            root,
            'relation-candidate-key': key,
            relation: 'same',
            'actor-type': 'human',
            'actor-id': 'reviewer-cli',
            'actor-display-name': 'CLI Reviewer',
            rationale: 'same Redis performance concept',
            'decided-at': '2026-08-14T14:30:00+08:00',
        });

        assert.equal(decision.schema_version, 'dedup_relation_decision_result.v1');
        assert.equal(decision.ok, true);
        assert.equal(decision.relation_candidate_key, key);
        assert.equal(decision.relation, 'same');
        assert.equal(decision.decision_state, 'explicit');
        assert.deepEqual(decision.actor, {
            type: 'human',
            id: 'reviewer-cli',
            display_name: 'CLI Reviewer',
        });
        for (const hidden of ['decision', 'store', 'source_revisions', 'expected_revisions']) {
            assert.equal(Object.hasOwn(decision, hidden), false);
        }

        const applied = await runApply({
            root,
            'relation-candidate-key': key,
            'canonical-id': 'cq_redis_performance',
            'canonical-title': 'Redis 为什么快？',
        });

        assert.equal(applied.schema_version, 'dedup_relation_apply_result.v1');
        assert.equal(applied.applied, true);
        assert.equal(applied.committed, true);
        assert.equal(applied.operation, 'canonicalize');
        assert.equal(applied.canonical_id, 'cq_redis_performance');
        assert.deepEqual(applied.question_ids, ['q_redis_a', 'q_redis_b']);
        for (const hidden of [
            'intent',
            'decision_snapshot',
            'current_source_revisions',
            'canonicalization_plan',
            'mutation_plan',
            'commit',
            'plan',
        ]) {
            assert.equal(Object.hasOwn(applied, hidden), false);
        }
        assert.ok(readJsonl(paths.questionsPath, []).every((row) =>
            row.canonical_id === 'cq_redis_performance'));
        assert.equal(readJsonl(paths.canonicalPath, []).length, 1);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

test('thin dedup CLI preserves explicit no-op and lets Application enforce relation apply requirements', async () => {
    const unrelatedRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-dedup-cli-noop-'));
    const sameRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-dedup-cli-needs-target-'));
    try {
        fixture(unrelatedRoot);
        const unrelatedKey = await suggestKey(unrelatedRoot);
        await runDecide({
            root: unrelatedRoot,
            'relation-candidate-key': unrelatedKey,
            relation: 'unrelated',
            'actor-type': 'human',
            'actor-id': 'reviewer-cli',
        });
        const noop = await runApply({
            root: unrelatedRoot,
            'relation-candidate-key': unrelatedKey,
        });
        assert.deepEqual(noop, {
            schema_version: 'dedup_relation_apply_result.v1',
            ok: true,
            applied: false,
            relation_candidate_key: unrelatedKey,
            relation: 'unrelated',
            reason_code: 'explicitly_unrelated',
        });

        fixture(sameRoot);
        const sameKey = await suggestKey(sameRoot);
        await runDecide({
            root: sameRoot,
            'relation-candidate-key': sameKey,
            relation: 'same',
            'actor-type': 'human',
            'actor-id': 'reviewer-cli',
        });
        await assert.rejects(
            runApply({ root: sameRoot, 'relation-candidate-key': sameKey }),
            /Relation apply intent is not ready/,
        );
    } finally {
        fs.rmSync(unrelatedRoot, { recursive: true, force: true });
        fs.rmSync(sameRoot, { recursive: true, force: true });
    }
});

test('dedup CLI performs only syntax-level target pairing and top-level xhs routes the namespace', async (t) => {
    await assert.rejects(
        runApply({
            root: '/tmp/unused-dedup-cli-root',
            'relation-candidate-key': 'entity|Redis|q_a,q_b',
            'canonical-id': 'cq_redis',
        }),
        /--canonical-id and --canonical-title must be provided together/,
    );

    const log = t.mock.method(console, 'log', () => {});
    const exitCode = await Promise.resolve(xhsMain(['node', 'scripts/xhs.js', 'dedup', 'help']));
    assert.equal(exitCode, 0);
    assert.ok(log.mock.callCount() >= 1);

    const error = t.mock.method(console, 'error', () => {});
    const unknown = await Promise.resolve(dedupMain(['node', 'scripts/commands/dedup.js', 'unknown']));
    assert.equal(unknown, 1);
    assert.ok(error.mock.callCount() >= 1);
});
