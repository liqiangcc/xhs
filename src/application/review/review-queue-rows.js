'use strict';

function questionMetadata(records, questions) {
    const byCanonicalId = new Map(records.map((record) => [record.canonical_id, {
        levels: new Set(),
        companies: new Set(record.companies || []),
    }]));
    const canonicalByQuestionId = new Map();
    for (const record of records) {
        for (const questionId of record.question_ids || []) {
            canonicalByQuestionId.set(questionId, record.canonical_id);
        }
    }
    for (const question of questions || []) {
        const canonicalId = question.canonical_id || canonicalByQuestionId.get(question.question_id);
        if (!canonicalId || !byCanonicalId.has(canonicalId)) continue;
        const meta = byCanonicalId.get(canonicalId);
        if (question.level) meta.levels.add(String(question.level));
        if (question.company) meta.companies.add(String(question.company));
    }
    return byCanonicalId;
}

function createReviewQueueRows(records, progress, options = {}) {
    const byProgress = new Map((progress.items || []).map((item) => [item.canonical_id, item]));
    const metaByCanonicalId = questionMetadata(records, options.questions || []);
    const issueLinks = new Map((options.issueLinks || []).map((item) => [item.canonical_id, item]));

    return records.map((record) => {
        const meta = metaByCanonicalId.get(record.canonical_id);
        const row = {
            canonical_id: record.canonical_id,
            canonical_title: record.canonical_title,
            review_priority: record.review_priority,
            answer_status: record.answer_status,
            frequency: record.frequency,
            primary_domain: record.primary_domain,
            primary_entities: record.primary_entities || [],
            companies: [...(meta?.companies || new Set(record.companies || []))]
                .sort((a, b) => a.localeCompare(b, 'zh')),
            levels: [...(meta?.levels || new Set())]
                .sort((a, b) => a.localeCompare(b, 'zh')),
            question_ids: record.question_ids || [],
            progress: byProgress.get(record.canonical_id),
        };
        if (options.includeIssues) {
            row.issue_url = issueLinks.get(record.canonical_id)?.issue_url || null;
        }
        return row;
    });
}

module.exports = {
    questionMetadata,
    createReviewQueueRows,
};
