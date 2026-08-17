'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    createCheckCanonicalIntegrityUseCase,
} = require('../src/application/canonical/check-canonical-integrity');

function report(ok = true) {
    return {
        schema_version: 'canonical_quality_report.v1',
        ok,
        orphan_binding_count: ok ? 0 : 1,
    };
}

test('CheckCanonicalIntegrity returns the report and publishes it by default', () => {
    const writes = [];
    const check = createCheckCanonicalIntegrityUseCase({
        integrityChecker: {
            check() {
                return report(false);
            },
        },
        reportPublisher: {
            publish(value) {
                writes.push(structuredClone(value));
            },
        },
    });

    const result = check();

    assert.equal(result.ok, false);
    assert.equal(result.orphan_binding_count, 1);
    assert.deepEqual(writes, [result]);
});

test('CheckCanonicalIntegrity suppresses report persistence when write_report is false', () => {
    let writeCount = 0;
    const check = createCheckCanonicalIntegrityUseCase({
        integrityChecker: { check: () => report(true) },
        reportPublisher: {
            publish() {
                writeCount += 1;
            },
        },
    });

    const result = check({ write_report: false });

    assert.equal(result.ok, true);
    assert.equal(writeCount, 0);
});

test('CheckCanonicalIntegrity preserves async checker compatibility without forcing sync adapters async', async () => {
    const writes = [];
    const check = createCheckCanonicalIntegrityUseCase({
        integrityChecker: { async check() { return report(true); } },
        reportPublisher: { publish(value) { writes.push(value); } },
    });

    const result = await check();

    assert.equal(result.ok, true);
    assert.equal(writes.length, 1);
});

test('CheckCanonicalIntegrity rejects invalid reports and missing outbound capabilities', () => {
    assert.throws(
        () => createCheckCanonicalIntegrityUseCase({
            integrityChecker: {},
            reportPublisher: { publish() {} },
        }),
        /CanonicalIntegrityChecker\.check\(\) is required/,
    );
    assert.throws(
        () => createCheckCanonicalIntegrityUseCase({
            integrityChecker: { check() {} },
            reportPublisher: {},
        }),
        /CanonicalQualityReportPublisher\.publish\(\) is required/,
    );

    const check = createCheckCanonicalIntegrityUseCase({
        integrityChecker: { check: () => ({ schema_version: 'wrong', ok: true }) },
        reportPublisher: { publish() {} },
    });
    assert.throws(check, /schema_version must be canonical_quality_report\.v1/);
});
