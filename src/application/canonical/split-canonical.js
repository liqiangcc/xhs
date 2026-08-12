'use strict';

const { splitCanonical } = require('../../domain/canonical/split-policy');
const { refreshCanonicalFromQuestions } = require('../../domain/canonical/refresh-policy');
const { createCanonicalMutationPlan } = require('./mutation-plan');
const { assertCanonicalRepository } = require('../../ports/repositories/canonical-repository');
const { assertQuestionBindingRepository } = require('../../ports/repositories/question-binding-repository');
const { assertCanonicalMutationStore } = require('../../ports/canonical-mutation-store');
const { assertCanonicalIntegrityChecker } = require('../../ports/services/canonical-integrity-checker');

function assertSnapshot(snapshot, label, valueKey) {
    if (!snapshot || typeof snapshot !== 'object') {
        throw new Error(`${label} snapshot is required`);
    }
    if (!snapshot.resource || typeof snapshot.resource !== 'string') {
        throw new Error(`${label} snapshot resource is required`);
    }
    if (!snapshot.revision || typeof snapshot.revision !== 'string') {
        throw new Error(`${label} snapshot revision is required`);
    }
    if (!(valueKey in snapshot)) {
        throw new Error(`${label} snapshot ${valueKey} is required`);
    }
    return snapshot;
}

function assertIntegrityReport(report) {
    if (!report || typeof report !== 'object') {
        throw new Error('canonical integrity report is required');
    }
    if (report.schema_version !== 'canonical_quality_report.v1') {
        throw new Error('canonical integrity report schema_version must be canonical_quality_report.v1');
    }
    if (typeof report.ok !== 'boolean') {
        throw new Error('canonical integrity report ok must be a boolean');
    }
    return report;
}

function expectedRevision(snapshot) {
    return {
        resource: snapshot.resource,
        revision: snapshot.revision,
    };
}

function uniqueSorted(values) {
    return [...new Set(values || [])].sort((a, b) => String(a).localeCompare(String(b)));
}

function assertPostCommitState(
    sourceCanonicalId,
    newCanonicalId,
    questionId,
    remainingSourceExpected,
    postSource,
    postNewCanonical,
    postQuestionBindings,
) {
    if (!postNewCanonical?.record || postNewCanonical.record.canonical_id !== newCanonicalId) {
        throw new Error(`Post-commit validation failed: new canonical ${newCanonicalId} is missing`);
    }
    if (!(postNewCanonical.record.question_ids || []).includes(questionId)) {
        throw new Error(`Post-commit validation failed: new canonical ${newCanonicalId} is missing question ${questionId}`);
    }

    if (remainingSourceExpected) {
        if (!postSource?.record || postSource.record.canonical_id !== sourceCanonicalId) {
            throw new Error(`Post-commit validation failed: source canonical ${sourceCanonicalId} is missing`);
        }
        if ((postSource.record.question_ids || []).includes(questionId)) {
            throw new Error(`Post-commit validation failed: source canonical still contains question ${questionId}`);
        }
    } else if (postSource !== null) {
        throw new Error(`Post-commit validation failed: empty source canonical ${sourceCanonicalId} still exists`);
    }

    const bindings = postQuestionBindings?.bindings || [];
    if (bindings.some((binding) => binding.canonical_id === sourceCanonicalId)) {
        throw new Error(`Post-commit validation failed: source canonical still owns question ${questionId}`);
    }
    if (!bindings.some((binding) => binding.canonical_id === newCanonicalId)) {
        throw new Error(`Post-commit validation failed: new canonical does not own question ${questionId}`);
    }
}

function createSplitCanonicalUseCase(dependencies = {}) {
    const canonicalRepository = assertCanonicalRepository(dependencies.canonicalRepository);
    const questionBindingRepository = assertQuestionBindingRepository(dependencies.questionBindingRepository);
    const mutationStore = assertCanonicalMutationStore(dependencies.mutationStore);
    const integrityChecker = assertCanonicalIntegrityChecker(dependencies.integrityChecker);
    const taxonomy = dependencies.taxonomy;

    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }

    return async function splitCanonicalUseCase(input = {}) {
        const sourceCanonicalId = input.source;
        const questionId = input.question_id;
        const newCanonicalId = input.new_canonical_id;
        const title = input.title;

        if (!sourceCanonicalId || !questionId || !newCanonicalId || !title) {
            throw new Error('source, question_id, new_canonical_id, and title are required');
        }
        if (sourceCanonicalId === newCanonicalId) {
            throw new Error('new-canonical-id must differ from canonical-id');
        }

        const [sourceSnapshot, existingNewCanonical] = await Promise.all([
            canonicalRepository.get(sourceCanonicalId),
            canonicalRepository.get(newCanonicalId),
        ]);
        if (!sourceSnapshot) throw new Error(`Canonical not found: ${sourceCanonicalId}`);
        if (existingNewCanonical) throw new Error(`Canonical already exists: ${newCanonicalId}`);
        assertSnapshot(sourceSnapshot, 'source canonical', 'record');

        const sourceQuestionIds = uniqueSorted(sourceSnapshot.record.question_ids);
        const questionSnapshots = await Promise.all(
            sourceQuestionIds.map((id) => questionBindingRepository.findByQuestionId(id)),
        );
        questionSnapshots.forEach((snapshot, index) => {
            assertSnapshot(snapshot, `question ${sourceQuestionIds[index]} bindings`, 'bindings');
            if (!Array.isArray(snapshot.bindings)) {
                throw new Error(`question ${sourceQuestionIds[index]} snapshot bindings must be an array`);
            }
        });

        const splitQuestionIndex = sourceQuestionIds.indexOf(questionId);
        if (splitQuestionIndex < 0) {
            throw new Error(`Question ${questionId} is not part of ${sourceCanonicalId}`);
        }
        const splitQuestionRows = questionSnapshots[splitQuestionIndex].bindings;
        if (!splitQuestionRows.length) throw new Error(`Question not found: ${questionId}`);

        const split = splitCanonical(sourceSnapshot.record, {
            questionId,
            newCanonicalId,
            title,
            questionFacts: {
                aliases: splitQuestionRows.map((question) => question.original_question),
            },
        });

        const rowsByQuestionId = new Map(
            sourceQuestionIds.map((id, index) => [id, questionSnapshots[index].bindings]),
        );
        const remainingRows = split.remaining_source
            ? split.remaining_source.question_ids.flatMap((id) => rowsByQuestionId.get(id) || [])
            : [];
        const remainingSource = split.remaining_source
            ? refreshCanonicalFromQuestions(split.remaining_source, remainingRows, taxonomy)
            : null;
        const newCanonical = refreshCanonicalFromQuestions(
            split.new_canonical,
            splitQuestionRows,
            taxonomy,
        );

        const plan = createCanonicalMutationPlan({
            operation: 'split',
            expected_revisions: [
                expectedRevision(sourceSnapshot),
                ...questionSnapshots.map(expectedRevision),
            ],
            changes: {
                canonical_upserts: [
                    ...(remainingSource ? [remainingSource] : []),
                    newCanonical,
                ],
                canonical_removals: remainingSource ? [] : [sourceCanonicalId],
                question_rebindings: [{
                    question_id: questionId,
                    from_canonical_id: sourceCanonicalId,
                    to_canonical_id: newCanonicalId,
                }],
                review_migrations: [],
                answer_invalidations: [],
                answer_archives: [],
                rebuild_indexes: true,
                history_entry: null,
            },
        });

        const preflightResult = await mutationStore.preflight(plan);
        const commitResult = await mutationStore.commit(plan, preflightResult);

        const [postSource, postNewCanonical, postQuestionBindings] = await Promise.all([
            canonicalRepository.get(sourceCanonicalId),
            canonicalRepository.get(newCanonicalId),
            questionBindingRepository.findByQuestionId(questionId),
        ]);
        assertPostCommitState(
            sourceCanonicalId,
            newCanonicalId,
            questionId,
            remainingSource,
            postSource,
            postNewCanonical,
            postQuestionBindings,
        );
        const integrity = assertIntegrityReport(await integrityChecker.check());

        return {
            ok: integrity.ok,
            source: sourceCanonicalId,
            new_canonical_id: newCanonicalId,
            question_id: questionId,
            canonical_count: commitResult?.canonical_count ?? null,
            integrity,
            plan,
            commit: commitResult || null,
        };
    };
}

module.exports = {
    createSplitCanonicalUseCase,
};
