'use strict';

function uniqueSorted(values, comparator) {
    const items = [...new Set(values || [])];
    return comparator ? items.sort(comparator) : items.sort();
}

function makeCanonicalFromCandidate(candidate, canonicalId, overrides = {}) {
    if (!candidate || typeof candidate !== 'object') throw new Error('canonical candidate is required');
    if (!canonicalId) throw new Error('canonicalId is required');

    const questionIds = uniqueSorted(candidate.question_ids);
    const companies = uniqueSorted(candidate.companies, (a, b) => String(a).localeCompare(String(b), 'zh'));
    const aliases = uniqueSorted(
        candidate.aliases || [candidate.canonical_title].filter(Boolean),
        (a, b) => String(a).length - String(b).length || String(a).localeCompare(String(b), 'zh'),
    );

    return {
        canonical_id: canonicalId,
        canonical_title: overrides.title || candidate.canonical_title,
        aliases,
        question_ids: questionIds,
        primary_domain: candidate.primary_domain || { l1: '其他', l2: '其他' },
        primary_entities: uniqueSorted(
            candidate.primary_entities,
            (a, b) => String(a).localeCompare(String(b), 'zh'),
        ),
        companies,
        frequency: Number(candidate.frequency || questionIds.length),
        review_priority: candidate.review_priority || 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

function extendCanonicalWithCandidate(existing, incoming) {
    if (!existing || typeof existing !== 'object' || !existing.canonical_id) {
        throw new Error('existing canonical record is required');
    }
    if (!incoming || typeof incoming !== 'object' || !incoming.canonical_id) {
        throw new Error('incoming canonical record is required');
    }
    if (existing.canonical_id !== incoming.canonical_id) {
        throw new Error('existing and incoming canonical ids must match');
    }

    return {
        ...structuredClone(existing),
        canonical_title: existing.canonical_title || incoming.canonical_title,
        aliases: uniqueSorted(
            [...(existing.aliases || []), ...(incoming.aliases || [])],
            (a, b) => String(a).length - String(b).length || String(a).localeCompare(String(b), 'zh'),
        ),
        question_ids: uniqueSorted([...(existing.question_ids || []), ...(incoming.question_ids || [])]),
        primary_entities: uniqueSorted(
            [...(existing.primary_entities || []), ...(incoming.primary_entities || [])],
            (a, b) => String(a).localeCompare(String(b), 'zh'),
        ),
        companies: uniqueSorted(
            [...(existing.companies || []), ...(incoming.companies || [])],
            (a, b) => String(a).localeCompare(String(b), 'zh'),
        ),
        frequency: Math.max(Number(existing.frequency || 0), Number(incoming.frequency || 0)),
        answer_status: existing.answer_status || incoming.answer_status || 'missing',
        schema_version: 'canonical_question.v1',
    };
}

function acceptCanonicalCandidate(existing, candidate, canonicalId, overrides = {}) {
    const incoming = makeCanonicalFromCandidate(candidate, canonicalId, overrides);
    return existing ? extendCanonicalWithCandidate(existing, incoming) : incoming;
}

module.exports = {
    makeCanonicalFromCandidate,
    extendCanonicalWithCandidate,
    acceptCanonicalCandidate,
};
