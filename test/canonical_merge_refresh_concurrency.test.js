'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const taxonomy = require('../config/taxonomy.json');
const { createMergeCanonicalUseCase } = require('../src/application/canonical/merge-canonical');
const { createInMemoryCanonicalAdapters } = require('../src/infrastructure/in-memory/canonical-adapters');

function canonical(id, questionIds) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: questionIds,
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: [],
        frequency: questionIds.length,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

function binding(questionId, canonicalId, company) {
    return {
        question_id: questionId,
        canonical_id: canonicalId,
        company,
        domain: { l1: '缓存', l2: 'Redis' },
        tech_entities: ['Redis'],
    };
}

test('rejects a merge when a question snapshot used for canonical refresh becomes stale', async () => {
    const adapters = createInMemoryCanonicalAdapters({
        canonicals: [
            canonical('cq_target', ['q1']),
            canonical('cq_source', ['q2']),
        ],
        bindings: [
            binding('q1', 'cq_target', '美团'),
            binding('q2', 'cq_source', '字节'),
        ],
    });
    const before = adapters.snapshot();
    const originalPreflight = adapters.mutationStore.preflight.bind(adapters.mutationStore);
    const mutationStore = {
        ...adapters.mutationStore,
        async preflight(plan) {
            const questionRevision = plan.expected_revisions.find(
                (item) => item.resource === 'question-bindings-by-question:q2',
            );
            assert.ok(questionRevision);
            adapters.mutationStore.bumpRevision(questionRevision.resource);
            return originalPreflight(plan);
        },
    };
    const merge = createMergeCanonicalUseCase({
        canonicalRepository: adapters.canonicalRepository,
        questionBindingRepository: adapters.questionBindingRepository,
        reviewRepository: adapters.reviewRepository,
        answerRepository: adapters.answerRepository,
        mutationStore,
        integrityChecker: {
            async check() {
                return { schema_version: 'canonical_quality_report.v1', ok: true };
            },
        },
        taxonomy,
        clock: () => '2026-08-12T07:00:00.000Z',
    });

    await assert.rejects(
        merge({ target: 'cq_target', source: 'cq_source', reason: 'same' }),
        /Revision mismatch for question-bindings-by-question:q2/,
    );
    assert.deepEqual(adapters.snapshot(), before);
});
