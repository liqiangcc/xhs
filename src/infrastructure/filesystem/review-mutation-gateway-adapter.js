'use strict';

const path = require('path');
const { stablePrettyStringify } = require('../../../scripts/lib/io');
const {
    SimulatedReviewMutationCrash,
    createReviewFileTransaction,
} = require('./review-file-transaction');

function createFileReviewMutationGatewayAdapter(options = {}) {
    if (!options.root) throw new Error('FileReviewMutationGatewayAdapter root is required');
    const transaction = options.transaction || createReviewFileTransaction(options);

    return {
        snapshot(input = {}) {
            const date = input.date;
            if (!date || typeof date !== 'string') {
                throw new Error('ReviewMutationGateway snapshot date is required');
            }
            transaction.recoverPendingTransaction();
            return {
                progress: transaction.readProgress(date),
                revision: transaction.mutationRevision(date),
            };
        },

        commit(mutation = {}) {
            if (mutation.schema_version !== 'review_mutation.v1') {
                throw new Error('ReviewMutationGateway mutation schema_version must be review_mutation.v1');
            }
            if (!mutation.date || typeof mutation.date !== 'string') {
                throw new Error('ReviewMutationGateway mutation date is required');
            }
            if (!mutation.progress || typeof mutation.progress !== 'object') {
                throw new Error('ReviewMutationGateway mutation progress is required');
            }
            if (!mutation.session_event || typeof mutation.session_event !== 'object') {
                throw new Error('ReviewMutationGateway mutation session_event is required');
            }

            const progress = {
                schema_version: 'review_progress_store.v1',
                updated_at: mutation.progress.updated_at,
                items: [...(mutation.progress.items || [])]
                    .sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)),
            };
            const session = transaction.readSession(mutation.date);
            const nextSession = {
                ...session,
                schema_version: 'review_session.v1',
                date: mutation.date,
                events: [...(session.events || []), structuredClone(mutation.session_event)]
                    .sort((a, b) =>
                        String(a.canonical_id || '').localeCompare(String(b.canonical_id || ''))
                        || String(a.result || '').localeCompare(String(b.result || ''))
                    ),
            };
            const sessionPath = transaction.sessionPath(mutation.date);

            const committed = transaction.commit({
                scope: 'mutation',
                date: mutation.date,
                expected_revision: mutation.expected_revision,
                metadata: {
                    operation: 'mark_review',
                    canonical_id: mutation.session_event.canonical_id,
                    result: mutation.session_event.result,
                },
                operations: [
                    {
                        kind: 'review_progress',
                        target: transaction.paths.progress,
                        content: stablePrettyStringify(progress),
                    },
                    {
                        kind: `review_session:${mutation.date}`,
                        target: sessionPath,
                        content: stablePrettyStringify(nextSession),
                    },
                ],
            });

            return {
                ...committed,
                session_path: path.relative(transaction.paths.root, sessionPath),
            };
        },
    };
}

module.exports = {
    SimulatedReviewMutationCrash,
    createFileReviewMutationGatewayAdapter,
};
