'use strict';

const { pickPriority, computePriority } = require('./priority-policy');
const { validateDomain, normalizeEntity } = require('../question/taxonomy-normalization');

function countValues(values) {
    const counts = new Map();
    for (const value of values) counts.set(value, (counts.get(value) || 0) + 1);
    return counts;
}

function pickTop(values, fallback) {
    const counts = countValues(values.filter(Boolean));
    const sorted = [...counts.entries()]
        .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]), 'zh'));
    return sorted[0]?.[0] || fallback;
}

function normalizedDomain(question, taxonomy) {
    const result = validateDomain(question.domain || {}, taxonomy);
    return result.valid
        ? result.normalized_domain
        : (question.domain || { l1: '其他', l2: '其他' });
}

/**
 * Recompute Canonical aggregate fields from the full set of Question rows that
 * belong to its question_ids. This preserves the legacy post-merge refresh
 * semantics without depending on filesystem, CLI, or config loading.
 */
function refreshCanonicalFromQuestions(record, questionRows, taxonomy) {
    if (!record || typeof record !== 'object' || !record.canonical_id) {
        throw new Error('canonical record is required');
    }
    if (!Array.isArray(questionRows)) throw new Error('questionRows must be an array');
    if (!taxonomy || typeof taxonomy !== 'object') throw new Error('taxonomy is required');

    const questionIds = new Set(record.question_ids || []);
    const rows = questionRows.filter((question) => questionIds.has(question.question_id));
    const companies = [...new Set(rows.map((question) => question.company || '未知'))]
        .sort((a, b) => a.localeCompare(b, 'zh'));

    const entities = [];
    for (const question of rows) {
        for (const entity of question.tech_entities || []) {
            const normalized = normalizeEntity(entity, taxonomy);
            if (normalized) entities.push(normalized);
        }
    }
    const entityCounts = countValues(entities);
    const primaryEntities = entities.length
        ? [...new Set(entities)].sort((a, b) =>
            (entityCounts.get(b) || 0) - (entityCounts.get(a) || 0)
            || a.localeCompare(b, 'zh')
        ).slice(0, 8)
        : (record.primary_entities || []);

    const domains = rows.map((question) => normalizedDomain(question, taxonomy));
    const derivedPrimaryDomain = domains.length
        ? JSON.parse(pickTop(
            domains.map((domain) => JSON.stringify(domain)),
            JSON.stringify(record.primary_domain || { l1: '其他', l2: '其他' }),
        ))
        : (record.primary_domain || { l1: '其他', l2: '其他' });
    const domainOverride = record.primary_domain_override
        ? validateDomain(record.primary_domain_override, taxonomy)
        : null;
    const primaryDomain = domainOverride?.valid
        ? domainOverride.normalized_domain
        : derivedPrimaryDomain;

    const frequency = rows.length || Number(record.frequency || 0);
    return {
        ...record,
        aliases: [...new Set(record.aliases || [record.canonical_title].filter(Boolean))]
            .sort((a, b) => String(a).length - String(b).length || String(a).localeCompare(String(b), 'zh')),
        question_ids: [...questionIds].sort(),
        primary_domain: primaryDomain,
        primary_entities: primaryEntities,
        companies,
        frequency,
        review_priority: pickPriority(
            record.review_priority,
            computePriority(frequency, companies.length),
        ),
        schema_version: 'canonical_question.v1',
    };
}

module.exports = {
    refreshCanonicalFromQuestions,
};
