'use strict';

const { writeJson } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function createFsCanonicalQualityReportWriter(options = {}) {
    if (!options.root) throw new Error('Filesystem canonical quality report writer root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        write(report) {
            writeJson(paths.qualityReport, report);
            return report;
        },
    };
}

module.exports = {
    createFsCanonicalQualityReportWriter,
};
