'use strict';

const { assertPort } = require('../port-contract');

/**
 * RelationDecisionRepository reads persisted explicit review decisions.
 *
 * get(relationCandidateKey) returns null or an opaque snapshot:
 *   { decision, resource, revision }
 *
 * The repository exposes review facts only. It has no Apply or Canonical
 * mutation capability.
 */
function assertRelationDecisionRepository(repository) {
    return assertPort(
        repository,
        'RelationDecisionRepository',
        ['get'],
    );
}

module.exports = {
    assertRelationDecisionRepository,
};
