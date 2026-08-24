'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJsonl } = require('../scripts/lib/io');
const { createApplication } = require('../src/bootstrap/create-application');
const { createDedupFsPaths } = require('../src/infrastructure/filesystem/dedup-paths');

function question(id, note, canonicalId) {
    return {
        question_id: id,
        original_question: `Question ${id}`,
        source_note_id: note,
        source_question_index: 0,
        company: '未知',
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2026',
        date: '未知',
        domain: { l1: '计算机基础', l2: '数据结构与算法' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: [],
        business_context: [],
        is_valid_for_library: true,
        canonical_id: canonicalId,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    };
}

test('filesystem pair candidate can be explicitly reviewed and applied as relation-only', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-pair-fs-'));
    try {
        const paths = createDedupFsPaths(root);
        writeJsonl(paths.questions, [
            question('q_a', 'note-a', 'cq_a'),
            question('q_b', 'note-b', 'cq_b'),
        ]);
        const app = createApplication({ root });
        const suggested = await app.dedup.suggest({ mode: 'pair', question_ids: ['q_a', 'q_b'] });
        const candidate = suggested.relation_candidates[0];

        assert.match(suggested.source_revisions[0].resource, /^dedup-questions-by-ids:/);
        const decided = await app.dedup.recordDecision({
            relation_candidate_key: candidate.relation_candidate_key,
            relation: 'related',
            actor: { type: 'ai', id: 'pair-review-test' },
            rationale: 'Explicit source review found related but distinct response contracts.',
        });
        assert.equal(decided.ok, true);

        const applied = await app.dedup.applyDecision({
            relation_candidate_key: candidate.relation_candidate_key,
        });
        assert.equal(applied.ok, true);
        assert.equal(applied.applied, false);
        assert.equal(applied.relation, 'related');
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
