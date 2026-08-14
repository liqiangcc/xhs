'use strict';

const path = require('path');

function createDedupFsPaths(root) {
    if (!root) throw new Error('Dedup filesystem root is required');
    const resolvedRoot = path.resolve(root);
    return Object.freeze({
        root: resolvedRoot,
        questions: path.join(resolvedRoot, 'data', 'questions', 'questions.jsonl'),
        entityIndex: path.join(resolvedRoot, 'data', 'indexes', 'entity_index.json'),
        hotspotIndex: path.join(resolvedRoot, 'data', 'indexes', 'hotspot_index.json'),
        relationCandidateQueues: path.join(
            resolvedRoot,
            'data',
            'manifests',
            'dedup',
            'relation_candidate_queues.json',
        ),
        relationDecisions: path.join(
            resolvedRoot,
            'data',
            'manifests',
            'dedup',
            'relation_decisions.jsonl',
        ),
        relationDecisionLock: path.join(
            resolvedRoot,
            '.xhs',
            'dedup-decisions',
            'record.lock',
        ),
    });
}

module.exports = {
    createDedupFsPaths,
};
