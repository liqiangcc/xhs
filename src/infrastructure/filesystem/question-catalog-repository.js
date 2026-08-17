'use strict';

const { readJsonl } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function clone(value) {
    return structuredClone(value);
}

function createFsQuestionCatalogRepository(options = {}) {
    if (!options.root) throw new Error('Filesystem question catalog repository root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        list() {
            return readJsonl(paths.questions, []).map(clone);
        },
    };
}

module.exports = {
    createFsQuestionCatalogRepository,
};
