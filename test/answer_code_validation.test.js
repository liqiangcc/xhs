'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { compileJava, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');

test('Java validation compiles complete classes and rejects broken implementations', () => {
    assert.equal(compileJava('public class Solution { public static int add(int a, int b) { return a + b; } }').ok, true);
    assert.equal(compileJava('public class Solution { public static int add(int a, int b) { return a + ; } }').ok, false);
    assert.equal(compileJava('static int add(int a, int b) { return a + b; }').error, 'java_class_required');
});

test('SQL validation checks statement structure balance and placeholders', () => {
    assert.equal(parseSql('SELECT department_id, COUNT(*) FROM employee GROUP BY department_id').ok, true);
    assert.equal(parseSql('SELECT * FROM source_table WHERE id = <id>').error, 'sql_placeholder');
    assert.equal(parseSql('SELECT * FROM employee WHERE (id = 1').error, 'sql_unbalanced_parentheses');
});

test('coding candidates require three declared passing boundary cases', () => {
    const content = [
        '## 核心结论', '数组双指针。', '## 常见追问',
        '- 问：空数组？答：返回空。', '- 问：重复值？答：保持不变量。', '- 问：复杂度？答：O(n)。',
        '## 3 分钟版', '```java', 'public class Solution { public static int size(int[] a) { return a == null ? 0 : a.length; } }', '```',
    ].join('\n');
    const candidate = { metadata: { answer_type: 'coding' }, content };
    const evidence = { validation: { boundary_tests: [{ case: 'empty', expected: 0, actual: 0, passed: true }] } };
    const context = { canonical: { canonical_title: '数组长度' }, primary_entities: ['数组'], source_variants: ['数组长度'] };
    const result = validateSpecializedCandidate(candidate, evidence, context);
    assert.ok(result.hard_failures.includes('unrunnable_implementation'));
    assert.ok(result.errors.some((row) => row.error === 'three_passing_boundary_tests_required'));
});

