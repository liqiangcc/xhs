'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { createReviewIntegrityUseCase } = require('../src/application/review/review-integrity');

function createUseCase(overrides = {}) {
    return createReviewIntegrityUseCase({
        canonicalCatalogRepository: {
            list() {
                return [{ canonical_id: 'cq_a' }];
            },
        },
        progressReader: {
            load() {
                return { items: [{ canonical_id: 'cq_a' }] };
            },
        },
        sessionReader: {
            list() {
                return [];
            },
        },
        ...overrides,
    });
}

test('ReviewIntegrity Application preserves review_integrity.v1 and maps opaque session sources to file DTO fields', () => {
    const integrity = createUseCase({
        sessionReader: {
            list() {
                return [{
                    source: 'review/sessions/bad.json',
                    parse_error: 'invalid_json',
                }];
            },
        },
    });

    const result = integrity();

    assert.equal(result.schema_version, 'review_integrity.v1');
    assert.equal(result.ok, false);
    assert.deepEqual(result.stale_session_events, [{
        file: 'review/sessions/bad.json',
        index: null,
        canonical_id: null,
        reason: 'invalid_json',
    }]);
    assert.equal('source' in result.stale_session_events[0], false);
});

test('ReviewIntegrity requires only the three narrow read capabilities', () => {
    assert.throws(
        () => createReviewIntegrityUseCase({
            canonicalCatalogRepository: {},
            progressReader: { load() {} },
            sessionReader: { list() {} },
        }),
        /CanonicalCatalogRepository\.list\(\) is required/,
    );
    assert.throws(
        () => createReviewIntegrityUseCase({
            canonicalCatalogRepository: { list() {} },
            progressReader: {},
            sessionReader: { list() {} },
        }),
        /ReviewProgressReader\.load\(\) is required/,
    );
    assert.throws(
        () => createReviewIntegrityUseCase({
            canonicalCatalogRepository: { list() {} },
            progressReader: { load() {} },
            sessionReader: {},
        }),
        /ReviewSessionReader\.list\(\) is required/,
    );
});
