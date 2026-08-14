'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');
function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('Review queue state uses approved Coordinator and Repository roles', () => {
    const coordinator = read('src/application/review/review-queue-state-coordinator.js');
    assert.equal(fs.existsSync(path.join(ROOT, 'src/application/review/review-queue-state.js')), false);
    assert.match(coordinator, /function createReviewQueueStateCoordinator/);
    assert.match(coordinator, /return function buildReviewQueueState/);
    assert.match(coordinator, /assertReviewProgressRepository/);
    assert.match(coordinator, /progressRepository\.snapshot/);
    assert.match(coordinator, /progressRepository\.save/);
    assert.doesNotMatch(coordinator, /Loader|ProgressWriter|progressWriter/);

    for (const relativePath of [
        'src/application/review/review-today.js',
        'src/application/review/review-next.js',
        'src/application/review/review-weak.js',
        'src/application/review/review-prepare.js',
    ]) {
        const source = read(relativePath);
        assert.match(source, /createReviewQueueStateCoordinator/);
        assert.match(source, /buildReviewQueueState/);
        assert.doesNotMatch(source, /createReviewQueueStateLoader|loadReviewQueueState/);
    }
});

test('Review mark uses approved UseCase and Gateway roles rather than Store or Writer', () => {
    const application = read('src/application/review/review-mark.js');
    const gatewayPort = read('src/ports/repositories/review-mutation-gateway.js');
    const gatewayAdapter = read('src/infrastructure/filesystem/review-mutation-gateway-adapter.js');
    const repositoryPort = read('src/ports/repositories/review-progress-repository.js');

    assert.match(application, /createReviewMarkUseCase/);
    assert.match(application, /assertReviewMutationGateway/);
    assert.match(gatewayPort, /ReviewMutationGateway/);
    assert.match(gatewayPort, /\['snapshot', 'commit'\]/);
    assert.match(gatewayAdapter, /createFileReviewMutationGatewayAdapter/);
    assert.match(repositoryPort, /ReviewProgressRepository/);
    assert.doesNotMatch(application, /MutationStore|ProgressWriter/);

    assert.equal(fs.existsSync(path.join(ROOT, 'src/ports/repositories/review-progress-writer.js')), false);
    assert.equal(fs.existsSync(path.join(ROOT, 'src/infrastructure/filesystem/review-progress-writer.js')), false);
});

test('Review naming audit records completed Review naming decisions', () => {
    const audit = read('docs/refactor/14_naming_convention_audit.md');
    assert.match(audit, /ReviewPlanPublisher[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewStrategyReader[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewQueueStateCoordinator[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewProgressRepository[\s\S]*(?:completed|已完成)/i);
    assert.match(audit, /ReviewMutationGateway[\s\S]*(?:completed|已完成)/i);
});
