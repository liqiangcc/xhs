'use strict';

const { assertPort } = require('./port-contract');

/**
 * RelationCandidatePublisher publishes the pending review queue produced by
 * one Dedup detection scope/seed. replaceQueue(queue) atomically replaces that
 * queue and returns opaque publication metadata:
 *   { resource, revision, candidate_count }
 *
 * The published queue contains review evidence only. It is not a Canonical
 * mutation authority and cannot turn a similarity signal into a Decision.
 */
function assertRelationCandidatePublisher(publisher) {
    return assertPort(
        publisher,
        'RelationCandidatePublisher',
        ['replaceQueue'],
    );
}

module.exports = {
    assertRelationCandidatePublisher,
};
