'use strict';

const path = require('path');

function createCanonicalFsPaths(root) {
    const resolvedRoot = path.resolve(root);
    const transactionDir = path.join(resolvedRoot, '.xhs', 'canonical-mutations');
    return Object.freeze({
        root: resolvedRoot,
        canonicalQuestions: path.join(resolvedRoot, 'data', 'questions', 'canonical_questions.jsonl'),
        questions: path.join(resolvedRoot, 'data', 'questions', 'questions.jsonl'),
        indexDir: path.join(resolvedRoot, 'data', 'indexes'),
        mergeHistory: path.join(resolvedRoot, 'data', 'manifests', 'canonical', 'canonical_merge_history.json'),
        transactionDir,
        journal: path.join(transactionDir, 'active.json'),
        lock: path.join(transactionDir, 'mutation.lock'),
    });
}

module.exports = {
    createCanonicalFsPaths,
};
