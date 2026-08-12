'use strict';

const { readJsonl } = require('../../../scripts/lib/io');
const { evaluateCanonicalIntegrity } = require('../../domain/canonical/integrity-policy');
const { createCanonicalFsPaths } = require('./canonical-paths');

function createFsCanonicalIntegrityChecker(options = {}) {
    if (!options.root) throw new Error('Filesystem canonical integrity checker root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        async check() {
            const records = readJsonl(paths.canonicalQuestions, []);
            const questions = readJsonl(paths.questions, []);
            return evaluateCanonicalIntegrity(records, questions);
        },
    };
}

module.exports = {
    createFsCanonicalIntegrityChecker,
};
