'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const {
    runList,
    runCheck,
    runStats,
} = require('../scripts/commands/canonical');
const { createApplication } = require('../src/bootstrap/create-application');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('canonical read-only audit freezes behavior and migration order', () => {
    const audit = read('docs/refactor/12_canonical_read_only_command_audit.md');

    assert.match(audit, /1\. canonical list[\s\S]*2\. canonical stats[\s\S]*3\. canonical check/);
    assert.match(audit, /canonical_list\.v1/);
    assert.match(audit, /canonical_stats\.v1/);
    assert.match(audit, /canonical_quality_report\.v1/);
    assert.match(audit, /report\.ok=false[\s\S]*exit remains 0/);
    assert.match(audit, /CanonicalCatalogRepository\.list\(\)/);
    assert.match(audit, /Do not make the CLI call `priorityRank\(\)` after migration/);
});

test('legacy list and stats remain read-only while awaiting vertical migration', () => {
    const listSource = runList.toString();
    const statsSource = runStats.toString();

    assert.match(listSource, /loadCanonicalQuestions/);
    assert.match(listSource, /priorityRank/);
    assert.match(statsSource, /loadCanonicalQuestions/);
    assert.match(statsSource, /loadQuestions/);

    for (const source of [listSource, statsSource]) {
        assert.doesNotMatch(source, /writeJson|writeJsonl|saveCanonicalQuestions|saveQuestions/);
    }
});

test('legacy check has only its characterized quality-report write boundary', () => {
    const checkSource = runCheck.toString();

    assert.match(checkSource, /loadCanonicalQuestions/);
    assert.match(checkSource, /loadQuestions/);
    assert.match(checkSource, /evaluateCanonicalIntegrity/);
    assert.match(checkSource, /shouldWriteReports/);
    assert.match(checkSource, /writeJson\(paths\.qualityReport, report\)/);
    assert.doesNotMatch(checkSource, /writeJsonl|saveCanonicalQuestions|saveQuestions/);
});

test('Production Application does not expose read-only canonical use cases before migration', () => {
    const app = createApplication({ root: ROOT });

    assert.equal('list' in app.canonical, false);
    assert.equal('stats' in app.canonical, false);
    assert.equal('check' in app.canonical, false);
    assert.equal(typeof app.canonical.merge, 'function');
    assert.equal(typeof app.canonical.split, 'function');
    assert.equal(typeof app.canonical.canonicalizeQuestionGroup, 'function');
});
