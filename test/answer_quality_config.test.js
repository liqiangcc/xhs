'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');
const quality = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'answer_quality.json'), 'utf8'));
const contentStrategy = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'content_strategy.json'), 'utf8'));

test('answer quality contract has the exact promotion thresholds', () => {
    assert.equal(quality.schema_version, 'answer_quality.v1');
    assert.equal(quality.batch_size, 10);
    assert.equal(quality.promotion.minimum_total_score, 90);
    assert.equal(quality.promotion.required_status, 'ready');
    assert.equal(quality.promotion.required_quality_tier, 'curated');
    assert.equal(quality.promotion.require_zero_hard_failures, true);
    assert.equal(quality.promotion.require_independent_review, true);
    assert.equal(quality.promotion.require_evidence, true);
    assert.equal(quality.promotion.maximum_revision_rounds, 2);

    const totalWeight = Object.values(quality.dimensions).reduce((sum, dimension) => sum + dimension.weight, 0);
    assert.equal(totalWeight, 100);
    assert.equal(quality.dimensions.facts_and_evidence.minimum_score, 23);
    assert.equal(quality.dimensions.directness_and_relevance.minimum_score, 18);
    for (const dimension of Object.values(quality.dimensions)) {
        assert.ok(dimension.minimum_score >= dimension.weight * 0.8);
        assert.ok(Array.isArray(dimension.requirements) && dimension.requirements.length > 0);
    }
});

test('answer quality contract covers every answer type and required hard failure', () => {
    const expectedTypes = ['behavior', 'coding', 'concept', 'mechanism', 'project', 'scenario'];
    assert.deepEqual(Object.keys(quality.type_requirements).sort(), expectedTypes);
    assert.deepEqual(Object.keys(contentStrategy.answer_types).sort(), expectedTypes);
    for (const type of expectedTypes) {
        assert.ok(quality.type_requirements[type].length >= 5, `${type} needs a complete rubric`);
    }

    const ids = quality.hard_failures.map((item) => item.id);
    assert.equal(new Set(ids).size, ids.length);
    for (const required of [
        'wrong_answer_type',
        'off_topic',
        'cross_topic_contamination',
        'unsupported_factual_claim',
        'missing_version_boundary',
        'fabricated_experience',
        'generic_followups',
        'placeholder_implementation',
        'unrunnable_implementation',
        'uncovered_source_variant',
        'template_only_answer',
        'missing_independent_review',
        'missing_evidence',
    ]) {
        assert.ok(ids.includes(required), `missing hard failure: ${required}`);
    }
});

test('evidence policy fails closed and excludes discovery-only sources', () => {
    assert.equal(quality.evidence_policy.unverified_disposition, 'needs_update');
    assert.equal(quality.evidence_policy.claim_mapping_required, true);
    assert.equal(quality.evidence_policy.checked_at_required, true);
    assert.ok(quality.evidence_policy.source_priority.includes('official_documentation'));
    assert.ok(quality.evidence_policy.source_priority.includes('executable_test_or_reproducible_experiment'));
    assert.ok(quality.evidence_policy.discovery_only_sources.includes('old_long_tail_answer'));
    assert.ok(quality.evidence_policy.primary_source_required_for.includes('numeric_threshold'));
});
