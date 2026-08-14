'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const {
    runToday, runNext, runWeak, runPrepare, runMark, runIntegrity,
} = require('../scripts/commands/review');
const { createApplication } = require('../src/bootstrap/create-application');

const ROOT = path.resolve(__dirname, '..');
function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('review audit records all six completed vertical migrations', () => {
    const audit = read('docs/refactor/13_review_command_audit.md');
    assert.match(audit, /1\. review integrity[\s\S]*2\. review today[\s\S]*3\. review next[\s\S]*4\. review weak[\s\S]*5\. review prepare[\s\S]*6\. review mark/);
    for (const schema of [
        'review_integrity.v1', 'review_today.v1', 'review_next.v1',
        'review_weak.v1', 'review_prepare_result.v1', 'review_mark_result.v1',
    ]) assert.match(audit, new RegExp(schema.replace('.', '\\.')));
    for (const command of ['integrity', 'today', 'next', 'weak', 'prepare', 'mark']) {
        assert.match(audit, new RegExp(`review ${command}[\\s\\S]*(?:completed|已完成)`, 'i'));
    }
    assert.match(audit, /ReviewProgressRepository/);
    assert.match(audit, /ReviewMutationGateway/);
});

test('Production Application exposes every migrated Review capability', () => {
    const app = createApplication({ root: ROOT });
    assert.equal(Object.isFrozen(app.review), true);
    assert.deepEqual(Object.keys(app.review), ['integrity', 'today', 'next', 'weak', 'prepare', 'mark']);
    for (const name of Object.keys(app.review)) assert.equal(typeof app.review[name], 'function');
});

test('all Review commands delegate business behavior to Application', () => {
    const sources = [runToday, runNext, runWeak, runPrepare, runMark, runIntegrity]
        .map((fn) => fn.toString());
    for (const source of sources) assert.match(source, /createApplication/);
    assert.match(runMark.toString(), /application\.review\.mark/);
    assert.match(runMark.toString(), /date:\s*defaultDate\(options\)/);
    assert.match(runMark.toString(), /canonical_id:\s*options\[['"]canonical-id['"]\]\s*\|\|\s*options\._\[0\]/);
    assert.match(runMark.toString(), /result:\s*options\.result\s*\|\|\s*options\.status/);
    assert.match(runMark.toString(), /write_mutation:\s*!options\.noWrite/);

    const commandModule = read('scripts/commands/review.js');
    assert.doesNotMatch(commandModule, /loadCanonicalQuestions|loadProgress|saveProgress|ensureProgressItems|progressMap|applyReviewResult|appendSessionEvent/);
    assert.doesNotMatch(commandModule, /review_store|canonical_store/);
    assert.match(commandModule, /return result\.ok === false \? 1 : 0/);
});

test('prepare selection and publication remain separated behind Application and Publisher', () => {
    const application = read('src/application/review/review-prepare.js');
    const publisherPort = read('src/ports/services/review-plan-publisher.js');
    const publisherAdapter = read('src/infrastructure/filesystem/review-plan-publisher-adapter.js');
    const queueState = read('src/application/review/review-queue-state-coordinator.js');
    assert.match(application, /createReviewQueueStateCoordinator/);
    assert.match(application, /assertReviewPlanPublisher/);
    assert.match(application, /planPublisher\.publish/);
    assert.match(publisherPort, /ReviewPlanPublisher/);
    assert.match(publisherAdapter, /createFileReviewPlanPublisherAdapter/);
    assert.match(queueState, /assertReviewProgressRepository/);
    assert.match(queueState, /progressRepository\.snapshot/);
    assert.match(queueState, /progressRepository\.save/);
});

test('mark separates Domain transition from atomic ReviewMutationGateway persistence', () => {
    const application = read('src/application/review/review-mark.js');
    const resultPolicy = read('src/domain/review/review-result-policy.js');
    const markPolicy = read('src/domain/review/review-mark-policy.js');
    const gatewayPort = read('src/ports/repositories/review-mutation-gateway.js');
    const gatewayAdapter = read('src/infrastructure/filesystem/review-mutation-gateway-adapter.js');
    const transaction = read('src/infrastructure/filesystem/review-file-transaction.js');

    assert.match(application, /applyReviewResult/);
    assert.match(application, /normalizeReviewMarkInput/);
    assert.match(application, /createReviewSessionEvent/);
    assert.match(application, /mutationGateway\.snapshot/);
    assert.match(application, /mutationGateway\.commit/);
    assert.doesNotMatch(application, /fs\.|path\.|saveProgress|appendSessionEvent/);
    assert.match(resultPolicy, /Invalid review result/);
    assert.match(markPolicy, /feedback-closed-at requires at least one quality-defect/);
    assert.match(gatewayPort, /ReviewMutationGateway/);
    assert.match(gatewayAdapter, /review_progress/);
    assert.match(gatewayAdapter, /review_session/);
    assert.match(transaction, /status:\s*'prepared'/);
    assert.match(transaction, /status:\s*'committed'/);
    assert.match(transaction, /recoverPendingTransaction/);
});

test('legacy review_store keeps compatibility wrappers but Review Domain is the result-transition SSOT', () => {
    const reviewStore = read('scripts/lib/review_store.js');
    assert.match(reviewStore, /review-result-policy/);
    assert.match(reviewStore, /applyReviewResultPolicy/);
    assert.doesNotMatch(reviewStore, /goodIntervals|easyIntervals|confidence = clamp|difficulty = clamp/);
});

test('existing ReviewRepository remains Canonical-merge-specific rather than becoming generic Review CRUD', () => {
    const port = read('src/ports/repositories/review-repository.js');
    assert.match(port, /loadMergeState/);
    assert.doesNotMatch(port, /listProgress|saveProgress|appendSession|today|next|weak|prepare|integrity|mark/);
});
