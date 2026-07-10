'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const {
    buildReport,
    compareToBaseline,
    sectionBody,
} = require('../scripts/content/analyze_answer_semantics');

const ROOT = path.resolve(__dirname, '..');
const BASELINE_PATH = path.join(ROOT, 'data', 'manifests', 'quality', 'answer_semantic_baseline.json');

test('extracts complete answer sections instead of stopping at the first paragraph', () => {
    const content = [
        '## 常见追问',
        '',
        '- 问：一？答：一。',
        '- 问：二？答：二。',
        '',
        '## 易错点',
        '',
        '- 不要答错。',
    ].join('\n');
    assert.equal(sectionBody(content, '常见追问'), '- 问：一？答：一。\n- 问：二？答：二。');
});

test('freezes the audited long-tail starting defects and only rejects regressions', () => {
    const baseline = JSON.parse(fs.readFileSync(BASELINE_PATH, 'utf8'));
    assert.equal(baseline.total_answer_count, 9260);
    assert.equal(baseline.curated.answer_count, 100);
    assert.equal(baseline.long_tail.answer_count, 9160);
    assert.equal(baseline.long_tail.defects.fallback_core_count, 1818);
    assert.equal(baseline.long_tail.defects.generic_scenario_count, 580);
    assert.equal(baseline.long_tail.defects.documents_with_all_global_followups_count, 9160);
    assert.equal(baseline.long_tail.coding.answer_count, 735);
    assert.equal(baseline.long_tail.coding.unique_implementation_block_count, 31);
    assert.equal(baseline.long_tail.coding.generic_problem_spec_count, 417);
    assert.equal(baseline.long_tail.coding.generic_sql_count, 36);
    assert.equal(baseline.long_tail.coding.generic_dp_count, 27);
    assert.equal(baseline.long_tail.coding.placeholder_implementation_count, 480);

    const current = buildReport({ root: ROOT, date: '2026-07-11' });
    assert.equal(compareToBaseline(current, baseline).ok, true);

    const regressed = structuredClone(current);
    regressed.long_tail.defects.fallback_core_count = baseline.long_tail.defects.fallback_core_count + 1;
    const comparison = compareToBaseline(regressed, baseline);
    assert.equal(comparison.ok, false);
    assert.deepEqual(comparison.regressions[0], {
        metric: 'long_tail.defects.fallback_core_count',
        error: 'defect_regression',
        baseline: 1818,
        current: 1819,
    });
});
