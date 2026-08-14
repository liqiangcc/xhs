'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJson, writeJsonl, readJson } = require('../scripts/lib/io');
const { createApplication } = require('../src/bootstrap/create-application');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');

function canonical() {
    return {
        canonical_id: 'cq_redis_fast',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？'],
        question_ids: ['q_redis_fast'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 3,
        review_priority: 'P0',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

test('production review today preserves noWrite persistence and optional issue enrichment', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-today-fs-'));
    try {
        const paths = createCanonicalFsPaths(root);
        writeJsonl(paths.canonicalQuestions, [canonical()]);
        writeJsonl(paths.questions, [{
            question_id: 'q_redis_fast',
            canonical_id: 'cq_redis_fast',
            company: '美团',
            level: '社招',
        }]);
        writeJson(path.join(root, 'review', 'issue_links.json'), {
            schema_version: 'review_issue_links.v1',
            updated_at: '2026-06-30',
            items: [{
                canonical_id: 'cq_redis_fast',
                issue_number: 12,
                issue_url: 'https://example.test/issues/12',
            }],
        });

        const app = createApplication({ root });
        const dry = app.review.today({
            date: '2026-06-30',
            with_issues: true,
            write_progress: false,
        });

        assert.equal(dry.schema_version, 'review_today.v1');
        assert.equal(dry.returned_count, 1);
        assert.equal(dry.rows[0].progress.status, 'new');
        assert.equal(dry.rows[0].issue_url, 'https://example.test/issues/12');
        assert.equal(dry.rows[0].companies.includes('美团'), true);
        assert.equal(dry.rows[0].levels.includes('社招'), true);
        assert.equal(fs.existsSync(paths.reviewProgress), false);

        const written = app.review.today({
            date: '2026-06-30',
            write_progress: true,
        });
        assert.equal(written.returned_count, 1);
        assert.equal(fs.existsSync(paths.reviewProgress), true);
        const progress = readJson(paths.reviewProgress);
        assert.equal(progress.updated_at, '2026-06-30');
        assert.equal(progress.items.length, 1);
        assert.equal(progress.items[0].canonical_id, 'cq_redis_fast');
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
