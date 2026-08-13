'use strict';

const { createAcceptCanonicalUseCase } = require('../application/canonical/accept-canonical');
const { createMergeCanonicalUseCase } = require('../application/canonical/merge-canonical');
const { createSplitCanonicalUseCase } = require('../application/canonical/split-canonical');
const {
    createSuggestCanonicalRelationsUseCase,
} = require('../application/dedup/suggest-canonical-relations');
const {
    createRecordRelationDecisionUseCase,
} = require('../application/dedup/record-relation-decision');
const { loadTaxonomy } = require('../infrastructure/config/taxonomy-provider');
const { createCanonicalFsPaths } = require('../infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../infrastructure/filesystem/canonical-repositories');
const { createFsCanonicalCandidateRepository } = require('../infrastructure/filesystem/canonical-candidate-repositories');
const { createFsReviewRepository } = require('../infrastructure/filesystem/review-repositories');
const { createFsAnswerRepository } = require('../infrastructure/filesystem/answer-repositories');
const { createFsCanonicalIntegrityChecker } = require('../infrastructure/filesystem/canonical-integrity-checker');
const { createFsCanonicalMutationStore } = require('../infrastructure/filesystem/fs-canonical-mutation-store');
const { createDedupFsPaths } = require('../infrastructure/filesystem/dedup-paths');
const {
    createFsDedupSuggestionRepositories,
} = require('../infrastructure/filesystem/dedup-suggestion-repositories');
const {
    createFsDedupDecisionRepositories,
} = require('../infrastructure/filesystem/dedup-decision-repositories');

/**
 * Production composition root for migrated application slices.
 *
 * Concrete filesystem/config adapters are constructed only here and injected
 * into the Application layer. Interfaces can depend on this module without
 * learning persistence paths, revision formats, or transaction mechanics.
 */
function createApplication(options = {}) {
    if (!options.root) throw new Error('Application root is required');

    const paths = createCanonicalFsPaths(options.root);
    const taxonomy = options.taxonomy || loadTaxonomy({ taxonomyPath: options.taxonomyPath });
    const {
        canonicalRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
    } = createFsCanonicalRepositories({ root: options.root, paths });
    const candidateRepository = createFsCanonicalCandidateRepository({ root: options.root, paths });
    const reviewRepository = createFsReviewRepository({ root: options.root, paths });
    const answerRepository = createFsAnswerRepository({ root: options.root, paths });
    const integrityChecker = createFsCanonicalIntegrityChecker({ root: options.root, paths });
    const mutationStore = createFsCanonicalMutationStore({ root: options.root, paths });

    const merge = createMergeCanonicalUseCase({
        canonicalRepository,
        questionBindingRepository,
        reviewRepository,
        answerRepository,
        integrityChecker,
        mutationStore,
        taxonomy,
        ...(options.clock ? { clock: options.clock } : {}),
    });
    const split = createSplitCanonicalUseCase({
        canonicalRepository,
        canonicalIdentityRepository: canonicalRepository,
        questionBindingRepository,
        integrityChecker,
        mutationStore,
        taxonomy,
    });
    const accept = createAcceptCanonicalUseCase({
        candidateRepository,
        canonicalIdentityRepository: canonicalRepository,
        canonicalQuestionOwnershipRepository,
        questionBindingRepository,
        mutationStore,
        taxonomy,
    });

    const dedupPaths = createDedupFsPaths(options.root);
    const {
        indexRepository: dedupIndexRepository,
        questionRepository: dedupQuestionRepository,
        relationCandidateStore,
    } = createFsDedupSuggestionRepositories({ root: options.root, paths: dedupPaths });
    const {
        relationCandidateRepository,
        relationDecisionStore,
    } = createFsDedupDecisionRepositories({ root: options.root, paths: dedupPaths });

    const suggest = createSuggestCanonicalRelationsUseCase({
        taxonomy,
        indexRepository: dedupIndexRepository,
        questionRepository: dedupQuestionRepository,
        relationCandidateStore,
    });
    const recordDecision = createRecordRelationDecisionUseCase({
        relationCandidateRepository,
        indexRepository: dedupIndexRepository,
        questionRepository: dedupQuestionRepository,
        relationDecisionStore,
    });

    return Object.freeze({
        canonical: Object.freeze({
            merge,
            split,
            accept,
        }),
        dedup: Object.freeze({
            suggest,
            recordDecision,
        }),
    });
}

module.exports = {
    createApplication,
};
