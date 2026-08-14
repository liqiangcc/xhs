'use strict';

const path = require('path');
const { readJson } = require('../../../scripts/lib/io');

function createFsReviewIssueLinkReader(options = {}) {
    if (!options.root) throw new Error('Filesystem review issue link reader root is required');
    const filePath = options.filePath || path.join(options.root, 'review', 'issue_links.json');

    return {
        load() {
            const store = readJson(filePath, {
                schema_version: 'review_issue_links.v1',
                updated_at: null,
                items: [],
            });
            return {
                schema_version: 'review_issue_links.v1',
                updated_at: store.updated_at ?? null,
                items: Array.isArray(store.items) ? structuredClone(store.items) : [],
            };
        },
    };
}

module.exports = {
    createFsReviewIssueLinkReader,
};
