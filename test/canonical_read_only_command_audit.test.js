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
    assert.match(audit, /QuestionCatalogRepository\.list\(\)/);
    assert.match(audit, /canonical stats[\s\S]*已完成|canonical stats[\s\S]*completed/i);
});

test('canonical list and stats delegate to Application without persistence or query semantics in CLI', () => {
    const listSource = runList.toString();
    const statsSource = runStats.toString();

    assert.match(listSource, /createApplication/);
    assert.match(listSource, /application\.canonical\.list/);
    assert.match(listSource, /answer_status:\s*options\[['"]answer-status['"]\]/);
    assert.doesNotMatch(listSource, /loadCanonicalQuestions|priorityRank|writeJson|writeJsonl/);

    assert.match(statsSource, /createApplication/);
    assert.match(statsSource, /application\.canonical\.stats/);
    assert.doesNotMatch(
        statsSource,
        /loadCanonicalQuestions|loadQuestions|canonicalQuestionIds|assigned_question_rows|top_canonical|writeJson|writeJsonl/,
    );
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

test('Production Application exposes list and stats but not check after the second read migration', () => {
    const app = createApplication({ root: ROOT });

    assert.equal(typeof app.canonical.list, 'function');
    assert.equal(typeof app.canonical.stats, 'function');
    assert.equal('check' in app.canonical, false);
    assert.equal(typeof app.canonical.merge, 'function');
    assert.equal(typeof app.canonical.split, 'function');
    assert.equal(typeof app.canonical.canonicalizeQuestionGroup, 'function');
});
