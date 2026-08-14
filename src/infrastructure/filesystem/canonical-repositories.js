'use strict';

const crypto = require('crypto');
const { readJsonl, stableStringify } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');
const {
    revisionForLegacyCandidateResource,
} = require('./legacy-canonical-candidate-revision');

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

function ownershipResource(questionId) {
    return `canonical-ownership-by-question:${questionId}`;
}

function hashValue(value) {
    return crypto.createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function sortBindings(bindings) {
    return [...bindings].sort((a, b) =>
        String(a.question_id || '').localeCompare(String(b.question_id || ''))
        || String(a.source_note_id || '').localeCompare(String(b.source_note_id || ''), 'zh')
        || Number(a.source_question_index ?? 0) - Number(b.source_question_index ?? 0)
    );
}

function readCanonicalRecords(paths) {
    return readJsonl(paths.canonicalQuestions, []);
}

function readQuestionRows(paths) {
    return readJsonl(paths.questions, []);
}

function canonicalOwners(records, questionId) {
    return records
        .filter((record) => (record.question_ids || []).includes(questionId))
        .map((record) => record.canonical_id)
        .sort((a, b) => String(a).localeCompare(String(b)));
}

function revisionForResource(paths, resource) {
    // Legacy compatibility only: historical accept MutationPlans may still carry
    // canonical-candidate revision evidence. The Repository/Port has been retired;
    // only this opaque CAS bridge remains until its dedicated cleanup slice.
    if (resource.startsWith('canonical-candidate:')) {
        return revisionForLegacyCandidateResource(paths, resource);
    }
    if (resource.startsWith('canonical:')) {
        const canonicalId = resource.slice('canonical:'.length);
        const record = readCanonicalRecords(paths).find((item) => item.canonical_id === canonicalId) || null;
        return hashValue(record);
    }
    if (resource.startsWith('question-bindings:')) {
        const canonicalId = resource.slice('question-bindings:'.length);
        const bindings = sortBindings(
            readQuestionRows(paths).filter((row) => row.canonical_id === canonicalId),
        );
        return hashValue(bindings);
    }
    if (resource.startsWith('question-bindings-by-question:')) {
        const questionId = resource.slice('question-bindings-by-question:'.length);
        const bindings = sortBindings(
            readQuestionRows(paths).filter((row) => row.question_id === questionId),
        );
        return hashValue(bindings);
    }
    if (resource.startsWith('canonical-ownership-by-question:')) {
        const questionId = resource.slice('canonical-ownership-by-question:'.length);
        return hashValue(canonicalOwners(readCanonicalRecords(paths), questionId));
    }
    throw new Error(`Unsupported filesystem canonical resource: ${resource}`);
}

function createFsCanonicalRepositories(options = {}) {
    if (!options.root) throw new Error('Filesystem canonical repository root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    const canonicalRepository = {
        async get(canonicalId) {
            const record = readCanonicalRecords(paths).find((item) => item.canonical_id === canonicalId) || null;
            if (!record) return null;
            const resource = canonicalResource(canonicalId);
            return {
                record: clone(record),
                resource,
                revision: revisionForResource(paths, resource),
            };
        },

        async inspect(canonicalId) {
            const record = readCanonicalRecords(paths).find((item) => item.canonical_id === canonicalId) || null;
            const resource = canonicalResource(canonicalId);
            return {
                record: record ? clone(record) : null,
                resource,
                revision: revisionForResource(paths, resource),
            };
        },
    };

    const questionBindingRepository = {
        async findByCanonical(canonicalId) {
            const resource = bindingResource(canonicalId);
            const bindings = sortBindings(
                readQuestionRows(paths).filter((row) => row.canonical_id === canonicalId),
            );
            return {
                bindings: bindings.map(clone),
                resource,
                revision: revisionForResource(paths, resource),
            };
        },

        async findByQuestionId(questionId) {
            const resource = questionResource(questionId);
            const bindings = sortBindings(
                readQuestionRows(paths).filter((row) => row.question_id === questionId),
            );
            return {
                bindings: bindings.map(clone),
                resource,
                revision: revisionForResource(paths, resource),
            };
        },
    };

    const canonicalQuestionOwnershipRepository = {
        async findOwners(questionId) {
            const resource = ownershipResource(questionId);
            return {
                canonical_ids: canonicalOwners(readCanonicalRecords(paths), questionId),
                resource,
                revision: revisionForResource(paths, resource),
            };
        },
    };

    return {
        canonicalRepository,
        questionBindingRepository,
        canonicalQuestionOwnershipRepository,
        paths,
    };
}

module.exports = {
    canonicalResource,
    bindingResource,
    questionResource,
    ownershipResource,
    revisionForResource,
    createFsCanonicalRepositories,
};
