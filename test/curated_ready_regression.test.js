'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJson } = require('../scripts/lib/io');
const { curatedReadyCount } = require('../scripts/content/check_curated_ready_regression');

test('curated ready counter only includes ready curated assets', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-curated-floor-'));
    const dir = path.join(root, 'review', 'answers');
    ensureDir(dir);
    const write = (name, metadata) => fs.writeFileSync(path.join(dir, `${name}.md`), `<!-- xhs-answer: ${JSON.stringify(metadata)} -->\n# ${name}\n`, 'utf8');
    write('ready', { canonical_id: 'ready', status: 'ready', quality_tier: 'curated' });
    write('failed', { canonical_id: 'failed', status: 'needs_update', quality_tier: 'curated_audit_failed' });
    assert.equal(curatedReadyCount(root), 1);
    fs.rmSync(root, { recursive: true, force: true });
});
