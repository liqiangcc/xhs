'use strict';

const SCHEMA_VERSION = 'canonical_mutation_plan.v1';
const SUPPORTED_OPERATIONS = new Set(['merge', 'split', 'accept', 'canonicalize']);

function assertObject(value, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        throw new Error(`${label} must be an object`);
    }
}

function clone(value) {
    return structuredClone(value);
}

function deepFreeze(value) {
    if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
    Object.freeze(value);
    for (const child of Object.values(value)) deepFreeze(child);
    return value;
}

function normalizeExpectedRevision(item, index) {
    assertObject(item, `expected_revisions[${index}]`);
    if (!item.resource || typeof item.resource !== 'string') {
        throw new Error(`expected_revisions[${index}].resource is required`);
    }
    if (!item.revision || typeof item.revision !== 'string') {
        throw new Error(`expected_revisions[${index}].revision is required`);
    }
    return { resource: item.resource, revision: item.revision };
}

function normalizeCanonicalRecord(record, index) {
    assertObject(record, `canonical_upserts[${index}]`);
    if (!record.canonical_id) throw new Error(`canonical_upserts[${index}].canonical_id is required`);
    return clone(record);
}

function normalizeCanonicalRemoval(canonicalId, index) {
    if (!canonicalId || typeof canonicalId !== 'string') {
        throw new Error(`canonical_removals[${index}] must be a canonical_id`);
    }
    return canonicalId;
}

function normalizeQuestionRebinding(binding, index) {
    assertObject(binding, `question_rebindings[${index}]`);
    if (!binding.question_id) throw new Error(`question_rebindings[${index}].question_id is required`);
    if (!Object.prototype.hasOwnProperty.call(binding, 'from_canonical_id')) {
        throw new Error(`question_rebindings[${index}].from_canonical_id is required`);
    }
    if (
        binding.from_canonical_id !== null
        && (!binding.from_canonical_id || typeof binding.from_canonical_id !== 'string')
    ) {
        throw new Error(`question_rebindings[${index}].from_canonical_id must be a canonical_id or null`);
    }
    if (!binding.to_canonical_id || typeof binding.to_canonical_id !== 'string') {
        throw new Error(`question_rebindings[${index}].to_canonical_id is required`);
    }
    if (binding.from_canonical_id === binding.to_canonical_id) {
        throw new Error(`question_rebindings[${index}] must change canonical ownership`);
    }
    return clone(binding);
}

function normalizeObjectList(values, label) {
    return values.map((value, index) => {
        assertObject(value, `${label}[${index}]`);
        return clone(value);
    });
}

function assertNoCanonicalUpsertRemovalOverlap(upserts, removals) {
    const removed = new Set(removals);
    const overlap = upserts.find((record) => removed.has(record.canonical_id));
    if (overlap) {
        throw new Error(`Canonical ${overlap.canonical_id} cannot be upserted and removed in the same mutation plan`);
    }
}

/**
 * Build a storage-agnostic application mutation plan.
 *
 * Revisions are opaque values supplied by outbound read ports. The plan never
 * contains JSONL paths, filesystem paths, temp-file names, or adapter details.
 * Infrastructure decides how semantic changes map to files or database rows.
 */
function createCanonicalMutationPlan(input = {}) {
    assertObject(input, 'mutation plan input');
    const operation = input.operation;
    if (!SUPPORTED_OPERATIONS.has(operation)) {
        throw new Error(`Unsupported canonical mutation operation: ${operation}`);
    }

    const changes = input.changes || {};
    assertObject(changes, 'changes');

    const expectedRevisions = (input.expected_revisions || [])
        .map(normalizeExpectedRevision);
    const canonicalUpserts = (changes.canonical_upserts || [])
        .map(normalizeCanonicalRecord);
    const canonicalRemovals = (changes.canonical_removals || [])
        .map(normalizeCanonicalRemoval);
    const questionRebindings = (changes.question_rebindings || [])
        .map(normalizeQuestionRebinding);
    const reviewMigrations = normalizeObjectList(changes.review_migrations || [], 'review_migrations');
    const answerInvalidations = normalizeObjectList(changes.answer_invalidations || [], 'answer_invalidations');
    const answerArchives = normalizeObjectList(changes.answer_archives || [], 'answer_archives');

    assertNoCanonicalUpsertRemovalOverlap(canonicalUpserts, canonicalRemovals);
    if (!canonicalUpserts.length && !canonicalRemovals.length && !questionRebindings.length) {
        throw new Error('Canonical mutation plan must contain a canonical or question-binding change');
    }

    const historyEntry = changes.history_entry == null ? null : clone(changes.history_entry);
    if (historyEntry !== null) assertObject(historyEntry, 'history_entry');

    return deepFreeze({
        schema_version: SCHEMA_VERSION,
        operation,
        expected_revisions: expectedRevisions,
        changes: {
            canonical_upserts: canonicalUpserts,
            canonical_removals: canonicalRemovals,
            question_rebindings: questionRebindings,
            review_migrations: reviewMigrations,
            answer_invalidations: answerInvalidations,
            answer_archives: answerArchives,
            rebuild_indexes: Boolean(changes.rebuild_indexes),
            history_entry: historyEntry,
        },
    });
}

module.exports = {
    SCHEMA_VERSION,
    createCanonicalMutationPlan,
};
