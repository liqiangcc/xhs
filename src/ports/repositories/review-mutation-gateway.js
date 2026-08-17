'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewMutationGateway is the atomic/recoverable consistency boundary for
 * review mark mutations spanning ReviewProgress and ReviewSession.
 *
 * snapshot({ date }) returns current progress and an opaque revision covering
 * both progress and that date's session resource.
 * commit(mutation) compare-and-sets that revision and publishes the whole
 * semantic mutation as one atomic or explicitly recoverable unit.
 */
function assertReviewMutationGateway(gateway) {
    return assertPort(
        gateway,
        'ReviewMutationGateway',
        ['snapshot', 'commit'],
    );
}

module.exports = {
    assertReviewMutationGateway,
};
