'use strict';

const {
    assertCanonicalCatalogRepository,
} = require('../../ports/repositories/canonical-catalog-repository');
const {
    assertQuestionCatalogRepository,
} = require('../../ports/repositories/question-catalog-repository');

function normalizeLimit(value) {
    return Number(value || 20);
}

function toTopCanonicalRecord(record) {
    return {
        canonical_id: record.canonical_id,
        canonical_title: record.canonical_title,
        frequency: record.frequency,
        companies: record.companies,
        primary_entities: record.primary_entities,
    };
}

function createCanonicalStatsUseCase(options = {}) {
    const canonicalCatalogRepository = assertCanonicalCatalogRepository(
        options.canonicalCatalogRepository,
    );
    const questionCatalogRepository = assertQuestionCatalogRepository(
        options.questionCatalogRepository,
    );

    return function canonicalStats(input = {}) {
        const canonicalRecords = canonicalCatalogRepository.list();
        const questionRows = questionCatalogRepository.list();
        const canonicalQuestionIds = new Set(
            canonicalRecords.flatMap((record) => record.question_ids || []),
        );
        const limit = normalizeLimit(input.limit);

        return {
            schema_version: 'canonical_stats.v1',
            canonical_count: canonicalRecords.length,
            canonical_question_id_count: canonicalQuestionIds.size,
            assigned_question_rows: questionRows.filter((question) => question.canonical_id).length,
            top_canonical: [...canonicalRecords]
                .sort((a, b) => b.frequency - a.frequency || a.canonical_id.localeCompare(b.canonical_id))
                .slice(0, limit)
                .map(toTopCanonicalRecord),
        };
    };
}

module.exports = {
    createCanonicalStatsUseCase,
};
