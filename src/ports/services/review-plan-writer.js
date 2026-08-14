'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewPlanWriter is the narrow outbound publication boundary for
 * review prepare plans. Application decides which rows belong in the plan;
 * Infrastructure owns path safety, Markdown rendering, and filesystem writes.
 */
function assertReviewPlanWriter(writer) {
    return assertPort(
        writer,
        'ReviewPlanWriter',
        ['write'],
    );
}

module.exports = {
    assertReviewPlanWriter,
};
