'use strict';

const { assertPort } = require('../port-contract');

/**
 * DedupQuestionRetrievalRepository resolves opaque retrieval refs into the
 * Question facts consumed by Dedup Application/Domain policies.
 *
 * findByRefs(refs) returns:
 *   { questions, resource, revision }
 *
 * The adapter owns ref resolution and revision generation. Application must
 * not know whether the backing source is JSONL, SQLite, MCP, or another store.
 */
function assertDedupQuestionRetrievalRepository(repository) {
    return assertPort(
        repository,
        'DedupQuestionRetrievalRepository',
        ['findByRefs'],
    );
}

module.exports = {
    assertDedupQuestionRetrievalRepository,
};
