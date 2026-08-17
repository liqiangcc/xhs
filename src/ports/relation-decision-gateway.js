'use strict';

const { assertPort } = require('./port-contract');

/**
 * RelationDecisionGateway is the revision-checked consistency boundary for
 * recording an explicit Dedup review decision.
 *
 * record(decision, { expected_revisions }) must re-read and compare the
 * pending queue revision plus every source revision while holding the adapter
 * lock. Any stale queue or stale Question/index source rejects the append.
 * The append is published atomically and returns opaque storage metadata:
 *   { recorded, resource, revision }
 *
 * This Gateway has no Canonical Merge/Accept/Apply capability.
 */
function assertRelationDecisionGateway(gateway) {
    return assertPort(
        gateway,
        'RelationDecisionGateway',
        ['record'],
    );
}

module.exports = {
    assertRelationDecisionGateway,
};
