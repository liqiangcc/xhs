'use strict';

const { priorityRank } = require('../../domain/canonical/priority-policy');
const {
    assertCanonicalCatalogRepository,
} = require('../../ports/repositories/canonical-catalog-repository');

function normalizeLimit(value) {
    if (value === undefined || value === null || value === '') return 50;
    return Number(value);
}

function toListRecord(record) {
    return {
        canonical_id: record.canonical_id,
        canonical_title: record.canonical_title,
        review_priority: record.review_priority,
        answer_status: record.answer_status,
        frequency: record.frequency,
        question_ids: record.question_ids,
        companies: record.companies,
        primary_domain: record.primary_domain,
        primary_entities: record.primary_entities,
    };
}

function createListCanonicalsUseCase(options = {}) {
    const catalogRepository = assertCanonicalCatalogRepository(options.catalogRepository);

    return async function listCanonicals(input = {}) {
        const limit = normalizeLimit(input.limit);
        const records = (await catalogRepository.list())
            .filter((record) => !input.priority || record.review_priority === input.priority)
            .filter((record) => !input.answer_status || record.answer_status === input.answer_status)
            .sort((a, b) =>
                priorityRank(a.review_priority) - priorityRank(b.review_priority)
                || b.frequency - a.frequency
                || a.canonical_id.localeCompare(b.canonical_id)
            );

        return {
            schema_version: 'canonical_list.v1',
            total_count: records.length,
            returned_count: Math.min(records.length, limit),
            records: records.slice(0, limit).map(toListRecord),
        };
    };
}

module.exports = {
    createListCanonicalsUseCase,
};
