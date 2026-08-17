'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJsonl } = require('../scripts/lib/io');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');
const {
    createFsCanonicalCatalogRepository,
} = require('../src/infrastructure/filesystem/canonical-catalog-repository');

function canonical(id, frequency) {
    return {
        canonical_id: id,
        canonical_title: id,
        aliases: [id],
        question_ids: [`q_${id}`],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['美团'],
        frequency,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

test('filesystem Canonical catalog adapter returns records without query semantics', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-list-fs-'));
    try {
        const paths = createCanonicalFsPaths(root);
        const records = [canonical('cq_second', 1), canonical('cq_first', 9)];
        writeJsonl(paths.canonicalQuestions, records);

        const repository = createFsCanonicalCatalogRepository({ root, paths });
        const loaded = await repository.list();

        assert.deepEqual(loaded, records);
        loaded[0].canonical_title = 'mutated snapshot';
        const loadedAgain = await repository.list();
        assert.equal(loadedAgain[0].canonical_title, 'cq_second');
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
