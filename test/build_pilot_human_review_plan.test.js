'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { renderPlan } = require('../scripts/content/build_pilot_human_review_plan');

function writeJson(filePath, value) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

test('pilot human-review plan contains only machine-approved candidates and binds exact hashes', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-pilot-human-plan-'));
    try {
        writeJson(path.join(root, 'data', 'manifests', 'quality', 'pilot_answer_audit.json'), {
            rows: [
                { canonical_id: 'cq_ready', answer_type: 'coding', promotion_status: 'awaiting_human_review' },
                { canonical_id: 'cq_blocked', answer_type: 'project', promotion_status: 'needs_update' },
            ],
        });
        const candidatePath = path.join(root, 'review', 'candidates', 'answers', 'cq_ready.md');
        fs.mkdirSync(path.dirname(candidatePath), { recursive: true });
        fs.writeFileSync(candidatePath, '# candidate\n', 'utf8');
        const expectedHash = crypto.createHash('sha256').update('# candidate\n').digest('hex');

        const content = renderPlan({ root });
        assert.match(content, /待签核（1）/);
        assert.match(content, /cq_ready/);
        assert.match(content, new RegExp(expectedHash));
        assert.doesNotMatch(content, /cq_blocked/);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
