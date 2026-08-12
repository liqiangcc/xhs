'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const test = require('node:test');
const assert = require('node:assert/strict');

const { computeQuestionId } = require('../scripts/lib/hash');
const { readJsonl, writeJson, writeJsonl } = require('../scripts/lib/io');

const CLI = path.resolve(__dirname, '..', 'scripts', 'xhs.js');

function makeQuestion(original, noteId, index, company, canonicalId = null) {
    return {
        question_id: computeQuestionId(original),
        original_question: original,
        source_note_id: noteId,
        source_question_index: index,
        company,
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2024',
        date: '未知',
        domain: { l1: '缓存', l2: 'Redis' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: ['Redis'],
        business_context: [],
        is_valid_for_library: true,
        canonical_id: canonicalId,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    };
}

function makeCanonical(canonicalId, title, questionIds, overrides = {}) {
    return {
        canonical_id: canonicalId,
        canonical_title: title,
        aliases: [title],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency: questionIds.length,
        review_priority: 'P0',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
        ...overrides,
    };
}

function makeRoot(prefix) {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function cleanup(root) {
    fs.rmSync(root, { recursive: true, force: true });
}

function runCanonicalCli(root, args) {
    const result = spawnSync(
        process.execPath,
        [CLI, 'canonical', ...args, '--root', root, '--noManifest'],
        { encoding: 'utf8' },
    );
    const stdout = result.stdout.trim();
    return {
        status: result.status,
        stdout,
        stderr: result.stderr.trim(),
        json: stdout ? JSON.parse(stdout) : null,
    };
}

function questionsPath(root) {
    return path.join(root, 'data', 'questions', 'questions.jsonl');
}

function canonicalPath(root) {
    return path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
}

function writeAnswer(root, canonicalId, overrides = {}) {
    const dir = path.join(root, 'review', 'answers');
    fs.mkdirSync(dir, { recursive: true });
    const metadata = {
        schema_version: 'answer.v1',
        canonical_id: canonicalId,
        version: 1,
        status: 'needs_update',
        quality_tier: 'long_tail_baseline',
        updated_at: '2026-08-12',
        ...overrides,
    };
    const filePath = path.join(dir, `${canonicalId}.md`);
    fs.writeFileSync(filePath, `<!-- xhs-answer: ${JSON.stringify(metadata)} -->\n# ${canonicalId}\n`, 'utf8');
    return filePath;
}

function snapshotFiles(root) {
    const files = new Map();
    function visit(dir) {
        if (!fs.existsSync(dir)) return;
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
            const fullPath = path.join(dir, entry.name);
            if (entry.isDirectory()) visit(fullPath);
            else files.set(path.relative(root, fullPath), fs.readFileSync(fullPath, 'utf8'));
        }
    }
    visit(root);
    return files;
}

function assertSnapshotEqual(actual, expected) {
    assert.deepEqual([...actual.keys()].sort(), [...expected.keys()].sort());
    for (const [name, content] of expected) assert.equal(actual.get(name), content, name);
}

test('characterizes canonical stats CLI JSON and exit code', () => {
    const root = makeRoot('xhs-canonical-char-stats-');
    try {
        const targetId = 'cq_redis_fast';
        const sourceId = 'cq_redis_ttl';
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', targetId);
        const q2 = makeQuestion('Redis 过期策略是什么？', 'note-b', 0, '字节', sourceId);
        writeJsonl(questionsPath(root), [q1, q2]);
        writeJsonl(canonicalPath(root), [
            makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
            makeCanonical(sourceId, 'Redis 过期策略是什么？', [q2.question_id]),
        ]);

        const result = runCanonicalCli(root, ['stats', '--limit', '10']);
        assert.equal(result.status, 0);
        assert.equal(result.stderr, '');
        assert.equal(result.json.schema_version, 'canonical_stats.v1');
        assert.equal(result.json.canonical_count, 2);
        assert.equal(result.json.canonical_question_id_count, 2);
        assert.equal(result.json.assigned_question_rows, 2);
        assert.equal(result.json.top_canonical.length, 2);
    } finally {
        cleanup(root);
    }
});

test('characterizes canonical accept CLI output and persisted side effects', () => {
    const root = makeRoot('xhs-canonical-char-accept-');
    try {
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团');
        const canonicalId = 'cq_redis_fast';
        writeJsonl(questionsPath(root), [q1]);
        writeJsonl(canonicalPath(root), []);
        writeJson(path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json'), {
            schema_version: 'canonical_candidates.v1',
            candidates: [{
                candidate_id: 'cand_redis_fast',
                canonical_title: 'Redis 为什么快？',
                aliases: ['Redis 为什么快？'],
                question_ids: [q1.question_id],
                primary_domain: { l1: '缓存', l2: 'Redis' },
                primary_entities: ['Redis'],
                companies: ['美团'],
                frequency: 1,
                review_priority: 'P2',
            }],
        });

        const result = runCanonicalCli(root, [
            'accept',
            '--candidate-id', 'cand_redis_fast',
            '--canonical-id', canonicalId,
        ]);
        assert.equal(result.status, 0);
        assert.equal(result.stderr, '');
        assert.equal(result.json.ok, true);
        assert.equal(result.json.canonical_id, canonicalId);
        assert.equal(result.json.updated_question_rows, 1);
        assert.equal(readJsonl(questionsPath(root))[0].canonical_id, canonicalId);
        assert.equal(readJsonl(canonicalPath(root))[0].canonical_id, canonicalId);
        for (const name of ['entity_index.json', 'company_index.json', 'domain_index.json', 'hotspot_index.json']) {
            assert.equal(fs.existsSync(path.join(root, 'data', 'indexes', name)), true, name);
        }
        assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'runs', 'latest_canonical_accept.json')), false);
    } finally {
        cleanup(root);
    }
});

test('characterizes merge then split CLI state transitions', () => {
    const root = makeRoot('xhs-canonical-char-merge-split-');
    try {
        const targetId = 'cq_redis_fast_target';
        const sourceId = 'cq_redis_fast_source';
        const splitId = 'cq_redis_single_thread';
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', targetId);
        const q2 = makeQuestion('Redis 单线程为什么快？', 'note-b', 0, '字节', sourceId);
        writeJsonl(questionsPath(root), [q1, q2]);
        writeJsonl(canonicalPath(root), [
            makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
            makeCanonical(sourceId, 'Redis 单线程为什么快？', [q2.question_id]),
        ]);

        const merged = runCanonicalCli(root, [
            'merge', '--target', targetId, '--source', sourceId, '--reason', 'same_topic',
        ]);
        assert.equal(merged.status, 0);
        assert.equal(merged.json.ok, true);
        assert.equal(merged.json.canonical_count, 1);
        assert.equal(merged.json.assigned_question_rows, 2);
        assert.deepEqual(merged.json.review_migration, {
            source_progress_found: false,
            target_progress_found: false,
            migrated_session_event_count: 0,
        });
        assert.equal(merged.json.invalidated_target_answer, null);
        assert.equal(merged.json.archived_source_answer, null);
        assert.equal(readJsonl(canonicalPath(root)).length, 1);
        assert.equal(readJsonl(questionsPath(root)).find((q) => q.question_id === q2.question_id).canonical_id, targetId);

        const split = runCanonicalCli(root, [
            'split',
            '--canonical-id', targetId,
            '--question-id', q2.question_id,
            '--new-canonical-id', splitId,
            '--title', 'Redis 单线程为什么快？',
        ]);
        assert.equal(split.status, 0);
        assert.equal(split.json.ok, true);
        assert.equal(readJsonl(canonicalPath(root)).length, 2);
        assert.equal(readJsonl(questionsPath(root)).find((q) => q.question_id === q2.question_id).canonical_id, splitId);
    } finally {
        cleanup(root);
    }
});

test('characterizes canonical check: validation failure is JSON ok=false but process exit remains zero', () => {
    const root = makeRoot('xhs-canonical-char-check-');
    try {
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', 'cq_missing');
        writeJsonl(questionsPath(root), [q1]);
        writeJsonl(canonicalPath(root), []);

        const result = runCanonicalCli(root, ['check', '--noWrite']);
        assert.equal(result.status, 0);
        assert.equal(result.stderr, '');
        assert.equal(result.json.ok, false);
        assert.equal(result.json.orphan_binding_count, 1);
    } finally {
        cleanup(root);
    }
});

test('characterizes accept conflict: exits one and leaves persisted state unchanged', () => {
    const root = makeRoot('xhs-canonical-char-accept-conflict-');
    try {
        const existingId = 'cq_existing_redis';
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', existingId);
        writeJsonl(questionsPath(root), [q1]);
        writeJsonl(canonicalPath(root), [makeCanonical(existingId, 'Redis 为什么快？', [q1.question_id])]);
        writeJson(path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json'), {
            schema_version: 'canonical_candidates.v1',
            candidates: [{
                candidate_id: 'cand_conflict',
                canonical_title: 'Redis 为什么快？',
                aliases: ['Redis 为什么快？'],
                question_ids: [q1.question_id],
                primary_domain: { l1: '缓存', l2: 'Redis' },
                primary_entities: ['Redis'],
                companies: ['美团'],
                frequency: 1,
                review_priority: 'P2',
            }],
        });
        const before = snapshotFiles(root);

        const result = runCanonicalCli(root, [
            'accept', '--candidate-id', 'cand_conflict', '--canonical-id', 'cq_new_redis',
        ]);
        assert.equal(result.status, 1);
        assert.match(result.stderr, /already belongs to cq_existing_redis/);
        assert.equal(result.stdout, '');
        assertSnapshotEqual(snapshotFiles(root), before);
    } finally {
        cleanup(root);
    }
});

test('characterizes merge archive preflight failure: exits one before mutations', () => {
    const root = makeRoot('xhs-canonical-char-archive-conflict-');
    try {
        const targetId = 'cq_redis_target';
        const sourceId = 'cq_redis_source';
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', targetId);
        const q2 = makeQuestion('Redis 为什么这么快？', 'note-b', 0, '字节', sourceId);
        writeJsonl(questionsPath(root), [q1, q2]);
        writeJsonl(canonicalPath(root), [
            makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
            makeCanonical(sourceId, 'Redis 为什么这么快？', [q2.question_id]),
        ]);
        writeAnswer(root, sourceId);
        const archiveDir = path.join(root, 'review', 'archive', 'answers');
        fs.mkdirSync(archiveDir, { recursive: true });
        fs.writeFileSync(path.join(archiveDir, `${sourceId}.md`), 'existing archive\n', 'utf8');
        const before = snapshotFiles(root);

        const result = runCanonicalCli(root, [
            'merge', '--target', targetId, '--source', sourceId, '--reason', 'duplicate',
        ]);
        assert.equal(result.status, 1);
        assert.match(result.stderr, /Source answer archive already exists/);
        assertSnapshotEqual(snapshotFiles(root), before);
    } finally {
        cleanup(root);
    }
});

test('characterizes duplicate review rows failure: exits one before canonical and answer mutations', () => {
    const root = makeRoot('xhs-canonical-char-review-conflict-');
    try {
        const targetId = 'cq_redis_target';
        const sourceId = 'cq_redis_source';
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', targetId);
        const q2 = makeQuestion('Redis 为什么这么快？', 'note-b', 0, '字节', sourceId);
        writeJsonl(questionsPath(root), [q1, q2]);
        writeJsonl(canonicalPath(root), [
            makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
            makeCanonical(sourceId, 'Redis 为什么这么快？', [q2.question_id]),
        ]);
        writeAnswer(root, sourceId);
        writeJson(path.join(root, 'review', 'progress.json'), {
            schema_version: 'review_progress_store.v1',
            updated_at: '2026-08-12',
            items: [
                { canonical_id: sourceId, status: 'learning', level: 1 },
                { canonical_id: sourceId, status: 'weak', level: 0 },
            ],
        });
        const before = snapshotFiles(root);

        const result = runCanonicalCli(root, [
            'merge', '--target', targetId, '--source', sourceId, '--reason', 'duplicate',
        ]);
        assert.equal(result.status, 1);
        assert.match(result.stderr, /Cannot merge review progress with duplicate rows/);
        assertSnapshotEqual(snapshotFiles(root), before);
    } finally {
        cleanup(root);
    }
});

test('characterizes merge index failure as a fully rolled-back mutation', () => {
    const root = makeRoot('xhs-canonical-char-atomic-rollback-');
    try {
        const targetId = 'cq_redis_target';
        const sourceId = 'cq_redis_source';
        const q1 = makeQuestion('Redis 为什么快？', 'note-a', 0, '美团', targetId);
        const q2 = makeQuestion('Redis 为什么这么快？', 'note-b', 0, '字节', sourceId);
        writeJsonl(questionsPath(root), [q1, q2]);
        writeJsonl(canonicalPath(root), [
            makeCanonical(targetId, 'Redis 为什么快？', [q1.question_id]),
            makeCanonical(sourceId, 'Redis 为什么这么快？', [q2.question_id]),
        ]);
        writeAnswer(root, sourceId);

        // Make the index directory path invalid so publication fails after earlier
        // transaction operations have already been attempted.
        fs.mkdirSync(path.join(root, 'data'), { recursive: true });
        fs.writeFileSync(path.join(root, 'data', 'indexes'), 'not-a-directory\n', 'utf8');
        const before = snapshotFiles(root);

        const result = runCanonicalCli(root, [
            'merge', '--target', targetId, '--source', sourceId, '--reason', 'duplicate',
        ]);
        assert.equal(result.status, 1);
        assert.notEqual(result.stderr, '');

        // Fixed behavior: every formal file is restored to its exact pre-merge bytes.
        assertSnapshotEqual(snapshotFiles(root), before);
        assert.equal(readJsonl(canonicalPath(root)).length, 2);
        assert.equal(readJsonl(questionsPath(root)).find((q) => q.question_id === q2.question_id).canonical_id, sourceId);
        assert.equal(fs.existsSync(path.join(root, 'review', 'answers', `${sourceId}.md`)), true);
        assert.equal(fs.existsSync(path.join(root, 'review', 'archive', 'answers', `${sourceId}.md`)), false);
        assert.equal(fs.existsSync(path.join(root, 'data', 'manifests', 'canonical', 'canonical_merge_history.json')), false);
    } finally {
        cleanup(root);
    }
});
