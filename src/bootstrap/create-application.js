'use strict';

const { createMergeCanonicalUseCase } = require('../application/canonical/merge-canonical');
const { createCanonicalFsPaths } = require('../infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../infrastructure/filesystem/canonical-repositories');
const { createFsReviewRepository } = require('../infrastructure/filesystem/review-repositories');
const { createFsAnswerRepository } = require('../infrastructure/filesystem/answer-repositories');
const { createFsCanonicalMutationStore } = require('../infrastructure/filesystem/fs-canonical-mutation-store');

/**
 * Production composition root for migrated application slices.
 *
 * Concrete filesystem adapters are constructed only here and injected into the
 * Application layer. Interfaces can depend on this module without learning
 * persistence paths, revision formats, or transaction mechanics.
 */
function createApplication(options = {}) {
    if (!options.root) throw new Error('Application root is required');

    const paths = createCanonicalFsPaths(options.root);
    const {
        canonicalRepository,
        questionBindingRepository,
    } = createFsCanonicalRepositories({ root: options.root, paths });
    const reviewRepository = createFsReviewRepository({ root: options.root, paths });
    const answerRepository = createFsAnswerRepository({ root: options.root, paths });
    const mutationStore = createFsCanonicalMutationStore({ root: options.root, paths });

    const merge = createMergeCanonicalUseCase({
        canonicalRepository,
        questionBindingRepository,
        reviewRepository,
        answerRepository,
        mutationStore,
        ...(options.clock ? { clock: options.clock } : {}),
    });

    return Object.freeze({
        canonical: Object.freeze({
            merge,
        }),
    });
}

module.exports = {
    createApplication,
};
