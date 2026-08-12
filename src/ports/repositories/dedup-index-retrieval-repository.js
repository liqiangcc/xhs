'use strict';

const { assertPort } = require('../port-contract');

/**
 * DedupIndexRetrievalRepository exposes read-only retrieval snapshots used by
 * relation suggestion Application use cases.
 *
 * findEntityRefs(seed) returns:
 *   { refs, resource, revision }
 *
 * `refs` are opaque Question references owned by the retrieval adapters.
 * Application may pass them to DedupQuestionRetrievalRepository but must not
 * interpret them as filesystem paths or persistence identifiers.
 */
function assertDedupIndexRetrievalRepository(repository) {
    return assertPort(
        repository,
        'DedupIndexRetrievalRepository',
        ['findEntityRefs'],
    );
}

module.exports = {
    assertDedupIndexRetrievalRepository,
};
