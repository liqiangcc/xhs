'use strict';

function clone(value) {
    return structuredClone(value);
}

function canonicalResource(canonicalId) {
    return `canonical:${canonicalId}`;
}

function bindingResource(canonicalId) {
    return `question-bindings:${canonicalId}`;
}

function questionResource(questionId) {
    return `question-bindings-by-question:${questionId}`;
}

function reviewResource(targetCanonicalId, sourceCanonicalId) {
    return `review-merge:${targetCanonicalId}:${sourceCanonicalId}`;
}

function answerResource(targetCanonicalId, sourceCanonicalId) {
    return `answer-merge:${targetCanonicalId}:${sourceCanonicalId}`;
}

function createInMemoryCanonicalAdapters(seed = {}) {
    let canonicalRecords = new Map(
        (seed.canonicals || []).map((record) => [record.canonical_id, clone(record)]),
    );
    let questionBindings = (seed.bindings || []).map(clone);
    let reviewProgress = (seed.review_progress || []).map(clone);
    let reviewSessionEvents = (seed.review_session_events || []).map(clone);
    let answers = new Map(
        (seed.answers || []).map((answer) => [answer.canonical_id, clone(answer)]),
    );
    let answerArchives = new Map(
        (seed.answer_archives || []).map((answer) => [answer.canonical_id, clone(answer)]),
    );
    let revisionSequence = 0;
    const revisions = new Map();
    const preflightPlans = new WeakMap();
    let preflightSequence = 0;
    let nextCommitFailure = null;
    const effects = {
        review_migrations: [],
        answer_invalidations: [],
        answer_archives: [],
        history: [],
        index_rebuild_count: 0,
    };

    function revision(resource) {
        if (!revisions.has(resource)) revisions.set(resource, 'rev-0');
        return revisions.get(resource);
    }

    function bump(resource) {
        revisionSequence += 1;
        revisions.set(resource, `rev-${revisionSequence}`);
    }

    function assertExpectedRevisions(plan) {
        for (const expected of plan.expected_revisions || []) {
            const actual = revision(expected.resource);
            if (actual !== expected.revision) {
                throw new Error(`Revision mismatch for ${expected.resource}: expected ${expected.revision}, got ${actual}`);
            }
        }
    }

    const canonicalRepository = {
        async get(canonicalId) {
            const record = canonicalRecords.get(canonicalId);
            if (!record) return null;
            const resource = canonicalResource(canonicalId);
            return {
                record: clone(record),
                resource,
                revision: revision(resource),
            };
        },

        async inspect(canonicalId) {
            const record = canonicalRecords.get(canonicalId) || null;
            const resource = canonicalResource(canonicalId);
            return {
                record: record ? clone(record) : null,
                resource,
                revision: revision(resource),
            };
        },
    };

    const questionBindingRepository = {
        async findByCanonical(canonicalId) {
            const resource = bindingResource(canonicalId);
            return {
                bindings: questionBindings
                    .filter((binding) => binding.canonical_id === canonicalId)
                    .map(clone),
                resource,
                revision: revision(resource),
            };
        },

        async findByQuestionId(questionId) {
            const resource = questionResource(questionId);
            return {
                bindings: questionBindings
                    .filter((binding) => binding.question_id === questionId)
                    .map(clone),
                resource,
                revision: revision(resource),
            };
        },
    };

    const reviewRepository = {
        async loadMergeState(targetCanonicalId, sourceCanonicalId) {
            const resource = reviewResource(targetCanonicalId, sourceCanonicalId);
            return {
                target_items: reviewProgress
                    .filter((item) => item.canonical_id === targetCanonicalId)
                    .map(clone),
                source_items: reviewProgress
                    .filter((item) => item.canonical_id === sourceCanonicalId)
                    .map(clone),
                source_session_event_count: reviewSessionEvents
                    .filter((event) => event.canonical_id === sourceCanonicalId).length,
                resource,
                revision: revision(resource),
            };
        },
    };

    const answerRepository = {
        async loadMergeState(targetCanonicalId, sourceCanonicalId) {
            const resource = answerResource(targetCanonicalId, sourceCanonicalId);
            return {
                target_answer: answers.has(targetCanonicalId)
                    ? clone(answers.get(targetCanonicalId))
                    : null,
                source_answer: answers.has(sourceCanonicalId)
                    ? clone(answers.get(sourceCanonicalId))
                    : null,
                source_archive_exists: answerArchives.has(sourceCanonicalId),
                resource,
                revision: revision(resource),
            };
        },
    };

    function applyReviewMigrations(progressRows, sessionEvents, migrations) {
        let nextProgress = progressRows.map(clone);
        let nextSessions = sessionEvents.map(clone);

        for (const migration of migrations || []) {
            const progress = migration.progress || {};
            if (progress.source_found) {
                const removeIds = new Set(progress.remove_canonical_ids || []);
                nextProgress = nextProgress.filter((item) => !removeIds.has(item.canonical_id));
                if (progress.upsert) nextProgress.push(clone(progress.upsert));
            }

            const session = migration.session_events || {};
            if (session.rebind_from_canonical_id && session.rebind_to_canonical_id) {
                nextSessions = nextSessions.map((event) => {
                    if (event.canonical_id !== session.rebind_from_canonical_id) return event;
                    return {
                        ...event,
                        canonical_id: session.rebind_to_canonical_id,
                        ...(session.annotate_migrated_from
                            ? { migrated_from_canonical_id: session.rebind_from_canonical_id }
                            : {}),
                    };
                });
            }
        }

        return {
            progress: nextProgress,
            sessions: nextSessions,
        };
    }

    function applyAnswerMutations(activeAnswers, archivedAnswers, invalidations, archives) {
        const nextAnswers = new Map(
            [...activeAnswers.entries()].map(([canonicalId, answer]) => [canonicalId, clone(answer)]),
        );
        const nextArchives = new Map(
            [...archivedAnswers.entries()].map(([canonicalId, answer]) => [canonicalId, clone(answer)]),
        );

        for (const invalidation of invalidations || []) {
            const answer = nextAnswers.get(invalidation.canonical_id);
            if (!answer) {
                throw new Error(`Target answer not found for ${invalidation.canonical_id}`);
            }
            if (!invalidation.next_metadata) {
                throw new Error(`Answer invalidation next_metadata is required for ${invalidation.canonical_id}`);
            }
            nextAnswers.set(invalidation.canonical_id, {
                ...answer,
                metadata: clone(invalidation.next_metadata),
            });
        }

        for (const archive of archives || []) {
            const source = nextAnswers.get(archive.canonical_id);
            if (!source) {
                throw new Error(`Source answer not found for archive ${archive.canonical_id}`);
            }
            if (nextArchives.has(archive.canonical_id)) {
                throw new Error(`Source answer archive already exists for ${archive.canonical_id}`);
            }
            nextAnswers.delete(archive.canonical_id);
            nextArchives.set(archive.canonical_id, clone(source));
        }

        return {
            active: nextAnswers,
            archived: nextArchives,
        };
    }

    const mutationStore = {
        async preflight(plan) {
            assertExpectedRevisions(plan);
            const token = Object.freeze({ id: `preflight-${++preflightSequence}` });
            preflightPlans.set(token, plan);
            return token;
        },

        async commit(plan, preflightResult) {
            if (!preflightResult || preflightPlans.get(preflightResult) !== plan) {
                throw new Error('Invalid or stale canonical mutation preflight token');
            }
            assertExpectedRevisions(plan);

            if (nextCommitFailure) {
                const error = nextCommitFailure;
                nextCommitFailure = null;
                throw error;
            }

            const nextCanonicals = new Map(
                [...canonicalRecords.entries()].map(([id, record]) => [id, clone(record)]),
            );
            const nextBindings = questionBindings.map(clone);

            for (const canonicalId of plan.changes.canonical_removals || []) {
                nextCanonicals.delete(canonicalId);
            }
            for (const record of plan.changes.canonical_upserts || []) {
                nextCanonicals.set(record.canonical_id, clone(record));
            }
            for (const rebinding of plan.changes.question_rebindings || []) {
                let matched = false;
                for (let index = 0; index < nextBindings.length; index += 1) {
                    const binding = nextBindings[index];
                    if (
                        binding.question_id === rebinding.question_id
                        && binding.canonical_id === rebinding.from_canonical_id
                    ) {
                        nextBindings[index] = {
                            ...binding,
                            canonical_id: rebinding.to_canonical_id,
                        };
                        matched = true;
                    }
                }
                if (!matched) {
                    throw new Error(
                        `Question binding not found for ${rebinding.question_id} in ${rebinding.from_canonical_id}`,
                    );
                }
            }

            const nextReview = applyReviewMigrations(
                reviewProgress,
                reviewSessionEvents,
                plan.changes.review_migrations || [],
            );
            const nextAnswerState = applyAnswerMutations(
                answers,
                answerArchives,
                plan.changes.answer_invalidations || [],
                plan.changes.answer_archives || [],
            );

            canonicalRecords = nextCanonicals;
            questionBindings = nextBindings;
            reviewProgress = nextReview.progress;
            reviewSessionEvents = nextReview.sessions;
            answers = nextAnswerState.active;
            answerArchives = nextAnswerState.archived;

            for (const record of plan.changes.canonical_upserts || []) {
                bump(canonicalResource(record.canonical_id));
            }
            for (const canonicalId of plan.changes.canonical_removals || []) {
                bump(canonicalResource(canonicalId));
            }
            for (const rebinding of plan.changes.question_rebindings || []) {
                bump(bindingResource(rebinding.from_canonical_id));
                bump(bindingResource(rebinding.to_canonical_id));
                bump(questionResource(rebinding.question_id));
            }
            for (const migration of plan.changes.review_migrations || []) {
                bump(reviewResource(migration.to_canonical_id, migration.from_canonical_id));
            }
            const answerResources = new Set();
            for (const invalidation of plan.changes.answer_invalidations || []) {
                answerResources.add(answerResource(
                    invalidation.canonical_id,
                    invalidation.source_canonical_id,
                ));
            }
            for (const archive of plan.changes.answer_archives || []) {
                answerResources.add(answerResource(
                    archive.target_canonical_id,
                    archive.canonical_id,
                ));
            }
            for (const resource of answerResources) bump(resource);

            effects.review_migrations.push(...clone(plan.changes.review_migrations || []));
            effects.answer_invalidations.push(...clone(plan.changes.answer_invalidations || []));
            effects.answer_archives.push(...clone(plan.changes.answer_archives || []));
            if (plan.changes.history_entry) effects.history.push(clone(plan.changes.history_entry));
            if (plan.changes.rebuild_indexes) effects.index_rebuild_count += 1;

            preflightPlans.delete(preflightResult);
            return {
                committed: true,
                operation: plan.operation,
                canonical_count: nextCanonicals.size,
                canonical_upsert_count: (plan.changes.canonical_upserts || []).length,
                canonical_removal_count: (plan.changes.canonical_removals || []).length,
                question_rebinding_count: (plan.changes.question_rebindings || []).length,
                review_migration_count: (plan.changes.review_migrations || []).length,
                answer_invalidation_count: (plan.changes.answer_invalidations || []).length,
                answer_archive_count: (plan.changes.answer_archives || []).length,
            };
        },

        failNextCommit(error = new Error('Injected in-memory commit failure')) {
            nextCommitFailure = error;
        },

        bumpRevision(resource) {
            bump(resource);
        },
    };

    const testSupport = Object.freeze({
        upsertCanonical(record) {
            if (!record || !record.canonical_id) throw new Error('canonical record is required');
            canonicalRecords.set(record.canonical_id, clone(record));
            bump(canonicalResource(record.canonical_id));
        },
    });

    function snapshot() {
        return {
            canonicals: [...canonicalRecords.values()].map(clone),
            bindings: questionBindings.map(clone),
            review_progress: reviewProgress.map(clone),
            review_session_events: reviewSessionEvents.map(clone),
            answers: [...answers.values()].map(clone),
            answer_archives: [...answerArchives.values()].map(clone),
            effects: clone(effects),
        };
    }

    return {
        canonicalRepository,
        canonicalIdentityRepository: canonicalRepository,
        questionBindingRepository,
        reviewRepository,
        answerRepository,
        mutationStore,
        testSupport,
        snapshot,
    };
}

module.exports = {
    createInMemoryCanonicalAdapters,
};
