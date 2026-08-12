'use strict';

const { assertPort } = require('./port-contract');

/**
 * CanonicalMutationStore is the single write boundary for a Canonical mutation.
 *
 * preflight(plan)
 *   - verifies opaque expected revisions and adapter-specific preconditions;
 *   - must not publish partial formal state;
 *   - returns an opaque preflight token/result for commit.
 *
 * commit(plan, preflightResult)
 *   - revalidates the preflight token as needed;
 *   - applies the whole semantic plan as an atomic or explicitly recoverable unit;
 *   - must never silently leave an unidentifiable half-completed mutation.
 *
 * The port deliberately does not expose writeFile/saveMany/rename primitives.
 */
function assertCanonicalMutationStore(store) {
    return assertPort(store, 'CanonicalMutationStore', ['preflight', 'commit']);
}

module.exports = {
    assertCanonicalMutationStore,
};
