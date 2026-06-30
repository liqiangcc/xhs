'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { writeJsonl } = require('../scripts/lib/io');
const { runPrepare } = require('../scripts/commands/review');

function writeFixture(root) {
    const questionId = computeQuestionId('Redis 为什么快？');
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{
        question_id: questionId,
        original_question: 'Redis 为什么快？',
        source_note_id: 'note-a',
        source_question_index: 0,
        company: '字节',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2024',
        date: '未知',
        domain: { l1: '缓存', l2: 'Redis' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: ['Redis'],
        business_context: [],
        is_valid_for_library: true,
        canonical_id: 'cq_redis_fast',
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        canonical_id: 'cq_redis_fast',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 为什么快？'],
        question_ids: [questionId],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    }]);
}

test('review prepare --noWrite returns rows without writing a plan', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-prepare-no-write-'));
    writeFixture(root);

    const result = runPrepare({ root, date: '2026-06-30', target: 'redis', noWrite: true });

    assert.equal(result.ok, true);
    assert.equal(result.dry_run, true);
    assert.equal(result.plan_path, null);
    assert.equal(result.item_count, 1);
    assert.equal(fs.existsSync(path.join(root, 'review', 'plans', 'redis.md')), false);
    assert.equal(fs.existsSync(path.join(root, 'review', 'progress.json')), false);
});
