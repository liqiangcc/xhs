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
    assert.match(audit, /review next[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /review weak[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /review prepare[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /saveProgress\([\s\S]*appendSessionEvent/);
    assert.match(audit, /ReviewMutationPlan/);
});

test('Production Application exposes only migrated Review capabilities', () => {
    const app = createApplication({ root: ROOT });

    assert.equal(Object.isFrozen(app.review), true);
    assert.deepEqual(Object.keys(app.review), ['integrity', 'today', 'next', 'weak', 'prepare']);
    assert.equal(typeof app.review.integrity, 'function');
    assert.equal(typeof app.review.today, 'function');
    assert.equal(typeof app.review.next, 'function');
    assert.equal(typeof app.review.weak, 'function');
    assert.equal(typeof app.review.prepare, 'function');
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

test('review today next weak and prepare delegate queue semantics to Application', () => {
    const todaySource = runToday.toString();
    const nextSource = runNext.toString();
    const weakSource = runWeak.toString();
    const prepareSource = runPrepare.toString();

    assert.match(todaySource, /createApplication/);
    assert.match(todaySource, /application\.review\.today/);
    assert.match(todaySource, /date:\s*defaultDate\(options\)/);
    assert.match(todaySource, /with_issues:\s*Boolean\(options\[['"]with-issues['"]\]\)/);
    assert.match(todaySource, /write_progress:\s*!options\.noWrite/);
    assert.doesNotMatch(todaySource, /loadReviewState|ensureProgressItems|saveProgress|canonicalRows|dueRows|rankReviewRows|loadReviewStrategy|loadIssueLinks/);

    assert.match(nextSource, /createApplication/);
    assert.match(nextSource, /application\.review\.next/);
    assert.match(nextSource, /date:\s*defaultDate\(options\)/);
    assert.match(nextSource, /days:\s*options\.days/);
    assert.match(nextSource, /with_issues:\s*Boolean\(options\[['"]with-issues['"]\]\)/);
    assert.match(nextSource, /write_progress:\s*!options\.noWrite/);
    assert.doesNotMatch(nextSource, /loadReviewState|upcomingRows|ensureProgressItems|saveProgress|canonicalRows|rankReviewRows|loadReviewStrategy|loadIssueLinks/);

    assert.match(weakSource, /createApplication/);
    assert.match(weakSource, /application\.review\.weak/);
    assert.match(weakSource, /date:\s*defaultDate\(options\)/);
    assert.match(weakSource, /with_issues:\s*Boolean\(options\[['"]with-issues['"]\]\)/);
    assert.match(weakSource, /write_progress:\s*!options\.noWrite/);
    assert.doesNotMatch(weakSource, /loadReviewState|ensureProgressItems|saveProgress|canonicalRows|rankReviewRows|loadReviewStrategy|loadIssueLinks/);

    assert.match(prepareSource, /createApplication/);
    assert.match(prepareSource, /application\.review\.prepare/);
    assert.match(prepareSource, /date:\s*defaultDate\(options\)/);
    assert.match(prepareSource, /target:\s*options\.target/);
    assert.match(prepareSource, /days:\s*options\.days/);
    assert.match(prepareSource, /with_issues:\s*Boolean\(options\[['"]with-issues['"]\]\)/);
    assert.match(prepareSource, /write_progress:\s*!options\.noWrite/);
    assert.match(prepareSource, /write_plan:\s*!options\.noWrite/);
    assert.doesNotMatch(prepareSource, /loadReviewState|upcomingRows|dueRows|ensureProgressItems|saveProgress|canonicalRows|rankReviewRows|loadReviewStrategy|loadIssueLinks|writePlan|fs\.writeFileSync/);
});

test('prepare query selection stays in Application while plan publication stays behind a Publisher port', () => {
    const application = read('src/application/review/review-prepare.js');
    const publisherPort = read('src/ports/services/review-plan-publisher.js');
    const publisherAdapter = read('src/infrastructure/filesystem/review-plan-publisher-adapter.js');
    const queueState = read('src/application/review/review-queue-state-coordinator.js');
    const strategyPort = read('src/ports/services/review-strategy-reader.js');
    const strategyAdapter = read('src/infrastructure/config/review-strategy-reader-adapter.js');
    const commandModule = read('scripts/commands/review.js');

    assert.match(application, /createReviewQueueStateCoordinator/);
    assert.match(application, /buildReviewQueueState/);
    assert.match(application, /input\.priority/);
    assert.match(application, /input\.status/);
    assert.match(application, /input\.domain/);
    assert.match(application, /input\.company/);
    assert.match(application, /input\.level/);
    assert.match(application, /input\.topic/);
    assert.match(application, /assertReviewPlanPublisher/);
    assert.match(application, /planPublisher\.publish/);

    assert.match(publisherPort, /ReviewPlanPublisher/);
    assert.match(publisherPort, /\['publish'\]/);
    assert.match(publisherAdapter, /createFileReviewPlanPublisherAdapter/);
    assert.match(publisherAdapter, /publish\(plan/);
    assert.match(publisherAdapter, /safeName/);
    assert.match(publisherAdapter, /fs\.writeFileSync/);
    assert.match(publisherAdapter, /review['"], ['"]plans/);
    assert.match(publisherAdapter, /Generated:/);

    assert.match(queueState, /createReviewQueueStateCoordinator/);
    assert.match(queueState, /buildReviewQueueState/);
    assert.match(queueState, /assertReviewStrategyReader/);
    assert.match(queueState, /strategyReader\.read/);
    assert.doesNotMatch(queueState, /createReviewQueueStateLoader|loadReviewQueueState/);
    assert.match(strategyPort, /ReviewStrategyReader/);
    assert.match(strategyPort, /\['read'\]/);
    assert.match(strategyAdapter, /createFileReviewStrategyReaderAdapter/);
    assert.match(strategyAdapter, /read\(\)/);

    assert.doesNotMatch(application, /ReviewPlanWriter|planWriter\.write/);
    assert.doesNotMatch(queueState, /ReviewStrategyProvider|strategyProvider\.load/);
    assert.doesNotMatch(commandModule, /function loadReviewState/);
    assert.doesNotMatch(commandModule, /function canonicalRows/);
    assert.doesNotMatch(commandModule, /function dueRows/);
    assert.doesNotMatch(commandModule, /function upcomingRows/);
    assert.doesNotMatch(commandModule, /function writePlan/);
    assert.doesNotMatch(commandModule, /review_scheduler|issue_store|loadQuestions/);
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

test('legacy Review helpers delegate migrated pure policies while retaining mark compatibility', () => {
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
    assert.doesNotMatch(port, /listProgress|saveProgress|appendSession|today|next|weak|prepare|integrity/);
});
