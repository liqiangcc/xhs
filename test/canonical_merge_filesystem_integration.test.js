'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { createApplication } = require('../src/bootstrap/create-application');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const { readAnswerFile } = require('../scripts/lib/answer_store');
const { readJson, readJsonl, writeJson, writeJsonl } = require('../scripts/lib/io');
const { buildIndexes, getIndexPaths, writeIndexes } = require('../scripts/lib/index_store');

function canonical(id, overrides = {}) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: [],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: [],
        frequency: 0,
        review_priority: 'P2',
        answer_status: 'ready',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function question(questionId, canonicalId, index, company) {
    return {
        question_id: questionId,
        original_question: `question ${questionId}`,
        source_note_id: `note_${index}`,
        source_question_index: index,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['Redis'],
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

function progress(canonicalId, overrides = {}) {
    return {
        canonical_id: canonicalId,
        status: 'learning',
        level: 2,
        review_count: 3,
        last_reviewed_at: '2026-08-01',
        next_review_at: '2026-08-10',
        confidence: 0.7,
        difficulty: 3,
        mistake_count: 0,
        updated_at: '2026-08-01',
        ...overrides,
    };
}

function answerContent(canonicalId, overrides = {}) {
    const metadata = {
        schema_version: 'answer.v1',
        canonical_id: canonicalId,
        version: 1,
        status: 'draft',
        quality_tier: 'long_tail_baseline',
        updated_at: '2026-08-01',
        ...overrides,
    };
    return [
        `<!-- xhs-answer: ${JSON.stringify(metadata)} -->`,
        `# ${canonicalId}`,
        '',
        'answer body',
        '',
    ].join('\n');
}

function createFixture() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-app-fs-merge-'));
    const paths = createCanonicalFsPaths(root);
    const canonicals = [
        canonical('cq_target', {
            canonical_title: 'Redis 为什么快？',
            aliases: ['Redis 为什么快？'],
            question_ids: ['q1'],
            companies: ['美团'],
            frequency: 1,
            review_priority: 'P1',
        }),
        canonical('cq_source', {
            canonical_title: 'Redis 单线程为什么快？',
            aliases: ['Redis 单线程为什么快？'],
            question_ids: ['q2'],
            companies: ['字节'],
            frequency: 1,
            review_priority: 'P0',
        }),
    ];
    const questions = [
        question('q1', 'cq_target', 1, '美团'),
        question('q2', 'cq_source', 2, '字节'),
    ];

    writeJsonl(paths.canonicalQuestions, canonicals);
    writeJsonl(paths.questions, questions);
    writeIndexes(buildIndexes(questions, { canonicalQuestions: canonicals }), paths.indexDir);
    writeJson(paths.mergeHistory, {
        schema_version: 'canonical_merge_history.v1',
        items: [],
    });
    writeJson(paths.reviewProgress, {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-08-01',
        items: [
            progress('cq_target', {
                level: 3,
                review_count: 2,
                confidence: 0.8,
                difficulty: 2,
            }),
            progress('cq_source', {
                level: 1,
                review_count: 4,
                confidence: 0.4,
                difficulty: 5,
                mistake_count: 1,
            }),
        ],
    });
    writeJson(path.join(paths.reviewSessionsDir, '2026-08-01.json'), {
        events: [
            { event_id: 'e-target', canonical_id: 'cq_target', result: 'good' },
            { event_id: 'e-source', canonical_id: 'cq_source', result: 'hard' },
        ],
    });

    fs.mkdirSync(paths.answersDir, { recursive: true });
    fs.writeFileSync(
        path.join(paths.answersDir, 'cq_target.md'),
        answerContent('cq_target', {
            version: 4,
            status: 'ready',
            quality_tier: 'curated',
        }),
        'utf8',
    );
    fs.writeFileSync(
        path.join(paths.answersDir, 'cq_source.md'),
        answerContent('cq_source', { version: 2, status: 'draft' }),
        'utf8',
    );

    return { root, paths };
}

test('composition root runs merge application through real filesystem adapters as one transaction', async () => {
    const fixture = createFixture();
    try {
        const app = createApplication({
            root: fixture.root,
            clock: () => '2026-08-12T06:44:00.000Z',
        });

        const result = await app.canonical.merge({
            target: 'cq_target',
            source: 'cq_source',
            reason: 'same interview knowledge point',
        });

        assert.equal(result.ok, true);
        assert.deepEqual(result.moved_question_ids, ['q2']);
        assert.equal(result.plan.expected_revisions.length, 6);
        assert.equal(result.commit.committed, true);
        assert.equal(result.commit.recoverable, true);
        assert.equal(result.commit.answer_invalidation_count, 1);
        assert.equal(result.commit.answer_archive_count, 1);

        const canonicals = readJsonl(fixture.paths.canonicalQuestions, []);
        assert.deepEqual(canonicals.map((item) => item.canonical_id), ['cq_target']);
        assert.deepEqual(canonicals[0].question_ids, ['q1', 'q2']);
        assert.equal(canonicals[0].review_priority, 'P0');
        assert.equal(canonicals[0].answer_status, 'needs_update');

        const questions = readJsonl(fixture.paths.questions, []);
        assert.equal(questions.find((item) => item.question_id === 'q2').canonical_id, 'cq_target');

        const review = readJson(fixture.paths.reviewProgress);
        assert.equal(review.updated_at, '2026-08-12');
        assert.equal(review.items.length, 1);
        assert.equal(review.items[0].canonical_id, 'cq_target');
        assert.equal(review.items[0].level, 1);
        assert.equal(review.items[0].review_count, 6);
        assert.equal(review.items[0].mistake_count, 1);

        const session = readJson(path.join(fixture.paths.reviewSessionsDir, '2026-08-01.json'));
        const migrated = session.events.find((event) => event.event_id === 'e-source');
        assert.equal(migrated.canonical_id, 'cq_target');
        assert.equal(migrated.migrated_from_canonical_id, 'cq_source');

        const targetAnswer = readAnswerFile(path.join(fixture.paths.answersDir, 'cq_target.md'));
        assert.equal(targetAnswer.metadata.status, 'needs_update');
        assert.equal(targetAnswer.metadata.quality_tier, 'needs_update');
        assert.equal(targetAnswer.metadata.version, 5);
        assert.equal(targetAnswer.metadata.updated_at, '2026-08-12');
        assert.equal(targetAnswer.metadata.invalidated_by_canonical_merge, 'cq_source');
        assert.equal(fs.existsSync(path.join(fixture.paths.answersDir, 'cq_source.md')), false);
        assert.equal(fs.existsSync(path.join(fixture.paths.answerArchiveDir, 'cq_source.md')), true);

        const hotspot = readJson(getIndexPaths(fixture.paths.indexDir).hotspot);
        assert.equal(hotspot.entries.length, 1);
        assert.equal(hotspot.entries[0].canonical_id, 'cq_target');
        assert.equal(hotspot.entries[0].frequency, 2);

        const history = readJson(fixture.paths.mergeHistory);
        assert.equal(history.items.length, 1);
        assert.equal(history.items[0].target, 'cq_target');
        assert.equal(history.items[0].source, 'cq_source');
        assert.equal(history.items[0].merged_at, '2026-08-12T06:44:00.000Z');
        assert.equal(history.items[0].reason, 'same interview knowledge point');

        assert.equal(fs.existsSync(fixture.paths.journal), false);
        assert.equal(fs.existsSync(fixture.paths.lock), false);
    } finally {
        fs.rmSync(fixture.root, { recursive: true, force: true });
    }
});
