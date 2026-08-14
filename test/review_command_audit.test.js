'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const {
    runToday,
    runNext,
    runWeak,
    runPrepare,
    runMark,
    runIntegrity,
} = require('../scripts/commands/review');
const { createApplication } = require('../src/bootstrap/create-application');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('review audit freezes migration order and high-risk boundaries', () => {
    const audit = read('docs/refactor/13_review_command_audit.md');

    assert.match(
        audit,
        /1\. review integrity[\s\S]*2\. review today[\s\S]*3\. review next[\s\S]*4\. review weak[\s\S]*5\. review prepare[\s\S]*6\. review mark/,
    );
    assert.match(audit, /review_integrity\.v1/);
    assert.match(audit, /review_today\.v1/);
    assert.match(audit, /review_next\.v1/);
    assert.match(audit, /review_weak\.v1/);
    assert.match(audit, /review_prepare_result\.v1/);
    assert.match(audit, /review_mark_result\.v1/);
    assert.match(audit, /review integrity[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /review today[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /saveProgress\([\s\S]*appendSessionEvent/);
    assert.match(audit, /ReviewMutationPlan \/ ReviewMutationStore/);
});

test('Production Application exposes only migrated Review capabilities', () => {
    const app = createApplication({ root: ROOT });

    assert.equal(Object.isFrozen(app.review), true);
    assert.deepEqual(Object.keys(app.review), ['integrity', 'today']);
    assert.equal(typeof app.review.integrity, 'function');
    assert.equal(typeof app.review.today, 'function');
    assert.equal('next' in app.review, false);
    assert.equal('weak' in app.review, false);
    assert.equal('prepare' in app.review, false);
    assert.equal('mark' in app.review, false);
});

test('review integrity delegates to Application and preserves ok=false exit semantics in Interface', () => {
    const source = runIntegrity.toString();
    const commandModule = read('scripts/commands/review.js');

    assert.match(source, /createApplication/);
    assert.match(source, /application\.review\.integrity/);
    assert.doesNotMatch(
        source,
        /loadCanonicalQuestions|loadProgress|fs\.readdirSync|fs\.readFileSync|saveProgress|appendSessionEvent|writePlan/,
    );
    assert.match(commandModule, /return result\.ok === false \? 1 : 0/);
});

test('review today delegates initialization ranking and optional persistence to Application', () => {
    const source = runToday.toString();

    assert.match(source, /createApplication/);
    assert.match(source, /application\.review\.today/);
    assert.match(source, /date:\s*defaultDate\(options\)/);
    assert.match(source, /with_issues:\s*Boolean\(options\[['"]with-issues['"]\]\)/);
    assert.match(source, /write_progress:\s*!options\.noWrite/);
    assert.doesNotMatch(
        source,
        /loadReviewState|ensureProgressItems|saveProgress|canonicalRows|dueRows|rankReviewRows|loadReviewStrategy|loadIssueLinks/,
    );
});

test('next weak and prepare still synthesize progress and persist it unless noWrite', () => {
    const commandModule = read('scripts/commands/review.js');

    assert.match(
        commandModule,
        /function loadReviewState[\s\S]*ensureProgressItems\([\s\S]*if \(!options\.noWrite\)[\s\S]*saveProgress\(/,
    );

    for (const source of [runNext.toString(), runWeak.toString(), runPrepare.toString()]) {
        assert.match(source, /loadReviewState/);
    }
});

test('prepare owns query filters and Markdown plan publication before migration', () => {
    const source = runPrepare.toString();
    const commandModule = read('scripts/commands/review.js');

    assert.match(source, /options\.priority/);
    assert.match(source, /options\.status/);
    assert.match(source, /options\.domain/);
    assert.match(source, /options\.company/);
    assert.match(source, /options\.level/);
    assert.match(source, /options\.topic/);
    assert.match(source, /writePlan/);
    assert.match(commandModule, /function writePlan[\s\S]*fs\.writeFileSync/);
});

test('mark still combines Review Domain transition with two separate filesystem writes', () => {
    const source = runMark.toString();

    assert.match(source, /applyReviewResult/);
    assert.match(source, /saveProgress/);
    assert.match(source, /appendSessionEvent/);
    assert.match(source, /saveProgress[\s\S]*appendSessionEvent/);
    assert.match(source, /feedback-closed-at requires at least one quality-defect/);
    assert.match(source, /oral-version must be one_minute/);
});

test('legacy Review helpers delegate migrated pure policies while retaining pending persistence/config compatibility', () => {
    const reviewStore = read('scripts/lib/review_store.js');
    const scheduler = read('scripts/lib/review_scheduler.js');

    assert.match(reviewStore, /require\(['"]fs['"]\)/);
    assert.match(reviewStore, /domain\/review\/progress-policy/);
    assert.match(reviewStore, /function loadProgress/);
    assert.match(reviewStore, /function saveProgress/);
    assert.match(reviewStore, /function applyReviewResult/);
    assert.match(reviewStore, /defaultProgressItemPolicy/);
    assert.match(reviewStore, /ensureProgressItemsPolicy/);

    assert.match(scheduler, /domain\/review\/ranking-policy/);
    assert.match(scheduler, /function loadReviewStrategy/);
    assert.match(scheduler, /scoreReviewRowPolicy/);
    assert.match(scheduler, /rankReviewRowsPolicy/);
    assert.match(scheduler, /readJson/);
});

test('existing ReviewRepository remains Canonical-merge-specific rather than becoming a generic Review port', () => {
    const port = read('src/ports/repositories/review-repository.js');

    assert.match(port, /loadMergeState/);
    assert.doesNotMatch(port, /listProgress|saveProgress|appendSession|today|weak|integrity/);
});
