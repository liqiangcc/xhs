'use strict';

const { assertPort } = require('../port-contract');

/**
 * DedupHotspotRetrievalRepository exposes the read-only hotspot detection
 * input without coupling Application to index files or index-store shapes.
 *
 * listHotspots() returns:
 *   { hotspots, resource, revision }
 *
 * Each hotspot may carry opaque Question refs that Application forwards to
 * DedupQuestionRetrievalRepository. The repository owns how hotspot facts are
 * materialized and revised.
 */
function assertDedupHotspotRetrievalRepository(repository) {
    return assertPort(
        repository,
        'DedupHotspotRetrievalRepository',
        ['listHotspots'],
    );
}

module.exports = {
    assertDedupHotspotRetrievalRepository,
};
