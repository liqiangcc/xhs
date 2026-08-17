'use strict';

const { createMergeCanonicalUseCase } = require('../application/canonical/merge-canonical');
const { createSplitCanonicalUseCase } = require('../application/canonical/split-canonical');
const { createListCanonicalsUseCase } = require('../application/canonical/list-canonicals');
const { createCanonicalStatsUseCase } = require('../application/canonical/canonical-stats');
const {
    createCheckCanonicalIntegrityUseCase,
} = require('../application/canonical/check-canonical-integrity');
const {
    createResolveQuestionGroupCanonicalizationUseCase,
} = require('../application/canonical/resolve-question-group-canonicalization');
const {
    createPlanQuestionGroupCanonicalizationMutationUseCase,
} = require('../application/canonical/plan-question-group-canonicalization-mutation');
const {
    createExecuteQuestionGroupCanonicalizationUseCase,
} = require('../application/canonical/execute-question-group-canonicalization');
const { createReviewIntegrityUseCase } = require('../application/review/review-integrity');
const { createReviewTodayUseCase } = require('../application/review/review-today');
const { createReviewNextUseCase } = require('../application/review/review-next');
const { createReviewWeakUseCase } = require('../application/review/review-weak');
const { createReviewPrepareUseCase } = require('../application/review/review-prepare');
const { createReviewMarkUseCase } = require('../application/review/review-mark');
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
const {
    createFileReviewStrategyReaderAdapter,
} = require('../infrastructure/config/review-strategy-reader-adapter');
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
const {
    createFileReviewProgressRepositoryAdapter,
} = require('../infrastructure/filesystem/review-progress-repository-adapter');
const {
    createFileReviewMutationGatewayAdapter,
} = require('../infrastructure/filesystem/review-mutation-gateway-adapter');
const { createFsReviewSessionReader } = require('../infrastructure/filesystem/review-session-reader');
const { createFsReviewIssueLinkReader } = require('../infrastructure/filesystem/review-issue-link-reader');
const {
    createFileReviewPlanPublisherAdapter,
} = require('../infrastructure/filesystem/review-plan-publisher-adapter');
const { createFsAnswerRepository } = require('../infrastructure/filesystem/answer-repositories');
const { createFsCanonicalIntegrityChecker } = require('../infrastructure/filesystem/canonical-integrity-checker');
const {
    createFsCanonicalQualityReportPublisher,
} = require('../infrastructure/filesystem/canonical-quality-report-publisher');
const {
    createFileCanonicalMutationGatewayAdapter,
} = require('../infrastructure/filesystem/file-canonical-mutation-gateway-adapter');
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
    const reviewProgressRepository = createFileReviewProgressRepositoryAdapter({ root: options.root });
    const reviewMutationGateway = createFileReviewMutationGatewayAdapter({ root: options.root });
    const reviewSessionReader = createFsReviewSessionReader({ root: options.root, paths });
    const reviewIssueLinkReader = createFsReviewIssueLinkReader({ root: options.root });
    const reviewPlanPublisher = createFileReviewPlanPublisherAdapter({ root: options.root });
    const reviewStrategyReader = createFileReviewStrategyReaderAdapter({
        ...(options.reviewStrategyPath ? { strategyPath: options.reviewStrategyPath } : {}),
    });
    const answerRepository = createFsAnswerRepository({ root: options.root, paths });
    const integrityChecker = createFsCanonicalIntegrityChecker({ root: options.root, paths });
    const qualityReportPublisher = createFsCanonicalQualityReportPublisher({ root: options.root, paths });
    const mutationGateway = createFileCanonicalMutationGatewayAdapter({ root: options.root, paths });

    const list = createListCanonicalsUseCase({ catalogRepository });
    const stats = createCanonicalStatsUseCase({
        canonicalCatalogRepository: catalogRepository,
        questionCatalogRepository,
    });
    const check = createCheckCanonicalIntegrityUseCase({
        integrityChecker,
        reportPublisher: qualityReportPublisher,
    });
    const merge = createMergeCanonicalUseCase({
        canonicalRepository,
        questionBindingRepository,
        reviewRepository,
        answerRepository,
        integrityChecker,
        mutationGateway,
        taxonomy,
        ...(options.clock ? { clock: options.clock } : {}),
    });
    const split = createSplitCanonicalUseCase({
        canonicalRepository,
        canonicalIdentityRepository: canonicalRepository,
        questionBindingRepository,
        integrityChecker,
        mutationGateway,
        taxonomy,
    });
    const resolveQuestionGroupCanonicalization = createResolveQuestionGroupCanonicalizationUseCase({
        canonicalIdentityRepository: canonicalRepository,
    });
    const planQuestionGroupCanonicalizationMutation =
        createPlanQuestionGroupCanonicalizationMutationUseCase({
            canonicalIdentityRepository: canonicalRepository,
            questionBindingRepository,
            canonicalQuestionOwnershipRepository,
            taxonomy,
        });
    const executeQuestionGroupCanonicalization = createExecuteQuestionGroupCanonicalizationUseCase({
        canonicalIdentityRepository: canonicalRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
        mutationGateway,
        taxonomy,
    });
    const reviewQueueDependencies = {
        canonicalCatalogRepository: catalogRepository,
        questionCatalogRepository,
        progressRepository: reviewProgressRepository,
        strategyReader: reviewStrategyReader,
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
        planPublisher: reviewPlanPublisher,
    });
    const reviewMark = createReviewMarkUseCase({
        canonicalCatalogRepository: catalogRepository,
        mutationGateway: reviewMutationGateway,
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
        resolveQuestionGroupCanonicalization,
        executeQuestionGroupCanonicalization,
    });

    return Object.freeze({
        canonical: Object.freeze({
            list,
            stats,
            check,
            merge,
            split,
            resolveQuestionGroupCanonicalization,
            planQuestionGroupCanonicalizationMutation,
            executeQuestionGroupCanonicalization,
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
            mark: reviewMark,
        }),
    });
}

module.exports = {
    createApplication,
};
