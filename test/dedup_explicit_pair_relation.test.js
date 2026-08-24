'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { detectExplicitQuestionPair } = require('../src/domain/dedup/explicit-question-pair-detection');
const { assertDedupQuestionSelectionRepository } = require('../src/ports/repositories/dedup-question-selection-repository');

function question(questionId, canonicalId, sourceNoteId) {
    return {
        question_id: questionId,
        original_question: `Question ${questionId}`,
        source_note_id: sourceNoteId,
        source_question_index: 0,
        is_valid_for_library: true,
        canonical_id: canonicalId,
    };
}

test('explicit pair accepts assigned reviewable Questions without relation inference', () => {
    const q1 = question('q_a', 'cq_a', 'note-a');
    const q2 = question('q_b', 'cq_b', 'note-b');
    const [cluster] = detectExplicitQuestionPair([q2, q1], { question_ids: ['q_b', 'q_a'] });

    assert.deepEqual(cluster.question_ids, ['q_a', 'q_b']);
    assert.equal(cluster.member_count, 2);
    assert.equal(cluster.distinct_source_count, 2);
    assert.deepEqual(cluster.evidence, [{
        signal: 'explicit_review_selection',
        question_ids: ['q_a', 'q_b'],
        relation_inference: 'none',
    }]);
    assert.equal(Object.hasOwn(cluster, 'relation'), false);
});

test('explicit pair rejects missing or invalid selected Questions', () => {
    const q1 = question('q_a', 'cq_a', 'note-a');
    const q2 = question('q_b', 'cq_b', 'note-b');
    assert.throws(
        () => detectExplicitQuestionPair([q1, { ...q2, is_valid_for_library: false }], {
            question_ids: ['q_a', 'q_b'],
        }),
        /not reviewable: q_b/,
    );
    assert.throws(
        () => detectExplicitQuestionPair([q1], { question_ids: ['q_a', 'q_b'] }),
        /Question not found: q_b/,
    );
});

test('explicit selection Port remains a narrow boundary', () => {
    const repository = assertDedupQuestionSelectionRepository({ findByQuestionIds() {} });
    assert.equal(repository.findByQuestionIds instanceof Function, true);
    assert.throws(
        () => assertDedupQuestionSelectionRepository({}),
        /findByQuestionIds\(\) is required/,
    );
});
