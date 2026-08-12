'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalQuestionOwnershipRepository answers only one question:
 * which Canonical records currently declare a given question_id?
 *
 * findOwners(questionId) returns:
 *   { canonical_ids, resource, revision }
 *
 * This preserves legacy Accept conflict detection even when Question binding
 * rows and Canonical records are temporarily inconsistent.
 */
function assertCanonicalQuestionOwnershipRepository(repository) {
    return assertPort(
        repository,
        'CanonicalQuestionOwnershipRepository',
        ['findOwners'],
    );
}

module.exports = {
    assertCanonicalQuestionOwnershipRepository,
};
