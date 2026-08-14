'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewPlanPublisher is the narrow outbound publication boundary for
 * review prepare plans. Application decides which rows belong in the plan;
 * Infrastructure owns path safety, Markdown rendering, and filesystem publication.
 */
function assertReviewPlanPublisher(publisher) {
    return assertPort(
        publisher,
        'ReviewPlanPublisher',
        ['publish'],
    );
}

module.exports = {
    assertReviewPlanPublisher,
};
