'use strict';

const fs = require('fs');
const path = require('path');
const {
    ensureDir,
    readJsonl,
    stableStringify,
} = require('../../../scripts/lib/io');
const { createDedupFsPaths } = require('./dedup-paths');
const {
    hashValue,
    entityIndexResource,
    hotspotIndexResource,
    questionSnapshotResource,
    relationQueueResource,
    matchingEntityRefs,
    listHotspots,
    hotspotRefs,
    resolveQuestionsByRefs,
    readQueueManifest,
    relationQueueSnapshot,
} = require('./dedup-suggestion-repositories');

function clone(value) {
    return structuredClone(value);
}

function decisionLogResource() {
    return 'dedup-relation-decisions';
}

function decisionSnapshotResource(relationCandidateKey) {
    return `dedup-relation-decision:${String(relationCandidateKey)}`;
}

function findRelationCandidateSnapshot(paths, relationCandidateKey) {
    const manifest = readQueueManifest(paths);
    for (const queue of Object.values(manifest.queues || {})) {
        const candidate = (queue.relation_candidates || []).find(
            (item) => item.relation_candidate_key === relationCandidateKey,
        );
        if (!candidate) continue;

        const mode = queue.mode || candidate.scope;
        const seed = queue.seed ?? candidate.seed;
        return {
            candidate: clone(candidate),
            source_revisions: clone(queue.source_revisions || []),
            resource: relationQueueResource(mode, seed),
            revision: hashValue(queue),
        };
    }
    return null;
}

function findLatestRelationDecisionSnapshot(paths, relationCandidateKey) {
    const decisions = readJsonl(paths.relationDecisions, []);
    for (let index = decisions.length - 1; index >= 0; index--) {
        const decision = decisions[index];
        if (decision.relation_candidate_key !== relationCandidateKey) continue;
        return {
            decision: clone(decision),
            resource: decisionSnapshotResource(relationCandidateKey),
            revision: hashValue(decision),
        };
    }
    return null;
}

function currentDecisionRevisions(paths, decision) {
    const candidate = decision?.candidate_snapshot;
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) {
        throw new Error('Dedup relation decision candidate_snapshot is required');
    }
    const mode = String(candidate.scope || '').trim();
    const seed = String(candidate.seed || '').trim();
    if (!mode || !seed) {
        throw new Error('Dedup relation decision candidate scope and seed are required');
    }

    const queueSnapshot = relationQueueSnapshot(paths, mode, seed);
    if (mode === 'entity') {
        const refs = matchingEntityRefs(paths, seed);
        const questions = resolveQuestionsByRefs(paths, refs);
        return new Map([
            [queueSnapshot.resource, queueSnapshot.revision],
            [entityIndexResource(seed), hashValue(refs)],
            [questionSnapshotResource(refs), hashValue(questions)],
        ]);
    }
    if (mode === 'hotspot') {
        const hotspots = listHotspots(paths);
        const refs = hotspotRefs(hotspots);
        const questions = resolveQuestionsByRefs(paths, refs);
        return new Map([
            [queueSnapshot.resource, queueSnapshot.revision],
            [hotspotIndexResource(), hashValue(hotspots)],
            [questionSnapshotResource(refs), hashValue(questions)],
        ]);
    }
    throw new Error(`Unsupported dedup relation decision scope: ${mode}`);
}

function normalizeExpectedRevisions(expectedRevisions) {
    if (!Array.isArray(expectedRevisions) || expectedRevisions.length === 0) {
        throw new Error('Dedup decision expected_revisions are required');
    }
    const normalized = new Map();
    for (const item of expectedRevisions) {
        const resource = String(item?.resource || '').trim();
        const revision = String(item?.revision || '').trim();
        if (!resource || !revision) {
            throw new Error('Dedup decision expected revision resource and revision are required');
        }
        if (normalized.has(resource)) {
            throw new Error(`Duplicate dedup decision expected revision: ${resource}`);
        }
        normalized.set(resource, revision);
    }
    return normalized;
}

function assertExpectedRevisions(paths, decision, expectedRevisions) {
    const expected = normalizeExpectedRevisions(expectedRevisions);
    const current = currentDecisionRevisions(paths, decision);

    for (const [resource, expectedRevision] of expected.entries()) {
        const actualRevision = current.get(resource);
        if (actualRevision !== expectedRevision) {
            throw new Error(
                `Revision mismatch for ${resource}: expected ${expectedRevision}, got ${actualRevision || 'missing'}`,
            );
        }
    }
    if (expected.size !== current.size) {
        throw new Error('Dedup decision expected revision set does not cover all current sources');
    }
    for (const resource of current.keys()) {
        if (!expected.has(resource)) {
            throw new Error(`Dedup decision expected revision missing for ${resource}`);
        }
    }
}

function writeDecisionLogAtomic(paths, decisions) {
    ensureDir(path.dirname(paths.relationDecisions));
    const tempPath = `${paths.relationDecisions}.tmp-${process.pid}-${Date.now()}`;
    const body = decisions.map(stableStringify).join('\n');
    try {
        fs.writeFileSync(tempPath, body ? `${body}\n` : '', 'utf8');
        fs.renameSync(tempPath, paths.relationDecisions);
    } finally {
        if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
    }
}

function withDecisionLock(paths, callback) {
    ensureDir(path.dirname(paths.relationDecisionLock));
    let fileDescriptor;
    try {
        fileDescriptor = fs.openSync(paths.relationDecisionLock, 'wx');
    } catch (error) {
        if (error?.code === 'EEXIST') {
            throw new Error('Dedup relation decision gateway is busy');
        }
        throw error;
    }

    try {
        return callback();
    } finally {
        fs.closeSync(fileDescriptor);
        if (fs.existsSync(paths.relationDecisionLock)) {
            fs.unlinkSync(paths.relationDecisionLock);
        }
    }
}

function createFsDedupDecisionRepositories(options = {}) {
    if (!options.root) throw new Error('Filesystem dedup decision repository root is required');
    const paths = options.paths || createDedupFsPaths(options.root);

    const relationCandidateRepository = {
        async get(relationCandidateKey) {
            const key = String(relationCandidateKey || '').trim();
            if (!key) throw new Error('relationCandidateKey is required');
            return findRelationCandidateSnapshot(paths, key);
        },
    };

    const relationDecisionRepository = {
        async get(relationCandidateKey) {
            const key = String(relationCandidateKey || '').trim();
            if (!key) throw new Error('relationCandidateKey is required');
            return findLatestRelationDecisionSnapshot(paths, key);
        },
    };

    const relationDecisionGateway = {
        async record(decision, options = {}) {
            if (!decision || typeof decision !== 'object' || Array.isArray(decision)) {
                throw new Error('relation decision is required');
            }
            if (decision.schema_version !== 'dedup_relation_decision.v1') {
                throw new Error('relation decision schema_version is invalid');
            }

            return withDecisionLock(paths, () => {
                assertExpectedRevisions(paths, decision, options.expected_revisions);
                const decisions = readJsonl(paths.relationDecisions, []);
                const next = [...decisions, clone(decision)];
                writeDecisionLogAtomic(paths, next);
                return {
                    recorded: true,
                    resource: decisionLogResource(),
                    revision: hashValue(next),
                    decision_count: next.length,
                };
            });
        },
    };

    return {
        relationCandidateRepository,
        relationDecisionRepository,
        relationDecisionGateway,
    };
}

module.exports = {
    decisionLogResource,
    decisionSnapshotResource,
    findRelationCandidateSnapshot,
    findLatestRelationDecisionSnapshot,
    currentDecisionRevisions,
    assertExpectedRevisions,
    createFsDedupDecisionRepositories,
};
