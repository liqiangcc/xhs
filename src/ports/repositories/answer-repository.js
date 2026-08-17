'use strict';

const { assertPort } = require('../port-contract');

/**
 * AnswerRepository exposes the read snapshot needed to plan a Canonical merge.
 *
 * loadMergeState(targetCanonicalId, sourceCanonicalId) returns:
 *   {
 *     target_answer,
 *     source_answer,
 *     source_archive_exists,
 *     resource,
 *     revision,
 *   }
 *
 * Answer values expose semantic content/metadata only. resource/revision are
 * opaque concurrency tokens; filesystem answer/archive paths stay inside the
 * concrete adapter.
 */
function assertAnswerRepository(repository) {
    return assertPort(repository, 'AnswerRepository', ['loadMergeState']);
}

module.exports = {
    assertAnswerRepository,
};
