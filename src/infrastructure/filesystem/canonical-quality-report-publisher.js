'use strict';

const { writeJson } = require('../../../scripts/lib/io');
const { createCanonicalFsPaths } = require('./canonical-paths');

function createFsCanonicalQualityReportPublisher(options = {}) {
    if (!options.root) throw new Error('Filesystem canonical quality report publisher root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        publish(report) {
            writeJson(paths.qualityReport, report);
            return report;
        },
    };
}

module.exports = {
    createFsCanonicalQualityReportPublisher,
};
