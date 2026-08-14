'use strict';

const { readJson } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function createFsReviewProgressReader(options = {}) {
    if (!options.root) throw new Error('Filesystem review progress reader root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        load() {
            return readJson(paths.reviewProgress, {
                schema_version: 'review_progress_store.v1',
                updated_at: null,
                items: [],
            });
        },
    };
}

module.exports = {
    createFsReviewProgressReader,
};
