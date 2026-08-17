'use strict';

const { stablePrettyStringify } = require('../../../scripts/lib/io');
const { createReviewFileTransaction } = require('./review-file-transaction');

function createFileReviewProgressRepositoryAdapter(options = {}) {
    if (!options.root) throw new Error('FileReviewProgressRepositoryAdapter root is required');
    const transaction = options.transaction || createReviewFileTransaction(options);

    return {
        snapshot(input = {}) {
            const date = input.date;
            if (!date || typeof date !== 'string') {
                throw new Error('ReviewProgressRepository snapshot date is required');
            }
            transaction.recoverPendingTransaction();
            return {
                progress: transaction.readProgress(date),
                revision: transaction.progressRevision(),
            };
        },

        save(progress, input = {}) {
            const expectedRevision = input.expected_revision;
            const date = input.date || progress?.updated_at;
            if (!progress || typeof progress !== 'object') {
                throw new Error('ReviewProgressRepository progress is required');
            }
            const stored = {
                schema_version: 'review_progress_store.v1',
                updated_at: progress.updated_at,
                items: [...(progress.items || [])]
                    .sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)),
            };
            transaction.commit({
                scope: 'progress',
                date,
                expected_revision: expectedRevision,
                metadata: { operation: 'save_review_progress' },
                operations: [{
                    kind: 'review_progress',
                    target: transaction.paths.progress,
                    content: stablePrettyStringify(stored),
                }],
            });
            return stored;
        },
    };
}

module.exports = {
    createFileReviewProgressRepositoryAdapter,
};
