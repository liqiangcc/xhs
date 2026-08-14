'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJson, writeJsonl } = require('../scripts/lib/io');
const { createApplication } = require('../src/bootstrap/create-application');

function canonical(canonicalId) {
    return {
        canonical_id: canonicalId,
        canonical_title: canonicalId,
        aliases: [canonicalId],
        question_ids: [],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: [],
        frequency: 0,
        review_priority: 'P2',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
}

test('production review integrity reads progress and session facts without mutating Review state', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-integrity-fs-'));
    try {
        const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
        const progressPath = path.join(root, 'review', 'progress.json');
        const sessionPath = path.join(root, 'review', 'sessions', '2026-06-30.json');
        const invalidSessionPath = path.join(root, 'review', 'sessions', 'invalid.json');

        writeJsonl(canonicalPath, [canonical('cq_a'), canonical('cq_b')]);
        writeJson(progressPath, {
            schema_version: 'review_progress_store.v1',
            updated_at: '2026-06-30',
            items: [
                { canonical_id: 'cq_a' },
                { canonical_id: 'cq_a' },
                { canonical_id: 'cq_removed' },
                {},
            ],
        });
        writeJson(sessionPath, {
            schema_version: 'review_session.v1',
            date: '2026-06-30',
            events: [{ canonical_id: 'cq_removed' }, {}],
        });
        fs.writeFileSync(invalidSessionPath, '{not-json', 'utf8');

        const progressBefore = fs.readFileSync(progressPath, 'utf8');
        const sessionBefore = fs.readFileSync(sessionPath, 'utf8');
        const app = createApplication({ root });
        const result = app.review.integrity();

        assert.equal(result.schema_version, 'review_integrity.v1');
        assert.equal(result.ok, false);
        assert.equal(result.missing_progress_count, 1);
        assert.deepEqual(result.missing_progress_sample, ['cq_b']);
        assert.deepEqual(result.duplicate_progress_canonical_ids, [{ canonical_id: 'cq_a', count: 2 }]);
        assert.deepEqual(result.stale_progress_canonical_ids, ['cq_removed']);
        assert.equal(result.malformed_progress_items.length, 1);
        assert.deepEqual(result.stale_session_events, [
            {
                file: path.join('review', 'sessions', '2026-06-30.json'),
                index: 0,
                canonical_id: 'cq_removed',
                reason: 'unknown_canonical_id',
            },
            {
                file: path.join('review', 'sessions', '2026-06-30.json'),
                index: 1,
                canonical_id: null,
                reason: 'missing_canonical_id',
            },
            {
                file: path.join('review', 'sessions', 'invalid.json'),
                index: null,
                canonical_id: null,
                reason: 'invalid_json',
            },
        ]);
        assert.equal(fs.readFileSync(progressPath, 'utf8'), progressBefore);
        assert.equal(fs.readFileSync(sessionPath, 'utf8'), sessionBefore);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
