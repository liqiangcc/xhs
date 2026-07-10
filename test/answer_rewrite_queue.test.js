'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJsonl } = require('../scripts/lib/io');
const { run } = require('../scripts/content/build_answer_rewrite_queue');

test('rewrite queue creates bounded stable batches and task files', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-rewrite-queue-'));
    const canonicals = Array.from({ length: 11 }, (_, index) => ({ canonical_id: `cq_${index}`, canonical_title: `题 ${index}`, primary_domain: {}, review_priority: 'P2', frequency: 1 }));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), canonicals);
    writeJsonl(path.join(root, 'data', 'manifests', 'quality', 'answer_type_audit.jsonl'), canonicals.map((row) => ({ canonical_id: row.canonical_id, answer_type: 'concept', secondary_requirements: [], risk_flags: [] })));
    fs.mkdirSync(path.join(root, 'review', 'answers'), { recursive: true });
    for (const row of canonicals) fs.writeFileSync(path.join(root, 'review', 'answers', `${row.canonical_id}.md`), `<!-- xhs-answer: {"canonical_id":"${row.canonical_id}","status":"needs_update","quality_tier":"long_tail_baseline"} -->\n# ${row.canonical_title}\n`, 'utf8');
    assert.equal(run({ root }).batch_count, 2);
    assert.equal(run({ root, check: true, noWrite: true }).ok, true);
    assert.ok(fs.existsSync(path.join(root, 'tasks', 'answer-batches', 'TASK-20260711-0313-answer-batch-0002.md')));
    fs.rmSync(root, { recursive: true, force: true });
});
