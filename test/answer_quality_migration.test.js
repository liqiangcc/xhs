'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir } = require('../scripts/lib/io');
const { parseAnswerMetadata } = require('../scripts/lib/answer_store');
const { runQualityMigrate } = require('../scripts/commands/answer');

function answer(metadata, title) {
    return [
        `<!-- xhs-answer: ${JSON.stringify(metadata)} -->`,
        `# ${title}`,
        '',
        '## 核心结论',
        '',
        '内容。',
        '',
    ].join('\n');
}

function setup() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-quality-migration-'));
    const answersDir = path.join(root, 'review', 'answers');
    ensureDir(answersDir);
    fs.writeFileSync(path.join(answersDir, 'cq_curated.md'), answer({
        schema_version: 'answer.v1',
        canonical_id: 'cq_curated',
        version: 2,
        status: 'ready',
        updated_at: '2026-07-10',
    }, '精选答案'), 'utf8');
    fs.writeFileSync(path.join(answersDir, 'cq_long.md'), answer({
        schema_version: 'answer.v1',
        canonical_id: 'cq_long',
        version: 1,
        status: 'ready',
        updated_at: '2026-07-10',
        answer_type: 'concept',
        quality_tier: 'long_tail_baseline',
        generator_version: 'long_tail.v1',
    }, '长尾答案'), 'utf8');
    return root;
}

test('quality migration dry-run has exact scope and does not write', () => {
    const root = setup();
    const curatedPath = path.join(root, 'review', 'answers', 'cq_curated.md');
    const longPath = path.join(root, 'review', 'answers', 'cq_long.md');
    const beforeCurated = fs.readFileSync(curatedPath, 'utf8');
    const beforeLong = fs.readFileSync(longPath, 'utf8');

    const result = runQualityMigrate({
        root,
        check: true,
        noWrite: true,
        expectedCurated: 1,
        expectedLongTail: 1,
    });
    assert.equal(result.ok, true);
    assert.equal(result.dry_run, true);
    assert.equal(result.changed_count, 2);
    assert.equal(fs.readFileSync(curatedPath, 'utf8'), beforeCurated);
    assert.equal(fs.readFileSync(longPath, 'utf8'), beforeLong);
    fs.rmSync(root, { recursive: true, force: true });
});

test('quality migration writes curated tier and downgrades baseline idempotently', () => {
    const root = setup();
    const options = { root, expectedCurated: 1, expectedLongTail: 1 };
    const first = runQualityMigrate(options);
    assert.equal(first.ok, true);
    assert.equal(first.migrated, true);
    assert.equal(first.changed_count, 2);

    const curated = parseAnswerMetadata(fs.readFileSync(path.join(root, 'review', 'answers', 'cq_curated.md'), 'utf8'));
    const longTail = parseAnswerMetadata(fs.readFileSync(path.join(root, 'review', 'answers', 'cq_long.md'), 'utf8'));
    assert.equal(curated.status, 'ready');
    assert.equal(curated.quality_tier, 'curated');
    assert.equal(longTail.status, 'needs_update');
    assert.equal(longTail.quality_tier, 'long_tail_baseline');

    const second = runQualityMigrate(options);
    assert.equal(second.ok, true);
    assert.equal(second.changed_count, 0);
    fs.rmSync(root, { recursive: true, force: true });
});

test('quality migration fails closed on ambiguous tiers and scope drift', () => {
    const root = setup();
    const ambiguousPath = path.join(root, 'review', 'answers', 'cq_ambiguous.md');
    fs.writeFileSync(ambiguousPath, answer({
        schema_version: 'answer.v1',
        canonical_id: 'cq_ambiguous',
        version: 1,
        status: 'draft',
        updated_at: '2026-07-10',
    }, '不明确答案'), 'utf8');

    const result = runQualityMigrate({ root, check: true, expectedCurated: 2, expectedLongTail: 1 });
    assert.equal(result.ok, false);
    assert.equal(result.error_count, 2);
    assert.deepEqual(result.errors.map((item) => item.error).sort(), [
        'ambiguous_quality_tier',
        'curated_scope_mismatch',
    ]);
    fs.rmSync(root, { recursive: true, force: true });
});
