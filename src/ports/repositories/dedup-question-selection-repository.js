'use strict';

const { assertPort } = require('../port-contract');

/**
 * DedupQuestionSelectionRepository resolves explicit Question identities for a
 * bounded relation review. The caller provides domain-level question_ids;
 * storage lookup, ordering, duplicate source rows and revision generation stay
 * behind the Port.
 *
 * findByQuestionIds(questionIds) returns:
 *   { questions, resource, revision }
 */
function assertDedupQuestionSelectionRepository(repository) {
    return assertPort(
        repository,
        'DedupQuestionSelectionRepository',
        ['findByQuestionIds'],
    );
}

module.exports = {
    assertDedupQuestionSelectionRepository,
};
