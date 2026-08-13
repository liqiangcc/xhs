'use strict';

const { assertPort } = require('./port-contract');

/**
 * RelationDecisionStore records explicit review decisions only.
 *
 * record(decision, options) must compare every options.expected_revisions
 * entry against current adapter state immediately before persisting. A stale
 * queue or stale detection source must reject the write.
 *
 * Returns opaque storage metadata such as:
 *   { recorded, resource, revision }
 *
 * This is not a Canonical mutation store and exposes no Merge/Accept/Apply
 * capability.
 */
function assertRelationDecisionStore(store) {
    return assertPort(
        store,
        'RelationDecisionStore',
        ['record'],
    );
}

module.exports = {
    assertRelationDecisionStore,
};
