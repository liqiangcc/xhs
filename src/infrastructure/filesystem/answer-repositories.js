'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { readAnswerFile } = require('../../../scripts/lib/answer_store');
const { stableStringify } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function clone(value) {
    return structuredClone(value);
}

function answerMergeResource(targetCanonicalId, sourceCanonicalId) {
    return `answer-merge:${targetCanonicalId}:${sourceCanonicalId}`;
}

function activeAnswerPath(paths, canonicalId) {
    return path.join(paths.answersDir, `${canonicalId}.md`);
}

function archivedAnswerPath(paths, canonicalId) {
    return path.join(paths.answerArchiveDir, `${canonicalId}.md`);
}

function readSemanticAnswer(filePath) {
    if (!fs.existsSync(filePath)) return null;
    const answer = readAnswerFile(filePath);
    return {
        canonical_id: answer.metadata.canonical_id,
        metadata: clone(answer.metadata),
        content: answer.content,
    };
}

function readRawOrNull(filePath) {
    return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : null;
}

function parseAnswerMergeResource(resource) {
    const prefix = 'answer-merge:';
    if (!String(resource).startsWith(prefix)) {
        throw new Error(`Unsupported filesystem answer resource: ${resource}`);
    }
    const parts = String(resource).slice(prefix.length).split(':');
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
        throw new Error(`Invalid filesystem answer merge resource: ${resource}`);
    }
    return {
        targetCanonicalId: parts[0],
        sourceCanonicalId: parts[1],
    };
}

function revisionForAnswerResource(paths, resource) {
    const { targetCanonicalId, sourceCanonicalId } = parseAnswerMergeResource(resource);
    return crypto.createHash('sha256')
        .update(stableStringify({
            target_answer: readRawOrNull(activeAnswerPath(paths, targetCanonicalId)),
            source_answer: readRawOrNull(activeAnswerPath(paths, sourceCanonicalId)),
            source_archive: readRawOrNull(archivedAnswerPath(paths, sourceCanonicalId)),
        }), 'utf8')
        .digest('hex');
}

function createFsAnswerRepository(options = {}) {
    if (!options.root) throw new Error('Filesystem answer repository root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        async loadMergeState(targetCanonicalId, sourceCanonicalId) {
            const resource = answerMergeResource(targetCanonicalId, sourceCanonicalId);
            const archivePath = archivedAnswerPath(paths, sourceCanonicalId);
            return {
                target_answer: readSemanticAnswer(activeAnswerPath(paths, targetCanonicalId)),
                source_answer: readSemanticAnswer(activeAnswerPath(paths, sourceCanonicalId)),
                source_archive_exists: fs.existsSync(archivePath),
                resource,
                revision: revisionForAnswerResource(paths, resource),
            };
        },
    };
}

module.exports = {
    answerMergeResource,
    activeAnswerPath,
    archivedAnswerPath,
    revisionForAnswerResource,
    createFsAnswerRepository,
};
