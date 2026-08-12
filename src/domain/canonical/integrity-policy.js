'use strict';

const { normalizeQuestionText } = require('../question/normalization-policy');

function questionRef(question) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
    };
}

function normalizedTitle(record) {
    return normalizeQuestionText([
        record.canonical_title,
        ...(record.aliases || []),
    ].join(' '));
}

/**
 * Evaluate global Canonical/Question consistency without I/O.
 *
 * This preserves the legacy canonical check semantics while making the rule
 * reusable by Application post-validation and any future interface.
 */
function evaluateCanonicalIntegrity(records = [], questions = []) {
    if (!Array.isArray(records)) throw new Error('canonical records must be an array');
    if (!Array.isArray(questions)) throw new Error('questions must be an array');

    const rowsByQuestionId = new Map();
    for (const question of questions) {
        if (!rowsByQuestionId.has(question.question_id)) rowsByQuestionId.set(question.question_id, []);
        rowsByQuestionId.get(question.question_id).push(question);
    }

    const recordsById = new Map(records.map((record) => [record.canonical_id, record]));
    const questionIdsByRecord = new Map(
        records.map((record) => [record.canonical_id, new Set(record.question_ids || [])]),
    );
    const canonicalByQuestionId = new Map();
    const duplicateQuestionIds = [];
    const missingQuestionIds = [];
    const bindingMismatches = [];
    const orphanBindings = [];
    const unlistedBindings = [];

    for (const record of records) {
        for (const questionId of record.question_ids || []) {
            if (!rowsByQuestionId.has(questionId)) {
                missingQuestionIds.push({ canonical_id: record.canonical_id, question_id: questionId });
            }
            const owner = canonicalByQuestionId.get(questionId);
            if (owner && owner !== record.canonical_id) {
                duplicateQuestionIds.push({
                    question_id: questionId,
                    canonical_ids: [owner, record.canonical_id].sort(),
                });
            } else {
                canonicalByQuestionId.set(questionId, record.canonical_id);
            }
            for (const question of rowsByQuestionId.get(questionId) || []) {
                if (question.canonical_id !== record.canonical_id) {
                    bindingMismatches.push({
                        question_id: question.question_id,
                        source_note_id: question.source_note_id,
                        source_question_index: question.source_question_index,
                        expected_canonical_id: record.canonical_id,
                        actual_canonical_id: question.canonical_id,
                    });
                }
            }
        }
    }

    for (const question of questions) {
        if (!question.canonical_id) continue;
        const record = recordsById.get(question.canonical_id);
        if (!record) {
            orphanBindings.push(questionRef(question));
        } else if (!questionIdsByRecord.get(record.canonical_id).has(question.question_id)) {
            unlistedBindings.push({
                ...questionRef(question),
                canonical_id: question.canonical_id,
            });
        }
    }

    const suspectedDuplicates = [];
    const recordsByNormalizedTitle = new Map();
    for (const record of records) {
        const normalized = normalizedTitle(record);
        if (!normalized) continue;
        const existing = recordsByNormalizedTitle.get(normalized) || [];
        for (const other of existing) {
            suspectedDuplicates.push({
                canonical_ids: [other.canonical_id, record.canonical_id],
                reason: 'same_normalized_title_or_aliases',
                titles: [other.canonical_title, record.canonical_title],
            });
        }
        existing.push(record);
        recordsByNormalizedTitle.set(normalized, existing);
    }

    const blockingCount = duplicateQuestionIds.length
        + missingQuestionIds.length
        + bindingMismatches.length
        + orphanBindings.length
        + unlistedBindings.length;

    return {
        schema_version: 'canonical_quality_report.v1',
        ok: blockingCount === 0,
        record_count: records.length,
        assigned_question_rows: questions.filter((question) => question.canonical_id).length,
        duplicate_question_id_count: duplicateQuestionIds.length,
        missing_question_id_count: missingQuestionIds.length,
        binding_mismatch_count: bindingMismatches.length,
        orphan_binding_count: orphanBindings.length,
        unlisted_binding_count: unlistedBindings.length,
        suspected_duplicate_count: suspectedDuplicates.length,
        duplicate_question_ids: duplicateQuestionIds,
        missing_question_ids: missingQuestionIds,
        binding_mismatches: bindingMismatches,
        orphan_bindings: orphanBindings,
        unlisted_bindings: unlistedBindings,
        suspected_duplicates: suspectedDuplicates,
    };
}

module.exports = {
    evaluateCanonicalIntegrity,
};
