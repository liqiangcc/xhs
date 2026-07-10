'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { buildAudit } = require('../scripts/content/build_pilot_answer_audit');

function writeJson(filePath, value) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

test('pilot audit derives candidate, evidence, reviewer, and human-review state from artifacts', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-pilot-audit-'));
    try {
        const canonicalId = 'cq_fixture';
        writeJson(path.join(root, 'data', 'manifests', 'quality', 'answer_pilot_set.json'), {
            items: [{ canonical_id: canonicalId, answer_type: 'coding', risk_flags: ['risk'], selection_reasons: ['selection'] }],
        });
        fs.mkdirSync(path.join(root, 'review', 'candidates', 'answers'), { recursive: true });
        fs.writeFileSync(path.join(root, 'review', 'candidates', 'answers', `${canonicalId}.md`), '# candidate\n', 'utf8');
        writeJson(path.join(root, 'review', 'candidates', 'audits', `${canonicalId}.json`), { ok: true });
        writeJson(path.join(root, 'review', 'evidence', `${canonicalId}.json`), {
            review: { independent: true, decision: 'pass' },
            human_review: { reviewer_type: 'human', decision: 'approved' },
        });

        const result = buildAudit({ root });
        assert.equal(result.rows.length, 1);
        assert.deepEqual(result.rows[0], {
            canonical_id: canonicalId,
            answer_type: 'coding',
            batch_id: 'pilot-coding',
            risk_flags: ['risk'],
            selection_reasons: ['selection'],
            candidate_status: 'rendered',
            independent_review_status: 'passed',
            evidence_status: 'verified',
            human_review_status: 'approved',
            promotion_status: 'ready_to_promote',
        });
        assert.equal(result.summary.candidate_rendered, 1);
        assert.equal(result.summary.evidence_verified, 1);
        assert.equal(result.summary.human_review_approved, 1);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
