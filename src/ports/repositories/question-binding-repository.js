'use strict';

const { assertPort } = require('../port-contract');

/**
 * QuestionBindingRepository is a read-oriented outbound port for Canonical use cases.
 *
 * findByCanonical(canonicalId) and findByQuestionId(questionId) return snapshots:
 *   { bindings, resource, revision }
 * where resource/revision are opaque adapter-owned concurrency tokens.
 * Application may carry them into a MutationPlan but must not interpret their
 * format or expose storage paths.
 */
function assertQuestionBindingRepository(repository) {
    return assertPort(
        repository,
        'QuestionBindingRepository',
        ['findByCanonical', 'findByQuestionId'],
    );
}

module.exports = {
    assertQuestionBindingRepository,
};
