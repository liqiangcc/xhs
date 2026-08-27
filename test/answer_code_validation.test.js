'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { compileJava, compileC, compileCpp, validateShell, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');

test('Java validation compiles complete classes and rejects broken implementations', () => {
    assert.equal(compileJava('public class Solution { public static int add(int a, int b) { return a + b; } }').ok, true);
    assert.equal(compileJava('public class Solution { public static int add(int a, int b) { return a + ; } }').ok, false);
    assert.equal(compileJava('static int add(int a, int b) { return a + b; }').error, 'java_class_required');
});


test('C validation compiles complete source and rejects broken implementations', () => {
    assert.equal(compileC('int add(int a, int b) { return a + b; }').ok, true);
    assert.equal(compileC('int add(int a, int b) { return a + ; }').ok, false);
});


test('C++ validation compiles common fence aliases and rejects broken implementations', () => {
    assert.equal(compileCpp('#include <vector>\nint size(const std::vector<int>& values) { return static_cast<int>(values.size()); }').ok, true);
    assert.equal(compileCpp('int add(int a, int b) { return a + ; }').ok, false);
    const context = { canonical: { canonical_title: '链表中点' }, primary_entities: ['链表'], source_variants: ['链表中点'] };
    const evidence = { validation: { boundary_tests: [
        { case: 'empty', expected: 'nullptr', passed: true },
        { case: 'odd', expected: 'middle', passed: true },
        { case: 'even', expected: 'second middle', passed: true },
    ] } };
    for (const language of ['cpp', 'c++', 'cc', 'cxx']) {
        const candidate = { metadata: { answer_type: 'coding' }, content: [
            '## 核心结论', '链表中点用快慢指针。',
            '## 常见追问', '- 问：空链表？答：空。', '- 问：奇数？答：唯一中点。', '- 问：偶数？答：契约决定。',
            '## 3 分钟版', `\`\`\`${language}`, 'struct Node { int v; Node* next; };', 'Node* middle(Node* h) { Node* s=h; Node* f=h; while (f && f->next) { s=s->next; f=f->next->next; } return s; }', '\`\`\`',
        ].join('\n') };
        const result = validateSpecializedCandidate(candidate, evidence, context);
        assert.equal(result.errors.some((row) => row.error === 'coding_block_required'), false, language);
        assert.equal(result.errors.some((row) => row.error.endsWith('_validation_failed')), false, language);
    }
});


test('shell validation accepts bash/sh fences and rejects malformed scripts', () => {
    assert.equal(validateShell("set -euo pipefail\nprintf '%s\\n' ok").ok, true);
    assert.equal(validateShell('if true; then\n  echo ok').ok, false);
    const context = { canonical: { canonical_title: 'Linux URL 计数' }, primary_entities: ['awk', 'sort', 'uniq'], source_variants: ['统计 URL 次数'] };
    const evidence = { validation: { boundary_tests: [
        { case: 'non-adjacent duplicates', expected: '3/2/1', passed: true },
        { case: 'blank line', expected: 'ignored', passed: true },
        { case: 'query variants', expected: 'distinct', passed: true },
    ] } };
    for (const language of ['bash', 'sh', 'shell']) {
        const fence = '```' + language;
        const candidate = { metadata: { answer_type: 'coding' }, content: [
            '## 核心结论', 'awk、sort、uniq 组成 URL 计数流水线。',
            '## 常见追问', '- 问：为何 sort？答：让重复行相邻。', '- 问：空行？答：过滤。', '- 问：query？答：按契约处理。',
            '## 3 分钟版', fence, "awk 'NF {print $0}' urls.txt | sort | uniq -c", '```',
        ].join('\n') };
        const result = validateSpecializedCandidate(candidate, evidence, context);
        assert.equal(result.errors.some((row) => row.error === 'coding_block_required'), false, language);
        assert.equal(result.errors.some((row) => row.error.endsWith('_validation_failed')), false, language);
    }
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

