'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { evaluateCanonicalIntegrity } = require('../src/domain/canonical/integrity-policy');
const { assertCanonicalIntegrityChecker } = require('../src/ports/services/canonical-integrity-checker');

function canonical(id, title, questionIds) {
    return {
        canonical_id: id,
        canonical_title: title,
        aliases: [title],
        question_ids: questionIds,
    };
}

function question(id, canonicalId, note = 'note', index = 0) {
    return {
        question_id: id,
        canonical_id: canonicalId,
        source_note_id: note,
        source_question_index: index,
    };
}

test('canonical integrity policy reports a valid global state', () => {
    const report = evaluateCanonicalIntegrity(
        [canonical('cq_a', 'Redis 为什么快？', ['q1'])],
        [question('q1', 'cq_a')],
    );

    assert.equal(report.schema_version, 'canonical_quality_report.v1');
    assert.equal(report.ok, true);
    assert.equal(report.record_count, 1);
    assert.equal(report.assigned_question_rows, 1);
    assert.equal(report.duplicate_question_id_count, 0);
    assert.equal(report.missing_question_id_count, 0);
    assert.equal(report.binding_mismatch_count, 0);
    assert.equal(report.orphan_binding_count, 0);
    assert.equal(report.unlisted_binding_count, 0);
});

test('canonical integrity policy preserves legacy blocking categories and duplicate suggestions', () => {
    const report = evaluateCanonicalIntegrity(
        [
            canonical('cq_a', 'Redis 为什么快？', ['q1', 'q_missing']),
            canonical('cq_b', 'Redis为什么快', ['q1']),
            canonical('cq_c', 'Kafka', []),
        ],
        [
            question('q1', 'cq_c', 'note-a', 0),
            question('q_orphan', 'cq_missing_record', 'note-b', 0),
            question('q_unlisted', 'cq_c', 'note-c', 0),
        ],
    );

    assert.equal(report.ok, false);
    assert.equal(report.duplicate_question_id_count, 1);
    assert.equal(report.missing_question_id_count, 1);
    assert.equal(report.binding_mismatch_count, 2);
    assert.equal(report.orphan_binding_count, 1);
    assert.equal(report.unlisted_binding_count, 2);
    assert.equal(report.suspected_duplicate_count, 1);
    assert.deepEqual(report.orphan_bindings[0], {
        question_id: 'q_orphan',
        source_note_id: 'note-b',
        source_question_index: 0,
    });
});

test('CanonicalIntegrityChecker port stays read-only and narrow', () => {
    const checker = { check() {} };
    assert.equal(assertCanonicalIntegrityChecker(checker), checker);
    assert.throws(
        () => assertCanonicalIntegrityChecker({}),
        /CanonicalIntegrityChecker.*check/,
    );
});
