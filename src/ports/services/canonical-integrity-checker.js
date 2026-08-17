'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalIntegrityChecker performs a global read-only consistency check.
 *
 * check() returns a storage-agnostic canonical_quality_report.v1 object.
 * The Application layer may use report.ok for post-commit compatibility while
 * Infrastructure owns how current Canonical and Question state is loaded.
 */
function assertCanonicalIntegrityChecker(checker) {
    return assertPort(
        checker,
        'CanonicalIntegrityChecker',
        ['check'],
    );
}

module.exports = {
    assertCanonicalIntegrityChecker,
};
