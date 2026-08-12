'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    invalidateAnswerForCanonicalMerge,
    planSourceAnswerArchive,
} = require('../src/domain/answer/merge-invalidation-policy');
const { planCanonicalAnswerMerge } = require('../src/application/canonical/answer-merge-plan');
const { assertAnswerRepository } = require('../src/ports/repositories/answer-repository');

function answer(canonicalId, metadataOverrides = {}) {
    return {
        canonical_id: canonicalId,
        metadata: {
            schema_version: 'answer.v1',
            canonical_id: canonicalId,
            version: 3,
            status: 'draft',
            quality_tier: 'long_tail_baseline',
            updated_at: '2026-08-01',
            ...metadataOverrides,
        },
        content: `# ${canonicalId}`,
    };
}

test('ready target answer is invalidated with legacy metadata semantics', () => {
    const metadata = answer('cq_target', {
        status: 'ready',
        quality_tier: 'long_tail_baseline',
        version: 7,
        custom_field: 'keep-me',
    }).metadata;
    const before = structuredClone(metadata);

    const next = invalidateAnswerForCanonicalMerge(metadata, 'cq_source', '2026-08-12');

    assert.equal(next.status, 'needs_update');
    assert.equal(next.quality_tier, 'needs_update');
    assert.equal(next.version, 8);
    assert.equal(next.updated_at, '2026-08-12');
    assert.equal(next.invalidated_by_canonical_merge, 'cq_source');
    assert.equal(next.custom_field, 'keep-me');
    assert.deepEqual(metadata, before);
});

test('curated target answer is invalidated even when status is not ready', () => {
    const next = invalidateAnswerForCanonicalMerge(
        answer('cq_target', {
            status: 'draft',
            quality_tier: 'curated',
            version: 1,
        }).metadata,
        'cq_source',
        '2026-08-12',
    );

    assert.equal(next.status, 'needs_update');
    assert.equal(next.quality_tier, 'needs_update');
    assert.equal(next.version, 2);
});

test('non-ready non-curated target answer is left unchanged by returning no invalidation', () => {
    assert.equal(
        invalidateAnswerForCanonicalMerge(
            answer('cq_target', { status: 'draft', quality_tier: 'long_tail_baseline' }).metadata,
            'cq_source',
            '2026-08-12',
        ),
        null,
    );
    assert.equal(invalidateAnswerForCanonicalMerge(null, 'cq_source', '2026-08-12'), null);
});

test('source answer archive intent preserves source status without filesystem details', () => {
    const archive = planSourceAnswerArchive(
        answer('cq_source', { status: 'ready' }),
        false,
        'cq_target',
    );

    assert.deepEqual(archive, {
        canonical_id: 'cq_source',
        target_canonical_id: 'cq_target',
        source_answer_status: 'ready',
        reason: 'canonical_merge',
    });
    assert.doesNotMatch(JSON.stringify(archive), /review\/answers|archive\/answers|\.md|filePath/i);
});

test('source answer archive uses draft fallback and rejects an existing archive', () => {
    const source = answer('cq_source');
    delete source.metadata.status;

    assert.equal(
        planSourceAnswerArchive(source, false, 'cq_target').source_answer_status,
        'draft',
    );
    assert.throws(
        () => planSourceAnswerArchive(source, true, 'cq_target'),
        /Source answer archive already exists for cq_source/,
    );
    assert.equal(planSourceAnswerArchive(null, true, 'cq_target'), null);
});

test('answer merge planner materializes target invalidation and source archive as semantic intent', () => {
    const target = answer('cq_target', {
        status: 'ready',
        quality_tier: 'curated',
        version: 4,
    });
    const source = answer('cq_source', { status: 'draft' });
    const targetBefore = structuredClone(target);
    const sourceBefore = structuredClone(source);

    const plan = planCanonicalAnswerMerge({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetAnswer: target,
        sourceAnswer: source,
        sourceArchiveExists: false,
        updatedAt: '2026-08-12',
    });

    assert.equal(Object.isFrozen(plan), true);
    assert.equal(Object.isFrozen(plan.target_invalidation), true);
    assert.equal(Object.isFrozen(plan.target_invalidation.next_metadata), true);
    assert.equal(plan.target_invalidation.canonical_id, 'cq_target');
    assert.equal(plan.target_invalidation.source_canonical_id, 'cq_source');
    assert.equal(plan.target_invalidation.next_metadata.status, 'needs_update');
    assert.equal(plan.target_invalidation.next_metadata.quality_tier, 'needs_update');
    assert.equal(plan.target_invalidation.next_metadata.version, 5);
    assert.deepEqual(plan.source_archive, {
        canonical_id: 'cq_source',
        target_canonical_id: 'cq_target',
        source_answer_status: 'draft',
        reason: 'canonical_merge',
    });
    assert.deepEqual(target, targetBefore);
    assert.deepEqual(source, sourceBefore);
});

test('answer merge planner emits no-op intents when answers do not require changes', () => {
    const plan = planCanonicalAnswerMerge({
        targetCanonicalId: 'cq_target',
        sourceCanonicalId: 'cq_source',
        targetAnswer: answer('cq_target', {
            status: 'draft',
            quality_tier: 'long_tail_baseline',
        }),
        sourceAnswer: null,
        sourceArchiveExists: true,
        updatedAt: '2026-08-12',
    });

    assert.equal(plan.target_invalidation, null);
    assert.equal(plan.source_archive, null);
});

test('answer merge planner rejects archive conflicts and inconsistent snapshots before mutation', () => {
    assert.throws(
        () => planCanonicalAnswerMerge({
            targetCanonicalId: 'cq_target',
            sourceCanonicalId: 'cq_source',
            targetAnswer: null,
            sourceAnswer: answer('cq_source'),
            sourceArchiveExists: true,
            updatedAt: '2026-08-12',
        }),
        /Source answer archive already exists for cq_source/,
    );

    assert.throws(
        () => planCanonicalAnswerMerge({
            targetCanonicalId: 'cq_target',
            sourceCanonicalId: 'cq_source',
            targetAnswer: answer('cq_wrong'),
            sourceAnswer: null,
            updatedAt: '2026-08-12',
        }),
        /Target answer canonical_id mismatch/,
    );

    assert.throws(
        () => planCanonicalAnswerMerge({
            targetCanonicalId: 'cq_target',
            sourceCanonicalId: 'cq_source',
            targetAnswer: null,
            sourceAnswer: answer('cq_wrong'),
            updatedAt: '2026-08-12',
        }),
        /Source answer canonical_id mismatch/,
    );
});

test('AnswerRepository contract remains narrow and merge-specific', () => {
    const repository = { loadMergeState() {} };
    assert.equal(assertAnswerRepository(repository), repository);
    assert.throws(() => assertAnswerRepository({}), /AnswerRepository\.loadMergeState\(\) is required/);
});
