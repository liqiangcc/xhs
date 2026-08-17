'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

const AUDIT_PATH = 'docs/refactor/16_repository_role_term_audit.md';

test('repository role audit records all three bounded migrations as completed', () => {
    const audit = read(AUDIT_PATH);

    assert.match(audit, /CanonicalQualityReportWriter\s+-> CanonicalQualityReportPublisher/);
    assert.match(audit, /RelationCandidateStore -> RelationCandidatePublisher/);
    assert.match(audit, /RelationDecisionStore -> RelationDecisionGateway/);
    assert.match(audit, /There is no remaining active `next_target`/);
    assert.equal((audit.match(/next_target:/g) || []).length, 0);
});

test('Canonical quality report uses a narrow Publisher Port and publish operation', () => {
    const audit = read(AUDIT_PATH);
    const port = read('src/ports/services/canonical-quality-report-publisher.js');
    const adapter = read('src/infrastructure/filesystem/canonical-quality-report-publisher.js');
    const useCase = read('src/application/canonical/check-canonical-integrity.js');

    assert.match(port, /CanonicalQualityReportPublisher/);
    assert.match(port, /\['publish'\]/);
    assert.doesNotMatch(port, /CanonicalQualityReportWriter|\['write'\]/);
    assert.match(adapter, /publish\(report\)/);
    assert.match(useCase, /reportPublisher\.publish\(checked\)/);
    assert.match(audit, /Application decides whether a `canonical_quality_report\.v1` is published/);
});

test('RelationCandidatePublisher stays distinct from its read Repository', () => {
    const audit = read(AUDIT_PATH);
    const publisher = read('src/ports/relation-candidate-publisher.js');
    const repository = read('src/ports/repositories/relation-candidate-repository.js');

    assert.match(publisher, /RelationCandidatePublisher/);
    assert.match(publisher, /replaceQueue/);
    assert.doesNotMatch(publisher, /\['get'\]/);
    assert.match(repository, /RelationCandidateRepository/);
    assert.match(repository, /\['get'\]/);
    assert.doesNotMatch(repository, /replaceQueue/);
    assert.match(audit, /cannot authorize a relation decision or mutate Canonical state/);
});

test('RelationDecisionGateway is a revision-checked consistency boundary', () => {
    const audit = read(AUDIT_PATH);
    const gateway = read('src/ports/relation-decision-gateway.js');
    const repository = read('src/ports/repositories/relation-decision-repository.js');
    const filesystem = read('src/infrastructure/filesystem/dedup-decision-repositories.js');

    assert.match(gateway, /RelationDecisionGateway/);
    assert.match(gateway, /expected_revisions/);
    assert.match(gateway, /pending queue revision plus every source revision/);
    assert.match(repository, /RelationDecisionRepository/);
    assert.match(repository, /\['get'\]/);
    assert.doesNotMatch(repository, /\['record'\]/);

    assert.match(filesystem, /assertExpectedRevisions/);
    assert.match(filesystem, /withDecisionLock/);
    assert.match(filesystem, /writeDecisionLogAtomic/);
    assert.match(filesystem, /relation decision gateway is busy/);
    assert.match(audit, /stale-state rejection before append/);
    assert.match(audit, /atomic decision-log replacement/);
});

test('retired architecture role files and public names are removed without aliases', () => {
    const removed = [
        'src/ports/services/canonical-quality-report-writer.js',
        'src/infrastructure/filesystem/canonical-quality-report-writer.js',
        'src/ports/relation-candidate-store.js',
        'src/ports/relation-decision-store.js',
    ];
    for (const relativePath of removed) {
        assert.equal(fs.existsSync(path.join(ROOT, relativePath)), false, relativePath);
    }

    const active = [
        'src/application/canonical/check-canonical-integrity.js',
        'src/application/dedup/suggest-canonical-relations.js',
        'src/application/dedup/record-relation-decision.js',
        'src/bootstrap/create-application.js',
    ].map(read).join('\n');
    assert.doesNotMatch(active, /CanonicalQualityReportWriter|RelationCandidateStore|RelationDecisionStore/);
    assert.doesNotMatch(active, /canonical-quality-report-writer|relation-candidate-store|relation-decision-store/);
});

test('legacy scripts lib Store modules remain explicit deferred compatibility debt', () => {
    const audit = read(AUDIT_PATH);
    const deferred = [
        'scripts/lib/answer_store.js',
        'scripts/lib/canonical_store.js',
        'scripts/lib/index_store.js',
        'scripts/lib/issue_store.js',
        'scripts/lib/question_store.js',
        'scripts/lib/review_store.js',
    ];

    for (const relativePath of deferred) {
        assert.equal(fs.existsSync(path.join(ROOT, relativePath)), true, relativePath);
        assert.match(audit, new RegExp(relativePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    }
    assert.match(audit, /not approved examples for new architecture naming/);
    assert.match(audit, /Do not mass-rename them/);
});

test('role audit keeps path restructuring separate from semantic role cleanup', () => {
    const audit = read(AUDIT_PATH);
    assert.match(audit, /directory name `src\/ports\/services` is not a reason to perform a bulk folder move/);
    assert.match(audit, /path restructuring is a separate concern/);
});
