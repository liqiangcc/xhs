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

test('repository role audit freezes exactly one next bounded rename target', () => {
    const audit = read(AUDIT_PATH);

    assert.match(audit, /next_target: CanonicalQualityReportWriter -> CanonicalQualityReportPublisher/);
    assert.equal((audit.match(/next_target:/g) || []).length, 1);
    assert.match(audit, /P1 RelationCandidateStore -> RelationCandidatePublisher/);
    assert.match(audit, /P2 RelationDecisionStore -> RelationDecisionGateway only after characterization is green/);
    assert.match(audit, /One semantic rename per bounded commit/);
});

test('CanonicalQualityReportWriter is characterized as one publication capability before rename', () => {
    const audit = read(AUDIT_PATH);
    const port = read('src/ports/services/canonical-quality-report-writer.js');

    assert.match(port, /CanonicalQualityReportWriter/);
    assert.match(port, /\['write'\]/);
    assert.match(port, /publication/i);
    assert.match(audit, /CanonicalQualityReportWriter → CanonicalQualityReportPublisher/);
    assert.match(audit, /Classification: \*\*rename candidate\*\*/);
    assert.match(audit, /Application decides whether a Canonical quality report should be published/);
});

test('RelationCandidateStore stays distinct from its read Repository and is classified as Publisher debt', () => {
    const audit = read(AUDIT_PATH);
    const store = read('src/ports/relation-candidate-store.js');
    const repository = read('src/ports/repositories/relation-candidate-repository.js');

    assert.match(store, /RelationCandidateStore/);
    assert.match(store, /replaceQueue/);
    assert.doesNotMatch(store, /getPending/);
    assert.match(repository, /RelationCandidateRepository/);
    assert.match(repository, /getPending/);
    assert.doesNotMatch(repository, /replaceQueue/);
    assert.match(audit, /RelationCandidateStore → RelationCandidatePublisher/);
    assert.match(audit, /filesystem implementation replaces\/publishes one pending review queue/);
});

test('RelationDecisionStore is frozen as a revision-checked consistency boundary before Gateway rename', () => {
    const audit = read(AUDIT_PATH);
    const store = read('src/ports/relation-decision-store.js');
    const repository = read('src/ports/repositories/relation-decision-repository.js');
    const filesystem = read('src/infrastructure/filesystem/dedup-decision-repositories.js');

    assert.match(store, /RelationDecisionStore/);
    assert.match(store, /record/);
    assert.match(store, /expected_queue_revision/);
    assert.match(store, /expected_source_revisions/);
    assert.match(repository, /RelationDecisionRepository/);
    assert.match(repository, /getLatest/);
    assert.doesNotMatch(repository, /record/);

    assert.match(filesystem, /expected_queue_revision/);
    assert.match(filesystem, /expected_source_revisions/);
    assert.match(filesystem, /lock/i);
    assert.match(filesystem, /revision/i);

    assert.match(audit, /RelationDecisionStore → RelationDecisionGateway/);
    assert.match(audit, /Classification: \*\*boundary audit required\*\*/);
    assert.match(audit, /queue revision semantics/);
    assert.match(audit, /lock ownership and stale-state rejection/);
});

test('legacy scripts lib Store modules are explicit deferred compatibility debt, not naming precedent', () => {
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

    assert.match(audit, /legacy technical\/compatibility modules/);
    assert.match(audit, /not approved examples of the `Store` architecture role/);
    assert.match(audit, /Do not mass-rename them/);
});

test('role audit prevents folder-name cleanup from being mixed into semantic role cleanup', () => {
    const audit = read(AUDIT_PATH);

    assert.match(audit, /directory name `src\/ports\/services` is not a reason to perform a bulk folder move/);
    assert.match(audit, /path restructuring is a separate concern/);
    assert.match(audit, /move src\/ports\/services as a directory/);
});
