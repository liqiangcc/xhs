'use strict';

function revisionOf(snapshot) {
    return {
        resource: snapshot.resource,
        revision: snapshot.revision,
    };
}

function normalizeRevisionSet(revisions, label) {
    if (!Array.isArray(revisions) || revisions.length === 0) {
        throw new Error(`${label} revisions are required`);
    }
    const map = new Map();
    for (const item of revisions) {
        const resource = String(item?.resource || '').trim();
        const revision = String(item?.revision || '').trim();
        if (!resource || !revision) {
            throw new Error(`${label} revision resource and revision are required`);
        }
        if (map.has(resource)) throw new Error(`Duplicate ${label} revision: ${resource}`);
        map.set(resource, revision);
    }
    return map;
}

function assertSourcesFresh(expectedRevisions, currentRevisions) {
    const expected = normalizeRevisionSet(expectedRevisions, 'relation candidate source');
    const current = normalizeRevisionSet(currentRevisions, 'current relation source');
    if (expected.size !== current.size) {
        throw new Error('Stale relation candidate sources: source set changed');
    }
    for (const [resource, expectedRevision] of expected.entries()) {
        const currentRevision = current.get(resource);
        if (currentRevision !== expectedRevision) {
            throw new Error(
                `Stale relation candidate source ${resource}: expected ${expectedRevision}, got ${currentRevision || 'missing'}`,
            );
        }
    }
}

module.exports = {
    revisionOf,
    normalizeRevisionSet,
    assertSourcesFresh,
};
