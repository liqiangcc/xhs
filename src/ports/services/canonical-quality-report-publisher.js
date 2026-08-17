'use strict';

const { assertPort } = require('../port-contract');

/**
 * CanonicalQualityReportPublisher is the narrow outbound side-effect boundary
 * for publishing canonical_quality_report.v1. Application decides whether a
 * report should be published; Infrastructure owns where/how it is persisted.
 */
function assertCanonicalQualityReportPublisher(publisher) {
    return assertPort(
        publisher,
        'CanonicalQualityReportPublisher',
        ['publish'],
    );
}

module.exports = {
    assertCanonicalQualityReportPublisher,
};
