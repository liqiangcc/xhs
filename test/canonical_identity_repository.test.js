'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { assertCanonicalIdentityRepository } = require('../src/ports/repositories/canonical-identity-repository');
const { createInMemoryCanonicalAdapters } = require('../src/infrastructure/in-memory/canonical-adapters');

test('CanonicalIdentityRepository keeps create-if-absent reads separate from CanonicalRepository.get', async () => {
    const identityRepository = { inspect() {} };
    assert.equal(assertCanonicalIdentityRepository(identityRepository), identityRepository);
    assert.throws(
        () => assertCanonicalIdentityRepository({}),
        /CanonicalIdentityRepository\.inspect\(\) is required/,
    );

    const adapters = createInMemoryCanonicalAdapters({ canonicals: [] });
    assert.equal(await adapters.canonicalRepository.get('cq_new'), null);

    const absent = await adapters.canonicalIdentityRepository.inspect('cq_new');
    assert.equal(absent.record, null);
    assert.equal(absent.resource, 'canonical:cq_new');
    assert.equal(typeof absent.revision, 'string');

    adapters.testSupport.upsertCanonical({
        canonical_id: 'cq_new',
        canonical_title: 'concurrent',
        question_ids: [],
    });
    const present = await adapters.canonicalIdentityRepository.inspect('cq_new');
    assert.equal(present.record.canonical_id, 'cq_new');
    assert.notEqual(present.revision, absent.revision);
});
