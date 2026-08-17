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

test('canonical read-only audit records all three completed vertical migrations', () => {
    const audit = read('docs/refactor/12_canonical_read_only_command_audit.md');

    assert.match(audit, /1\. canonical list[\s\S]*2\. canonical stats[\s\S]*3\. canonical check/);
    assert.match(audit, /canonical_list\.v1/);
    assert.match(audit, /canonical_stats\.v1/);
    assert.match(audit, /canonical_quality_report\.v1/);
    assert.match(audit, /report\.ok=false[\s\S]*exit remains 0/);
    assert.match(audit, /CanonicalCatalogRepository\.list\(\)/);
    assert.match(audit, /QuestionCatalogRepository\.list\(\)/);
    assert.match(audit, /canonical check[\s\S]*已完成|canonical check[\s\S]*completed/i);
});

test('canonical list stats and check all delegate to Application without read/query semantics in CLI', () => {
    const listSource = runList.toString();
    const statsSource = runStats.toString();
    const checkSource = runCheck.toString();

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

    assert.match(checkSource, /createApplication/);
    assert.match(checkSource, /application\.canonical\.check/);
    assert.match(checkSource, /write_report:\s*!options\.noWrite\s*&&\s*!options\.noReport/);
    assert.doesNotMatch(
        checkSource,
        /loadCanonicalQuestions|loadQuestions|evaluateCanonicalIntegrity|shouldWriteReports|writeJson|writeJsonl/,
    );
});

test('canonical command module no longer imports legacy read-side stores policies or report writer', () => {
    const source = read('scripts/commands/canonical.js');

    assert.doesNotMatch(source, /require\(['"]\.\.\/lib\/canonical_store['"]\)/);
    assert.doesNotMatch(source, /require\(['"]\.\.\/lib\/question_store['"]\)/);
    assert.doesNotMatch(source, /domain\/canonical\/integrity-policy/);
    assert.doesNotMatch(source, /\bwriteJson\b/);
    assert.doesNotMatch(source, /\bshouldWriteReports\b/);
});

test('Production Application exposes migrated Canonical reads and named Canonicalization lifecycle', () => {
    const app = createApplication({ root: ROOT });

    assert.equal(typeof app.canonical.list, 'function');
    assert.equal(typeof app.canonical.stats, 'function');
    assert.equal(typeof app.canonical.check, 'function');
    assert.equal(typeof app.canonical.merge, 'function');
    assert.equal(typeof app.canonical.split, 'function');
    assert.equal(typeof app.canonical.resolveQuestionGroupCanonicalization, 'function');
    assert.equal(typeof app.canonical.planQuestionGroupCanonicalizationMutation, 'function');
    assert.equal(typeof app.canonical.executeQuestionGroupCanonicalization, 'function');
    assert.equal('planQuestionGroup' in app.canonical, false);
    assert.equal('planQuestionGroupMutation' in app.canonical, false);
    assert.equal('canonicalizeQuestionGroup' in app.canonical, false);
});
