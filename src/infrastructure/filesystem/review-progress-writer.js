'use strict';

const { writeJson } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function createFsReviewProgressWriter(options = {}) {
    if (!options.root) throw new Error('Filesystem review progress writer root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        write(progress) {
            const stored = {
                schema_version: 'review_progress_store.v1',
                updated_at: progress.updated_at,
                items: [...(progress.items || [])]
                    .sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)),
            };
            writeJson(paths.reviewProgress, stored);
            return stored;
        },
    };
}

module.exports = {
    createFsReviewProgressWriter,
};
