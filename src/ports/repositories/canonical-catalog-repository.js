'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalCatalogRepository is the read-side catalog port for Canonical records.
 *
 * list() returns storage-agnostic Canonical records. Filtering, ordering, limiting,
 * and response DTO semantics belong to the Application layer, not the adapter.
 */
function assertCanonicalCatalogRepository(repository) {
    return assertPort(repository, 'CanonicalCatalogRepository', ['list']);
}

module.exports = {
    assertCanonicalCatalogRepository,
};
