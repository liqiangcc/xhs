'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { readJson, stableStringify } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function clone(value) {
    return structuredClone(value);
}

function reviewMergeResource(targetCanonicalId, sourceCanonicalId) {
    return `review-merge:${targetCanonicalId}:${sourceCanonicalId}`;
}

function readProgress(paths) {
    return readJson(paths.reviewProgress, {
        schema_version: 'review_progress_store.v1',
        updated_at: null,
        items: [],
    });
}

function readSessions(paths) {
    if (!fs.existsSync(paths.reviewSessionsDir)) return [];
    return fs.readdirSync(paths.reviewSessionsDir)
        .filter((name) => name.endsWith('.json'))
        .sort()
        .map((name) => ({
            name,
            value: readJson(path.join(paths.reviewSessionsDir, name)),
        }));
}

function hashReviewState(paths) {
    return crypto.createHash('sha256')
        .update(stableStringify({
            progress: readProgress(paths),
            sessions: readSessions(paths),
        }), 'utf8')
        .digest('hex');
}

function revisionForReviewResource(paths, resource) {
    if (!resource.startsWith('review-merge:')) {
        throw new Error(`Unsupported filesystem review resource: ${resource}`);
    }
    return hashReviewState(paths);
}

function createFsReviewRepository(options = {}) {
    if (!options.root) throw new Error('Filesystem review repository root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        async loadMergeState(targetCanonicalId, sourceCanonicalId) {
            const progress = readProgress(paths);
            const resource = reviewMergeResource(targetCanonicalId, sourceCanonicalId);
            return {
                target_items: (progress.items || [])
                    .filter((item) => item.canonical_id === targetCanonicalId)
                    .map(clone),
                source_items: (progress.items || [])
                    .filter((item) => item.canonical_id === sourceCanonicalId)
                    .map(clone),
                resource,
                revision: revisionForReviewResource(paths, resource),
            };
        },
    };
}

module.exports = {
    reviewMergeResource,
    revisionForReviewResource,
    createFsReviewRepository,
};
