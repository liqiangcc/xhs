'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewRepository exposes the read snapshot needed to plan a Canonical merge.
 *
 * loadMergeState(targetCanonicalId, sourceCanonicalId) returns:
 *   {
 *     target_items,
 *     source_items,
 *     source_session_event_count,
 *     resource,
 *     revision,
 *   }
 *
 * resource/revision are opaque concurrency tokens. The snapshot intentionally
 * does not expose progress.json or review/sessions filesystem paths.
 */
function assertReviewRepository(repository) {
    return assertPort(repository, 'ReviewRepository', ['loadMergeState']);
}

module.exports = {
    assertReviewRepository,
};
