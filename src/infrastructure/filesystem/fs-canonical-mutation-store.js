'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const {
    ensureDir,
    readJson,
    readJsonl,
    stablePrettyStringify,
    stableStringify,
} = require('../../../scripts/lib/io');
const { replaceAnswerMetadata } = require('../../../scripts/lib/answer_store');
const { buildIndexes, getIndexPaths } = require('../../../scripts/lib/index_store');
const { createCanonicalFsPaths } = require('./canonical-paths');
const { revisionForResource } = require('./canonical-repositories');
const { revisionForReviewResource } = require('./review-repositories');
const {
    activeAnswerPath,
    archivedAnswerPath,
    revisionForAnswerResource,
} = require('./answer-repositories');

let transactionSequence = 0;

class SimulatedCanonicalMutationCrash extends Error {
    constructor(message = 'Simulated canonical mutation crash') {
        super(message);
        this.name = 'SimulatedCanonicalMutationCrash';
        this.simulatedCrash = true;
    }
}

function clone(value) {
    return structuredClone(value);
}

function hashValue(value) {
    return crypto.createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function serializeJsonl(records) {
    const body = records.map(stableStringify).join('\n');
    return body ? `${body}\n` : '';
}

function sortCanonicalRecords(records) {
    return [...records].sort((a, b) => a.canonical_id.localeCompare(b.canonical_id));
}

function sortQuestionRows(rows) {
    return [...rows].sort((a, b) =>
        String(a.source_note_id || '').localeCompare(String(b.source_note_id || ''), 'zh')
        || Number(a.source_question_index ?? 0) - Number(b.source_question_index ?? 0)
        || String(a.question_id || '').localeCompare(String(b.question_id || ''))
    );
}

function removeIfExists(filePath) {
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
}

function writeFileAtomic(filePath, content) {
    ensureDir(path.dirname(filePath));
    const tempPath = `${filePath}.tmp-${process.pid}-${Date.now()}-${++transactionSequence}`;
    fs.writeFileSync(tempPath, content, 'utf8');
    fs.renameSync(tempPath, filePath);
}

function processIsAlive(pid) {
    if (!Number.isInteger(pid) || pid <= 0) return false;
    try {
        process.kill(pid, 0);
        return true;
    } catch (error) {
        return error.code === 'EPERM';
    }
}

function assertReviewConcurrencyCoverage(plan) {
    if (!(plan.changes?.review_migrations || []).length) return;
    const covered = (plan.expected_revisions || [])
        .some((item) => String(item.resource || '').startsWith('review-merge:'));
    if (!covered) {
        throw new Error('Filesystem review migration requires an opaque review-merge revision');
    }
}

function assertAnswerConcurrencyCoverage(plan) {
    const changes = plan.changes || {};
    if (!(changes.answer_invalidations || []).length && !(changes.answer_archives || []).length) return;
    const covered = (plan.expected_revisions || [])
        .some((item) => String(item.resource || '').startsWith('answer-merge:'));
    if (!covered) {
        throw new Error('Filesystem answer mutation requires an opaque answer-merge revision');
    }
}

function revisionForMutationResource(paths, resource) {
    if (String(resource).startsWith('review-merge:')) {
        return revisionForReviewResource(paths, resource);
    }
    if (String(resource).startsWith('answer-merge:')) {
        return revisionForAnswerResource(paths, resource);
    }
    return revisionForResource(paths, resource);
}

function assertExpectedRevisions(paths, plan) {
    for (const expected of plan.expected_revisions || []) {
        const actual = revisionForMutationResource(paths, expected.resource);
        if (actual !== expected.revision) {
            throw new Error(
                `Revision mismatch for ${expected.resource}: expected ${expected.revision}, got ${actual}`,
            );
        }
    }
}

function applyCanonicalChanges(records, plan) {
    const byId = new Map(records.map((record) => [record.canonical_id, clone(record)]));
    for (const canonicalId of plan.changes.canonical_removals || []) byId.delete(canonicalId);
    for (const record of plan.changes.canonical_upserts || []) {
        byId.set(record.canonical_id, clone(record));
    }
    return sortCanonicalRecords([...byId.values()]);
}

function applyQuestionRebindings(rows, plan) {
    const nextRows = rows.map(clone);
    for (const rebinding of plan.changes.question_rebindings || []) {
        let matched = false;
        for (let index = 0; index < nextRows.length; index += 1) {
            const row = nextRows[index];
            if (
                row.question_id === rebinding.question_id
                && row.canonical_id === rebinding.from_canonical_id
            ) {
                nextRows[index] = {
                    ...row,
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
    return sortQuestionRows(nextRows);
}

function readReviewSessions(paths) {
    if (!fs.existsSync(paths.reviewSessionsDir)) return new Map();
    return new Map(
        fs.readdirSync(paths.reviewSessionsDir)
            .filter((name) => name.endsWith('.json'))
            .sort()
            .map((name) => [name, readJson(path.join(paths.reviewSessionsDir, name))]),
    );
}

function materializeReviewOperations(paths, plan) {
    const migrations = plan.changes.review_migrations || [];
    if (!migrations.length) return [];
    assertReviewConcurrencyCoverage(plan);

    let progress = readJson(paths.reviewProgress, {
        schema_version: 'review_progress_store.v1',
        updated_at: null,
        items: [],
    });
    const sessions = readReviewSessions(paths);
    let progressChanged = false;
    const changedSessionNames = new Set();

    for (const migration of migrations) {
        const progressIntent = migration.progress || {};
        if (progressIntent.source_found) {
            const removed = new Set(progressIntent.remove_canonical_ids || []);
            const items = (progress.items || [])
                .filter((item) => !removed.has(item.canonical_id));
            if (progressIntent.upsert) items.push(clone(progressIntent.upsert));
            items.sort((a, b) => String(a.canonical_id || '').localeCompare(String(b.canonical_id || '')));
            progress = {
                ...progress,
                updated_at: progressIntent.store_updated_at || progress.updated_at || null,
                items,
            };
            progressChanged = true;
        }

        const sessionIntent = migration.session_events || {};
        const fromCanonicalId = sessionIntent.rebind_from_canonical_id;
        const toCanonicalId = sessionIntent.rebind_to_canonical_id;
        if (!fromCanonicalId || !toCanonicalId) continue;

        for (const [name, session] of sessions.entries()) {
            let changed = false;
            const events = (session.events || []).map((event) => {
                if (event.canonical_id !== fromCanonicalId) return event;
                changed = true;
                return {
                    ...event,
                    canonical_id: toCanonicalId,
                    ...(sessionIntent.annotate_migrated_from
                        ? { migrated_from_canonical_id: fromCanonicalId }
                        : {}),
                };
            });
            if (changed) {
                sessions.set(name, { ...session, events });
                changedSessionNames.add(name);
            }
        }
    }

    const operations = [];
    if (progressChanged) {
        operations.push({
            kind: 'review_progress',
            action: 'write',
            target: paths.reviewProgress,
            content: stablePrettyStringify(progress),
        });
    }
    for (const name of [...changedSessionNames].sort()) {
        operations.push({
            kind: `review_session:${name}`,
            action: 'write',
            target: path.join(paths.reviewSessionsDir, name),
            content: stablePrettyStringify(sessions.get(name)),
        });
    }
    return operations;
}

function materializeAnswerOperations(paths, plan) {
    const invalidations = plan.changes.answer_invalidations || [];
    const archives = plan.changes.answer_archives || [];
    if (!invalidations.length && !archives.length) return [];
    assertAnswerConcurrencyCoverage(plan);

    const operations = [];
    for (const invalidation of invalidations) {
        if (!invalidation.canonical_id || !invalidation.next_metadata) {
            throw new Error('Filesystem answer invalidation requires canonical_id and next_metadata');
        }
        const target = activeAnswerPath(paths, invalidation.canonical_id);
        if (!fs.existsSync(target)) {
            throw new Error(`Target answer not found for ${invalidation.canonical_id}`);
        }
        const current = fs.readFileSync(target, 'utf8');
        operations.push({
            kind: `answer_invalidation:${invalidation.canonical_id}`,
            action: 'write',
            target,
            content: replaceAnswerMetadata(current, invalidation.next_metadata),
        });
    }

    for (const archive of archives) {
        if (!archive.canonical_id || !archive.target_canonical_id) {
            throw new Error('Filesystem answer archive requires canonical_id and target_canonical_id');
        }
        const source = activeAnswerPath(paths, archive.canonical_id);
        const target = archivedAnswerPath(paths, archive.canonical_id);
        if (!fs.existsSync(source)) {
            throw new Error(`Source answer not found for archive ${archive.canonical_id}`);
        }
        if (fs.existsSync(target)) {
            throw new Error(`Source answer archive already exists for ${archive.canonical_id}`);
        }
        const content = fs.readFileSync(source, 'utf8');
        operations.push({
            kind: `answer_archive_write:${archive.canonical_id}`,
            action: 'write',
            target,
            content,
        });
        operations.push({
            kind: `answer_archive_delete_source:${archive.canonical_id}`,
            action: 'delete',
            target: source,
        });
    }

    return operations;
}

function buildHistory(paths, historyEntry) {
    if (!historyEntry) return null;
    const current = readJson(paths.mergeHistory, {
        schema_version: 'canonical_merge_history.v1',
        items: [],
    });
    const items = [...(current.items || []), clone(historyEntry)]
        .sort((a, b) =>
            String(a.source || '').localeCompare(String(b.source || ''))
            || String(a.target || '').localeCompare(String(b.target || ''))
            || String(a.merged_at || '').localeCompare(String(b.merged_at || ''))
        );
    return {
        schema_version: 'canonical_merge_history.v1',
        items,
    };
}

function materializeOperations(paths, plan) {
    assertReviewConcurrencyCoverage(plan);
    assertAnswerConcurrencyCoverage(plan);
    const canonicalRecords = readJsonl(paths.canonicalQuestions, []);
    const questionRows = readJsonl(paths.questions, []);
    const nextCanonicals = applyCanonicalChanges(canonicalRecords, plan);
    const nextQuestions = applyQuestionRebindings(questionRows, plan);

    const operations = [
        {
            kind: 'canonical_questions',
            action: 'write',
            target: paths.canonicalQuestions,
            content: serializeJsonl(nextCanonicals),
        },
        {
            kind: 'questions',
            action: 'write',
            target: paths.questions,
            content: serializeJsonl(nextQuestions),
        },
        ...materializeReviewOperations(paths, plan),
        ...materializeAnswerOperations(paths, plan),
    ];

    if (plan.changes.rebuild_indexes) {
        const indexes = buildIndexes(nextQuestions, { canonicalQuestions: nextCanonicals });
        const indexPaths = getIndexPaths(paths.indexDir);
        for (const key of ['entity', 'company', 'domain', 'hotspot']) {
            operations.push({
                kind: `index:${key}`,
                action: 'write',
                target: indexPaths[key],
                content: stablePrettyStringify(indexes[key]),
            });
        }
    }

    const history = buildHistory(paths, plan.changes.history_entry);
    if (history) {
        operations.push({
            kind: 'merge_history',
            action: 'write',
            target: paths.mergeHistory,
            content: stablePrettyStringify(history),
        });
    }

    return operations;
}

function createFsCanonicalMutationStore(options = {}) {
    if (!options.root) throw new Error('FsCanonicalMutationStore root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);
    const faultInjector = typeof options.faultInjector === 'function'
        ? options.faultInjector
        : null;
    const preflightPlans = new WeakMap();
    let preflightSequence = 0;

    function invokeFault(stage, context = {}) {
        if (faultInjector) faultInjector(stage, { ...context, paths });
    }

    function acquireLock() {
        ensureDir(paths.transactionDir);
        for (let attempt = 0; attempt < 2; attempt += 1) {
            try {
                const fd = fs.openSync(paths.lock, 'wx');
                fs.writeFileSync(fd, JSON.stringify({
                    pid: process.pid,
                    created_at: new Date().toISOString(),
                }));
                fs.closeSync(fd);
                return;
            } catch (error) {
                if (error.code !== 'EEXIST') throw error;
                let owner = null;
                try {
                    owner = JSON.parse(fs.readFileSync(paths.lock, 'utf8'));
                } catch {
                    owner = null;
                }
                if (owner?.pid && processIsAlive(Number(owner.pid))) {
                    throw new Error(`Canonical mutation lock is already held by pid ${owner.pid}`);
                }
                removeIfExists(paths.lock);
            }
        }
        throw new Error('Unable to acquire canonical mutation lock');
    }

    function releaseLock() {
        removeIfExists(paths.lock);
    }

    function cleanupJournalArtifacts(journal) {
        if (journal?.transaction_dir && fs.existsSync(journal.transaction_dir)) {
            fs.rmSync(journal.transaction_dir, { recursive: true, force: true });
        }
        removeIfExists(paths.journal);
    }

    function recoverPendingTransactionUnlocked() {
        if (!fs.existsSync(paths.journal)) return { recovered: false };
        const journal = readJson(paths.journal);
        if (journal.status === 'committed') {
            cleanupJournalArtifacts(journal);
            return { recovered: true, outcome: 'committed' };
        }

        for (const operation of [...(journal.operations || [])].reverse()) {
            ensureDir(path.dirname(operation.target));
            if (operation.existed_before) {
                if (!fs.existsSync(operation.backup)) {
                    throw new Error(`Cannot recover canonical mutation; backup missing: ${operation.backup}`);
                }
                fs.copyFileSync(operation.backup, operation.target);
            } else {
                removeIfExists(operation.target);
            }
        }
        cleanupJournalArtifacts(journal);
        return { recovered: true, outcome: 'rolled_back' };
    }

    function recoverPendingTransaction() {
        if (!fs.existsSync(paths.journal)) return { recovered: false };
        acquireLock();
        try {
            return recoverPendingTransactionUnlocked();
        } finally {
            releaseLock();
        }
    }

    function prepareTransaction(plan, operations) {
        ensureDir(paths.transactionDir);
        const transactionId = `tx-${Date.now()}-${process.pid}-${++transactionSequence}`;
        const transactionDir = path.join(paths.transactionDir, transactionId);
        const stageDir = path.join(transactionDir, 'stage');
        const backupDir = path.join(transactionDir, 'backup');
        ensureDir(stageDir);
        ensureDir(backupDir);

        const journalOperations = [];
        try {
            operations.forEach((operation, index) => {
                const action = operation.action || 'write';
                const stage = action === 'delete'
                    ? null
                    : path.join(stageDir, `${String(index).padStart(3, '0')}.next`);
                const backup = path.join(backupDir, `${String(index).padStart(3, '0')}.previous`);
                const existedBefore = fs.existsSync(operation.target);
                if (existedBefore) fs.copyFileSync(operation.target, backup);
                if (action !== 'delete') fs.writeFileSync(stage, operation.content, 'utf8');
                journalOperations.push({
                    kind: operation.kind,
                    action,
                    target: operation.target,
                    stage,
                    backup,
                    existed_before: existedBefore,
                });
            });

            const journal = {
                schema_version: 'canonical_fs_transaction.v1',
                transaction_id: transactionId,
                transaction_dir: transactionDir,
                plan_hash: hashValue(plan),
                status: 'prepared',
                operations: journalOperations,
            };
            writeFileAtomic(paths.journal, stablePrettyStringify(journal));
            return journal;
        } catch (error) {
            fs.rmSync(transactionDir, { recursive: true, force: true });
            throw error;
        }
    }

    function publishOperation(operation, index, total) {
        invokeFault('before_publish', { operation, index, total });
        ensureDir(path.dirname(operation.target));
        if (operation.action === 'delete') {
            fs.unlinkSync(operation.target);
        } else {
            fs.renameSync(operation.stage, operation.target);
        }
        invokeFault('after_publish', { operation, index, total });
    }

    async function preflight(plan) {
        recoverPendingTransaction();
        assertExpectedRevisions(paths, plan);
        const operations = materializeOperations(paths, plan);
        const token = Object.freeze({
            id: `fs-preflight-${++preflightSequence}`,
            plan_hash: hashValue(plan),
            operation_count: operations.length,
        });
        preflightPlans.set(token, plan);
        return token;
    }

    async function commit(plan, preflightResult) {
        if (!preflightResult || preflightPlans.get(preflightResult) !== plan) {
            throw new Error('Invalid or stale filesystem canonical mutation preflight token');
        }

        acquireLock();
        try {
            recoverPendingTransactionUnlocked();
            assertExpectedRevisions(paths, plan);
            const operations = materializeOperations(paths, plan);
            const journal = prepareTransaction(plan, operations);
            invokeFault('after_journal', { journal });

            try {
                journal.operations.forEach((operation, index) => {
                    publishOperation(operation, index, journal.operations.length);
                });
                const committedJournal = { ...journal, status: 'committed' };
                writeFileAtomic(paths.journal, stablePrettyStringify(committedJournal));
                invokeFault('after_commit_mark', { journal: committedJournal });
                cleanupJournalArtifacts(committedJournal);
                preflightPlans.delete(preflightResult);
                return {
                    committed: true,
                    recoverable: true,
                    operation: plan.operation,
                    file_operation_count: journal.operations.length,
                    canonical_upsert_count: (plan.changes.canonical_upserts || []).length,
                    canonical_removal_count: (plan.changes.canonical_removals || []).length,
                    question_rebinding_count: (plan.changes.question_rebindings || []).length,
                    review_migration_count: (plan.changes.review_migrations || []).length,
                    answer_invalidation_count: (plan.changes.answer_invalidations || []).length,
                    answer_archive_count: (plan.changes.answer_archives || []).length,
                };
            } catch (error) {
                if (error?.simulatedCrash) throw error;
                recoverPendingTransactionUnlocked();
                throw error;
            }
        } finally {
            releaseLock();
        }
    }

    return {
        preflight,
        commit,
        recoverPendingTransaction,
        paths,
    };
}

module.exports = {
    SimulatedCanonicalMutationCrash,
    createFsCanonicalMutationStore,
};
