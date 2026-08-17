'use strict';

const {
    assertCanonicalIntegrityChecker,
} = require('../../ports/services/canonical-integrity-checker');
const {
    assertCanonicalQualityReportPublisher,
} = require('../../ports/services/canonical-quality-report-publisher');

function assertIntegrityReport(report) {
    if (!report || typeof report !== 'object') {
        throw new Error('canonical integrity report is required');
    }
    if (report.schema_version !== 'canonical_quality_report.v1') {
        throw new Error('canonical integrity report schema_version must be canonical_quality_report.v1');
    }
    if (typeof report.ok !== 'boolean') {
        throw new Error('canonical integrity report ok must be a boolean');
    }
    return report;
}

function isPromiseLike(value) {
    return Boolean(value && typeof value.then === 'function');
}

function createCheckCanonicalIntegrityUseCase(dependencies = {}) {
    const integrityChecker = assertCanonicalIntegrityChecker(dependencies.integrityChecker);
    const reportPublisher = assertCanonicalQualityReportPublisher(dependencies.reportPublisher);

    function finalize(report, input) {
        const checked = assertIntegrityReport(report);
        if (input.write_report === false) return checked;
        const writeResult = reportPublisher.publish(checked);
        if (isPromiseLike(writeResult)) {
            return writeResult.then(() => checked);
        }
        return checked;
    }

    return function checkCanonicalIntegrity(input = {}) {
        const result = integrityChecker.check();
        if (isPromiseLike(result)) {
            return result.then((report) => finalize(report, input));
        }
        return finalize(result, input);
    };
}

module.exports = {
    createCheckCanonicalIntegrityUseCase,
};
