'use strict';

const { assertPort } = require('../port-contract');

/**
 * ReviewProgressRepository owns persistence of the ReviewProgress aggregate
 * when a queue use case needs to initialize missing progress state.
 *
 * snapshot({ date }) returns the current progress plus an opaque revision.
 * save(progress, { expected_revision, date }) performs compare-and-set
 * persistence so a stale queue snapshot cannot overwrite a concurrent mark.
 */
function assertReviewProgressRepository(repository) {
    return assertPort(
        repository,
        'ReviewProgressRepository',
        ['snapshot', 'save'],
    );
}

module.exports = {
    assertReviewProgressRepository,
};
