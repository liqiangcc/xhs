'use strict';

const { assertPort } = require('../port-contract');

/**
 * QuestionCatalogRepository is the read-side catalog port for Question rows.
 *
 * list() returns storage-agnostic Question records. Cross-catalog aggregation,
 * filtering, counting, and response DTO semantics belong to Application.
 */
function assertQuestionCatalogRepository(repository) {
    return assertPort(repository, 'QuestionCatalogRepository', ['list']);
}

module.exports = {
    assertQuestionCatalogRepository,
};
