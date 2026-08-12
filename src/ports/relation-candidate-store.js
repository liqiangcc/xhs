'use strict';

const { assertPort } = require('./port-contract');

/**
 * RelationCandidateStore persists review queues produced by Dedup detection.
 *
 * replaceQueue(queue) atomically replaces the current queue for the queue's
 * scope/seed and returns opaque storage metadata:
 *   { resource, revision, candidate_count }
 *
 * This store contains pending review evidence only. It is intentionally not a
 * CanonicalCandidateRepository and cannot authorize Canonical mutation.
 */
function assertRelationCandidateStore(store) {
    return assertPort(
        store,
        'RelationCandidateStore',
        ['replaceQueue'],
    );
}

module.exports = {
    assertRelationCandidateStore,
};
