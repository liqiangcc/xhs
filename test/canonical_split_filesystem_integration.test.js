'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { createApplication } = require('../src/bootstrap/create-application');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { readJson, readJsonl, writeJsonl } = require('../scripts/lib/io');
const { getIndexPaths } = require('../scripts/lib/index_store');

function canonical(id, questionIds, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['旧公司'],
        frequency: questionIds.length,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(questionId, index, canonicalId, company, originalQuestion) {
    return {
        question_id: questionId,
        original_question: originalQuestion || `question ${questionId}`,
        source_note_id: `note_${index}`,
        source_question_index: index,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['redis'],
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

function createFixture(canonicals, questions) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-app-fs-split-'));
    const paths = createCanonicalFsPaths(root);
    writeJsonl(paths.canonicalQuestions, canonicals);
    writeJsonl(paths.questions, questions);
    return { root, paths };
}

function cleanup(fixture) {
    fs.rmSync(fixture.root, { recursive: true, force: true });
}

test('composition root runs split through real filesystem adapters and refreshes both canonicals', async () => {
    const fixture = createFixture(
        [canonical('cq_source', ['q1', 'q2'], {
            canonical_title: 'Redis 综合问题',
            aliases: ['Redis 综合问题'],
            frequency: 3,
            review_priority: 'P1',
        })],
        [
            question('q1', 1, 'cq_source', '美团', 'Redis 过期策略有哪些？'),
            question('q2', 2, 'cq_source', '字节', 'Redis 为什么快？'),
            question('q2', 3, 'cq_source', '阿里', 'Redis 单线程为什么快？'),
        ],
    );

    try {
        const app = createApplication({ root: fixture.root });
        const result = await app.canonical.split({
            source: 'cq_source',
            question_id: 'q2',
            new_canonical_id: 'cq_redis_fast',
            title: 'Redis 为什么快？',
        });

        assert.equal(result.ok, true);
        assert.equal(result.canonical_count, 2);
        assert.equal(result.commit.committed, true);
        assert.equal(result.commit.recoverable, true);
        assert.deepEqual(
            result.plan.expected_revisions.map((item) => item.resource),
            [
                'canonical:cq_source',
                'canonical:cq_redis_fast',
                'question-bindings-by-question:q1',
                'question-bindings-by-question:q2',
            ],
        );

        const records = readJsonl(fixture.paths.canonicalQuestions, []);
        assert.deepEqual(
            records.map((item) => item.canonical_id),
            ['cq_redis_fast', 'cq_source'],
        );
        const source = records.find((item) => item.canonical_id === 'cq_source');
        const created = records.find((item) => item.canonical_id === 'cq_redis_fast');
        assert.deepEqual(source.question_ids, ['q1']);
        assert.equal(source.frequency, 1);
        assert.deepEqual(source.companies, ['美团']);
        assert.deepEqual(created.question_ids, ['q2']);
        assert.equal(created.frequency, 2);
        assert.deepEqual(created.companies, ['字节', '阿里'].sort((a, b) => a.localeCompare(b, 'zh')));
        assert.deepEqual(created.primary_domain, { l1: '缓存', l2: 'Redis' });
        assert.deepEqual(created.primary_entities, ['Redis']);
        assert.deepEqual(
            created.aliases,
            ['Redis 为什么快？', 'Redis 单线程为什么快？']
                .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh')),
        );

        const rows = readJsonl(fixture.paths.questions, []);
        assert.deepEqual(
            rows.filter((item) => item.question_id === 'q2').map((item) => item.canonical_id),
            ['cq_redis_fast', 'cq_redis_fast'],
        );
        assert.equal(rows.find((item) => item.question_id === 'q1').canonical_id, 'cq_source');

        const hotspot = readJson(getIndexPaths(fixture.paths.indexDir).hotspot);
        assert.deepEqual(
            hotspot.entries.map((entry) => [entry.canonical_id, entry.frequency]),
            [
                ['cq_redis_fast', 2],
                ['cq_source', 1],
            ],
        );
        assert.equal(result.integrity.ok, true);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture);
    }
});

test('filesystem split removes an empty source canonical when its last question is moved', async () => {
    const fixture = createFixture(
        [canonical('cq_source', ['q1'], {
            canonical_title: '旧 Canonical',
            frequency: 1,
        })],
        [question('q1', 1, 'cq_source', '美团', 'Redis 为什么快？')],
    );

    try {
        const app = createApplication({ root: fixture.root });
        const result = await app.canonical.split({
            source: 'cq_source',
            question_id: 'q1',
            new_canonical_id: 'cq_new',
            title: 'Redis 为什么快？',
        });

        assert.equal(result.ok, true);
        assert.equal(result.canonical_count, 1);
        assert.deepEqual(result.plan.changes.canonical_removals, ['cq_source']);

        const records = readJsonl(fixture.paths.canonicalQuestions, []);
        assert.deepEqual(records.map((item) => item.canonical_id), ['cq_new']);
        assert.deepEqual(records[0].question_ids, ['q1']);
        assert.equal(records[0].frequency, 1);

        const rows = readJsonl(fixture.paths.questions, []);
        assert.equal(rows.length, 1);
        assert.equal(rows[0].canonical_id, 'cq_new');

        const hotspot = readJson(getIndexPaths(fixture.paths.indexDir).hotspot);
        assert.deepEqual(
            hotspot.entries.map((entry) => entry.canonical_id),
            ['cq_new'],
        );
        assert.equal(result.integrity.ok, true);
        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        cleanup(fixture);
    }
});
