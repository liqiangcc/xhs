'use strict';

const { assertPort } = require('../port-contract');

/**
 * QuestionBindingRepository is a read-oriented outbound port for Canonical use cases.
 *
 * findByCanonical(canonicalId) returns the bindings currently owned by a Canonical.
 * findByQuestionId(questionId) returns every row/reference for a question id.
 * Implementations may attach an opaque revision token to their returned snapshot.
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
