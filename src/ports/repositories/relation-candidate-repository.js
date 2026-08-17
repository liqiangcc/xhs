'use strict';

const { assertPort } = require('../port-contract');

/**
 * RelationCandidateRepository exposes one pending review candidate together
 * with the queue/source revisions that produced it.
 *
 * get(relationCandidateKey) returns null when the candidate is not present in
 * the current review queue, otherwise:
 *   {
 *     candidate,
 *     source_revisions,
 *     resource,
 *     revision,
 *   }
 *
 * `resource`/`revision` identify the current review queue snapshot. Source
 * revisions remain adapter-owned opaque tokens and are revalidated before an
 * explicit decision is recorded.
 */
function assertRelationCandidateRepository(repository) {
    return assertPort(
        repository,
        'RelationCandidateRepository',
        ['get'],
    );
}

module.exports = {
    assertRelationCandidateRepository,
};
