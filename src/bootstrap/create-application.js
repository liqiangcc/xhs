'use strict';

const { createMergeCanonicalUseCase } = require('../application/canonical/merge-canonical');
const { createSplitCanonicalUseCase } = require('../application/canonical/split-canonical');
const { createListCanonicalsUseCase } = require('../application/canonical/list-canonicals');
const { createCanonicalStatsUseCase } = require('../application/canonical/canonical-stats');
const {
    createCheckCanonicalIntegrityUseCase,
} = require('../application/canonical/check-canonical-integrity');
const {
    createPlanCanonicalizeQuestionGroupUseCase,
} = require('../application/canonical/plan-canonicalize-question-group');
const {
    createPlanCanonicalizeQuestionGroupMutationUseCase,
} = require('../application/canonical/plan-canonicalize-question-group-mutation-use-case');
const {
    createCanonicalizeQuestionGroupUseCase,
} = require('../application/canonical/canonicalize-question-group');
const { createReviewIntegrityUseCase } = require('../application/review/review-integrity');
const { createReviewTodayUseCase } = require('../application/review/review-today');
const { createReviewNextUseCase } = require('../application/review/review-next');
const { createReviewWeakUseCase } = require('../application/review/review-weak');
const { createReviewPrepareUseCase } = require('../application/review/review-prepare');
const {
    createSuggestCanonicalRelationsUseCase,
} = require('../application/dedup/suggest-canonical-relations');
const {
    createRecordRelationDecisionUseCase,
} = require('../application/dedup/record-relation-decision');
const {
    createPrepareRelationApplyUseCase,
} = require('../application/dedup/prepare-relation-apply');
const {
    createApplyRelationDecisionUseCase,
} = require('../application/dedup/apply-relation-decision');
const { loadTaxonomy } = require('../infrastructure/config/taxonomy-provider');
const { createReviewStrategyProvider } = require('../infrastructure/config/review-strategy-provider');
const { createCanonicalFsPaths } = require('../infrastructure/filesystem/canonical-paths');
const { createFsCanonicalRepositories } = require('../infrastructure/filesystem/canonical-repositories');
const {
    createFsCanonicalCatalogRepository,
} = require('../infrastructure/filesystem/canonical-catalog-repository');
const {
    createFsQuestionCatalogRepository,
} = require('../infrastructure/filesystem/question-catalog-repository');
const { createFsReviewRepository } = require('../infrastructure/filesystem/review-repositories');
const { createFsReviewProgressReader } = require('../infrastructure/filesystem/review-progress-reader');
const { createFsReviewProgressWriter } = require('../infrastructure/filesystem/review-progress-writer');
const { createFsReviewSessionReader } = require('../infrastructure/filesystem/review-session-reader');
const { createFsReviewIssueLinkReader } = require('../infrastructure/filesystem/review-issue-link-reader');
const { createFsReviewPlanWriter } = require('../infrastructure/filesystem/review-plan-writer');
const { createFsAnswerRepository } = require('../infrastructure/filesystem/answer-repositories');
const { createFsCanonicalIntegrityChecker } = require('../infrastructure/filesystem/canonical-integrity-checker');
const {
    createFsCanonicalQualityReportWriter,
} = require('../infrastructure/filesystem/canonical-quality-report-writer');
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
    const catalogRepository = createFsCanonicalCatalogRepository({ root: options.root, paths });
    const questionCatalogRepository = createFsQuestionCatalogRepository({ root: options.root, paths });
    const reviewRepository = createFsReviewRepository({ root: options.root, paths });
    const reviewProgressReader = createFsReviewProgressReader({ root: options.root, paths });
    const reviewProgressWriter = createFsReviewProgressWriter({ root: options.root, paths });
    const reviewSessionReader = createFsReviewSessionReader({ root: options.root, paths });
    const reviewIssueLinkReader = createFsReviewIssueLinkReader({ root: options.root });
    const reviewPlanWriter = createFsReviewPlanWriter({ root: options.root });
    const reviewStrategyProvider = createReviewStrategyProvider({
        ...(options.reviewStrategyPath ? { strategyPath: options.reviewStrategyPath } : {}),
    });
    const answerRepository = createFsAnswerRepository({ root: options.root, paths });
    const integrityChecker = createFsCanonicalIntegrityChecker({ root: options.root, paths });
    const qualityReportWriter = createFsCanonicalQualityReportWriter({ root: options.root, paths });
    const mutationStore = createFsCanonicalMutationStore({ root: options.root, paths });

    const list = createListCanonicalsUseCase({ catalogRepository });
    const stats = createCanonicalStatsUseCase({
        canonicalCatalogRepository: catalogRepository,
        questionCatalogRepository,
    });
    const check = createCheckCanonicalIntegrityUseCase({
        integrityChecker,
        reportWriter: qualityReportWriter,
    });
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
    const planQuestionGroup = createPlanCanonicalizeQuestionGroupUseCase({
        canonicalIdentityRepository: canonicalRepository,
    });
    const planQuestionGroupMutation = createPlanCanonicalizeQuestionGroupMutationUseCase({
        canonicalIdentityRepository: canonicalRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
        taxonomy,
    });
    const canonicalizeQuestionGroup = createCanonicalizeQuestionGroupUseCase({
        canonicalIdentityRepository: canonicalRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
        mutationStore,
        taxonomy,
    });
    const reviewQueueDependencies = {
        canonicalCatalogRepository: catalogRepository,
        questionCatalogRepository,
        progressReader: reviewProgressReader,
        progressWriter: reviewProgressWriter,
        strategyProvider: reviewStrategyProvider,
        issueLinkReader: reviewIssueLinkReader,
    };
    const reviewIntegrity = createReviewIntegrityUseCase({
        canonicalCatalogRepository: catalogRepository,
        progressReader: reviewProgressReader,
        sessionReader: reviewSessionReader,
    });
    const reviewToday = createReviewTodayUseCase(reviewQueueDependencies);
    const reviewNext = createReviewNextUseCase(reviewQueueDependencies);
    const reviewWeak = createReviewWeakUseCase(reviewQueueDependencies);
    const reviewPrepare = createReviewPrepareUseCase({
        ...reviewQueueDependencies,
        planWriter: reviewPlanWriter,
    });

    const dedupPaths = createDedupFsPaths(options.root);
    const {
        indexRepository: dedupIndexRepository,
        hotspotRepository: dedupHotspotRepository,
        questionRepository: dedupQuestionRepository,
        relationCandidateStore,
    } = createFsDedupSuggestionRepositories({ root: options.root, paths: dedupPaths });
    const {
        relationCandidateRepository,
        relationDecisionStore,
        relationDecisionRepository,
    } = createFsDedupDecisionRepositories({ root: options.root, paths: dedupPaths });

    const suggest = createSuggestCanonicalRelationsUseCase({
        taxonomy,
        indexRepository: dedupIndexRepository,
        hotspotRepository: dedupHotspotRepository,
        questionRepository: dedupQuestionRepository,
        relationCandidateStore,
    });
    const recordDecision = createRecordRelationDecisionUseCase({
        relationCandidateRepository,
        indexRepository: dedupIndexRepository,
        hotspotRepository: dedupHotspotRepository,
        questionRepository: dedupQuestionRepository,
        relationDecisionStore,
    });
    const prepareApply = createPrepareRelationApplyUseCase({
        relationDecisionRepository,
        indexRepository: dedupIndexRepository,
        hotspotRepository: dedupHotspotRepository,
        questionRepository: dedupQuestionRepository,
    });
    const applyDecision = createApplyRelationDecisionUseCase({
        prepareRelationApply: prepareApply,
        planCanonicalizeQuestionGroup: planQuestionGroup,
        canonicalizeQuestionGroup,
    });

    return Object.freeze({
        canonical: Object.freeze({
            list,
            stats,
            check,
            merge,
            split,
            planQuestionGroup,
            planQuestionGroupMutation,
            canonicalizeQuestionGroup,
        }),
        dedup: Object.freeze({
            suggest,
            recordDecision,
            prepareApply,
            applyDecision,
        }),
        review: Object.freeze({
            integrity: reviewIntegrity,
            today: reviewToday,
            next: reviewNext,
            weak: reviewWeak,
            prepare: reviewPrepare,
        }),
    });
}

module.exports = {
    createApplication,
};
