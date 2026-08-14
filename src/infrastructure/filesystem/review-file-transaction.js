'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { ensureDir, readJson, stablePrettyStringify } = require('../../../scripts/lib/io');

let transactionSequence = 0;

class SimulatedReviewMutationCrash extends Error {
    constructor(message = 'Simulated review mutation crash') {
        super(message);
        this.name = 'SimulatedReviewMutationCrash';
        this.simulatedCrash = true;
    }
}

function removeIfExists(filePath) {
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
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

function writeFileAtomic(filePath, content) {
    ensureDir(path.dirname(filePath));
    const tempPath = `${filePath}.tmp-${process.pid}-${Date.now()}-${++transactionSequence}`;
    fs.writeFileSync(tempPath, content, 'utf8');
    fs.renameSync(tempPath, filePath);
}

function createReviewFileTransaction(options = {}) {
    if (!options.root) throw new Error('ReviewFileTransaction root is required');
    const root = path.resolve(options.root);
    const reviewDir = path.join(root, 'review');
    const transactionDir = path.join(root, '.xhs', 'review-mutations');
    const paths = Object.freeze({
        root,
        progress: path.join(reviewDir, 'progress.json'),
        sessionsDir: path.join(reviewDir, 'sessions'),
        transactionDir,
        journal: path.join(transactionDir, 'active.json'),
        lock: path.join(transactionDir, 'mutation.lock'),
    });
    const faultInjector = typeof options.faultInjector === 'function'
        ? options.faultInjector
        : null;

    function sessionPath(date) {
        return path.join(paths.sessionsDir, `${date}.json`);
    }

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
                    throw new Error(`Review mutation lock is already held by pid ${owner.pid}`);
                }
                removeIfExists(paths.lock);
            }
        }
        throw new Error('Unable to acquire review mutation lock');
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
            if (operation.existed_before) {
                if (!fs.existsSync(operation.backup)) {
                    throw new Error(`Cannot recover review mutation; backup missing: ${operation.backup}`);
                }
                ensureDir(path.dirname(operation.target));
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

    function readProgress(date) {
        return readJson(paths.progress, {
            schema_version: 'review_progress_store.v1',
            updated_at: date,
            items: [],
        });
    }

    function readSession(date) {
        return readJson(sessionPath(date), {
            schema_version: 'review_session.v1',
            date,
            events: [],
        });
    }

    function hashResources(resourcePaths) {
        const hash = crypto.createHash('sha256');
        for (const filePath of resourcePaths) {
            hash.update(filePath, 'utf8');
            hash.update('\0', 'utf8');
            if (fs.existsSync(filePath)) hash.update(fs.readFileSync(filePath));
            else hash.update('<missing>', 'utf8');
            hash.update('\0', 'utf8');
        }
        return hash.digest('hex');
    }

    function progressRevision() {
        return hashResources([paths.progress]);
    }

    function mutationRevision(date) {
        return hashResources([paths.progress, sessionPath(date)]);
    }

    function prepareTransaction(operations, metadata = {}) {
        ensureDir(paths.transactionDir);
        const transactionId = `tx-${Date.now()}-${process.pid}-${++transactionSequence}`;
        const transactionRoot = path.join(paths.transactionDir, transactionId);
        const stageDir = path.join(transactionRoot, 'stage');
        const backupDir = path.join(transactionRoot, 'backup');
        ensureDir(stageDir);
        ensureDir(backupDir);

        const journalOperations = [];
        try {
            operations.forEach((operation, index) => {
                const stage = path.join(stageDir, `${String(index).padStart(3, '0')}.next`);
                const backup = path.join(backupDir, `${String(index).padStart(3, '0')}.previous`);
                const existedBefore = fs.existsSync(operation.target);
                if (existedBefore) fs.copyFileSync(operation.target, backup);
                fs.writeFileSync(stage, operation.content, 'utf8');
                journalOperations.push({
                    kind: operation.kind,
                    target: operation.target,
                    stage,
                    backup,
                    existed_before: existedBefore,
                });
            });

            const journal = {
                schema_version: 'review_fs_transaction.v1',
                transaction_id: transactionId,
                transaction_dir: transactionRoot,
                status: 'prepared',
                metadata,
                operations: journalOperations,
            };
            writeFileAtomic(paths.journal, stablePrettyStringify(journal));
            return journal;
        } catch (error) {
            fs.rmSync(transactionRoot, { recursive: true, force: true });
            throw error;
        }
    }

    function commit(input = {}) {
        const expectedRevision = input.expected_revision;
        const scope = input.scope;
        const date = input.date;
        const operations = input.operations || [];
        if (!expectedRevision || typeof expectedRevision !== 'string') {
            throw new Error('Review file transaction expected_revision is required');
        }
        if (!['progress', 'mutation'].includes(scope)) {
            throw new Error('Review file transaction scope must be progress or mutation');
        }
        if (scope === 'mutation' && (!date || typeof date !== 'string')) {
            throw new Error('Review file transaction date is required for mutation scope');
        }
        if (!operations.length) throw new Error('Review file transaction operations are required');

        acquireLock();
        try {
            recoverPendingTransactionUnlocked();
            const actualRevision = scope === 'progress'
                ? progressRevision()
                : mutationRevision(date);
            if (actualRevision !== expectedRevision) {
                throw new Error(
                    `Review revision mismatch: expected ${expectedRevision}, got ${actualRevision}`,
                );
            }

            const journal = prepareTransaction(operations, input.metadata || {});
            invokeFault('after_journal', { journal });
            try {
                journal.operations.forEach((operation, index) => {
                    invokeFault('before_publish', { operation, index, total: journal.operations.length });
                    ensureDir(path.dirname(operation.target));
                    fs.renameSync(operation.stage, operation.target);
                    invokeFault('after_publish', { operation, index, total: journal.operations.length });
                });
                const committedJournal = { ...journal, status: 'committed' };
                writeFileAtomic(paths.journal, stablePrettyStringify(committedJournal));
                invokeFault('after_commit_mark', { journal: committedJournal });
                cleanupJournalArtifacts(committedJournal);
                return {
                    committed: true,
                    recoverable: true,
                    file_operation_count: journal.operations.length,
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
        paths,
        sessionPath,
        readProgress,
        readSession,
        progressRevision,
        mutationRevision,
        recoverPendingTransaction,
        commit,
    };
}

module.exports = {
    SimulatedReviewMutationCrash,
    createReviewFileTransaction,
};
