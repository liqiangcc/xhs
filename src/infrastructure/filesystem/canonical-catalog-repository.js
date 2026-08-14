'use strict';

const { readJsonl } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function clone(value) {
    return structuredClone(value);
}

function createFsCanonicalCatalogRepository(options = {}) {
    if (!options.root) throw new Error('Filesystem canonical catalog repository root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        async list() {
            return readJsonl(paths.canonicalQuestions, []).map(clone);
        },
    };
}

module.exports = {
    createFsCanonicalCatalogRepository,
};
