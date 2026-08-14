'use strict';

function clone(value) {
    return structuredClone(value);
}

function compareMembers(left, right) {
    return String(left?.question_id || '').localeCompare(String(right?.question_id || ''))
        || String(left?.source_note_id || '').localeCompare(String(right?.source_note_id || ''), 'zh')
        || Number(left?.source_question_index ?? 0) - Number(right?.source_question_index ?? 0);
}

function memberRef(question) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
    };
}

function assertHotspot(hotspot) {
    if (!hotspot || typeof hotspot !== 'object' || Array.isArray(hotspot)) {
        throw new Error('Dedup hotspot is required');
    }
    if (!hotspot.question_id) throw new Error('Dedup hotspot question_id is required');
    if (!Array.isArray(hotspot.refs)) throw new Error(`Dedup hotspot refs are required for ${hotspot.question_id}`);
}

/**
 * Detect reviewable duplicate groups from the persisted hotspot index facts.
 *
 * Historical hotspot semantics are intentionally preserved:
 * - only unassigned, valid-for-library Question rows are eligible;
 * - a hotspot is reviewable when at least two eligible rows remain;
 * - distinct source count is evidence metadata, not an eligibility threshold.
 *
 * This policy emits detection evidence only. It never creates Canonical IDs,
 * RelationDecisions, or mutation commands.
 */
function detectHotspotQuestionClusters(hotspots, questions) {
    if (!Array.isArray(hotspots)) throw new Error('Dedup hotspots must be an array');
    if (!Array.isArray(questions)) throw new Error('Dedup hotspot questions must be an array');

    const questionsById = new Map();
    for (const question of questions) {
        if (!question?.question_id) continue;
        if (!questionsById.has(question.question_id)) questionsById.set(question.question_id, []);
        questionsById.get(question.question_id).push(question);
    }

    const clusters = [];
    for (const hotspot of hotspots) {
        assertHotspot(hotspot);
        if (hotspot.canonical_id) continue;

        const eligible = [...(questionsById.get(hotspot.question_id) || [])]
            .filter((question) => question?.is_valid_for_library && !question?.canonical_id)
            .sort(compareMembers);
        if (eligible.length < 2) continue;

        const questionIds = [...new Set(eligible.map((question) => question.question_id))]
            .sort((left, right) => String(left).localeCompare(String(right)));
        const sourceNoteIds = [...new Set(eligible.map((question) => question.source_note_id))];
        const companies = [...new Set(eligible.map((question) => question.company || '未知'))];
        const anchorQuestionId = questionIds[0];

        clusters.push({
            anchor_question_id: anchorQuestionId,
            question_ids: questionIds,
            member_count: eligible.length,
            distinct_source_count: sourceNoteIds.length,
            company_count: companies.length,
            members: eligible.map(memberRef),
            evidence: [{
                signal: 'hotspot_question_id',
                question_id: anchorQuestionId,
                eligible_member_count: eligible.length,
                indexed_frequency: Number(hotspot.frequency || 0),
                matched: true,
            }],
        });
    }

    return clusters
        .sort((left, right) =>
            right.member_count - left.member_count
            || right.company_count - left.company_count
            || String(left.anchor_question_id).localeCompare(String(right.anchor_question_id))
        )
        .map((cluster) => Object.freeze({
            anchor_question_id: cluster.anchor_question_id,
            question_ids: [...cluster.question_ids],
            member_count: cluster.member_count,
            distinct_source_count: cluster.distinct_source_count,
            members: cluster.members.map(clone),
            evidence: cluster.evidence.map(clone),
        }));
}

module.exports = {
    detectHotspotQuestionClusters,
};
