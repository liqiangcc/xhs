#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { readJson } = require('../lib/io');
const {
    pathsFor,
    sha256,
    auditOneCandidate,
    validateAnswerEvidence,
    validateSpecializedCandidate,
} = require('../lib/answer_quality');

const ROOT = path.resolve(__dirname, '..', '..');

function metadata(type = 'concept') {
    return { schema_version: 'answer.v1', canonical_id: 'cq_fixture', version: 1, status: 'draft', updated_at: '2026-07-11', answer_type: type, quality_tier: 'candidate' };
}

function answerContent(type = 'concept', overrides = {}) {
    const core = overrides.core || 'Redis 的事件循环、内存访问和数据结构共同降低了典型命令路径的额外开销。';
    const implementation = overrides.implementation || '';
    const project = overrides.project || '如果没有可核验的真实经历，应明确说明这里只做方案推演。';
    const followups = overrides.followups || [
        '- 问：Redis 单线程为什么仍能处理高并发？答：命令执行路径短，网络 I/O 由事件循环复用。',
        '- 问：Redis 是否所有工作都在一个线程？答：不是，持久化和部分 I/O 会使用后台线程，需绑定版本。',
        '- 问：大 Key 为什么会拖慢 Redis？答：单次命令工作量增大，会延长事件循环处理其他请求的等待。',
    ].join('\n');
    const meta = metadata(type);
    return [
        `<!-- xhs-answer: ${JSON.stringify(meta)} -->`, '# Redis 为什么快？', '',
        '## 核心结论', '', core, '', '## 1 分钟版', '', 'Redis 主要减少网络等待、内存访问和常见操作的计算成本。', '',
        '## 3 分钟版', '', `沿客户端请求、事件分派、命令执行和响应写回解释。${implementation}`, '',
        '## 关键细节', '', '不同版本会把部分网络 I/O 放到辅助线程，但命令语义仍需按官方版本说明。', '',
        '## 原理机制', '', '事件循环在就绪连接之间推进状态，避免为每个连接绑定阻塞线程。', '',
        '## 项目经验版', '', project, '', '## 常见追问', '', followups, '',
        '## 易错点', '', '不能把性能归因于单线程一个因素，也不能声称所有操作都是 O(1)。', '',
    ].join('\n');
}

function fixtureContext(type = 'concept') {
    return {
        canonical: { canonical_id: 'cq_fixture', canonical_title: 'Redis 为什么快？' },
        answer_type: type,
        primary_entities: ['Redis'],
        source_variants: ['Redis 为什么快？'],
        source_questions: [{ question_id: 'q_fixture', original_question: 'Redis 为什么快？' }],
    };
}

function fixtureEvidence(content, config) {
    return {
        schema_version: 'answer_evidence.v1', canonical_id: 'cq_fixture', candidate_sha256: sha256(content), checked_at: '2026-07-11',
        writer: { writer_id: 'writer-fixture', writer_version: 'fixture.v1' },
        sources: [{ source_id: 'redis-doc', title: 'Redis documentation', locator: 'https://redis.io/docs/latest/develop/reference/clients/', source_type: 'official_documentation', checked_at: '2026-07-11' }],
        claims: [{ claim_id: 'claim-1', text: 'Redis uses an event loop for client processing.', source_ids: ['redis-doc'], answer_locations: ['原理机制'] }],
        source_question_coverage: [{ question_id: 'q_fixture', covered: true, answer_locations: ['核心结论', '原理机制'] }],
        review: {
            reviewer_id: 'reviewer-fixture', review_version: 'fixture.v1', independent: true, decision: 'pass', revision_round: 1,
            hard_failures: [], scores: Object.fromEntries(Object.entries(config.dimensions).map(([key, rule]) => [key, rule.weight])), revision_suggestions: [],
        },
    };
}

function validateFixture(name, type, overrides, expectedHardFailure, config, evidenceMutator) {
    const content = answerContent(type, overrides);
    const candidate = { metadata: metadata(type), content };
    const evidence = fixtureEvidence(content, config);
    if (type === 'coding') evidence.validation = { boundary_tests: [
        { case: 'empty', expected: '-1', actual: '-1', passed: true },
        { case: 'single', expected: '0', actual: '0', passed: true },
        { case: 'normal', expected: '2', actual: '2', passed: true },
    ] };
    if (evidenceMutator) evidenceMutator(evidence);
    const evidenceResult = validateAnswerEvidence(evidence, candidate, fixtureContext(type), config);
    const specialized = validateSpecializedCandidate(candidate, evidence, fixtureContext(type));
    const hardFailures = [...new Set([...evidenceResult.hard_failures, ...specialized.hard_failures])];
    const actualPass = evidenceResult.errors.length === 0 && specialized.errors.length === 0;
    const expectationMet = expectedHardFailure ? hardFailures.includes(expectedHardFailure) : actualPass;
    return { name, expectation_met: expectationMet, expected_hard_failure: expectedHardFailure, actual_pass: actualPass, hard_failures: hardFailures, errors: [...evidenceResult.errors, ...specialized.errors] };
}

function runEvidenceFixtures(options = {}) {
    const root = options.root ? path.resolve(options.root) : ROOT;
    const config = readJson(path.join(root, 'config', 'answer_quality.json'));
    const rows = [
        validateFixture('valid_concept', 'concept', {}, null, config),
        validateFixture('generic_followups', 'concept', { followups: '- 问：这道题最先要澄清什么？答：看情况。\n- 问：方案的主要代价是什么？答：看情况。\n- 问：如何验证回答不是背诵？答：做实验。' }, 'generic_followups', config),
        validateFixture('cross_topic_core', 'concept', { core: 'MySQL B+ 树的叶子节点保存行或主键，查询可能需要回表。' }, 'cross_topic_contamination', config),
        validateFixture('placeholder_sql', 'coding', { implementation: '\n\n```sql\nSELECT column_name FROM source_table WHERE id = <id>\n```' }, 'placeholder_implementation', config),
        validateFixture('fabricated_project', 'project', { project: '我主导线上优化，将延迟降低 40%。' }, 'fabricated_experience', config),
    ];
    return { schema_version: 'answer_evidence_fixture_report.v1', ok: rows.every((row) => row.expectation_met), dry_run: Boolean(options.noWrite), fixture_count: rows.length, rows };
}

function runEvidenceCheck(options = {}) {
    const root = options.root ? path.resolve(options.root) : ROOT;
    const paths = pathsFor(root);
    const files = fs.existsSync(paths.candidateAnswersDir)
        ? fs.readdirSync(paths.candidateAnswersDir).filter((name) => name.endsWith('.md')).sort().map((name) => path.join(paths.candidateAnswersDir, name))
        : [];
    const rows = files.map((filePath) => auditOneCandidate(filePath, { ...options, root }));
    return { schema_version: 'answer_evidence_check.v1', ok: rows.every((row) => row.ok), candidate_count: rows.length, rows };
}

function parseArgs(argv) {
    const options = { noWrite: true };
    for (let index = 2; index < argv.length; index++) {
        if (argv[index] === '--fixtures') options.fixtures = true;
        else if (argv[index] === '--root') options.root = argv[++index];
        else if (argv[index] === '--noWrite' || argv[index] === '--check') options.noWrite = true;
        else throw new Error(`Unknown option: ${argv[index]}`);
    }
    return options;
}

function main(argv = process.argv) {
    try {
        const options = parseArgs(argv);
        const result = options.fixtures ? runEvidenceFixtures(options) : runEvidenceCheck(options);
        console.log(JSON.stringify(result, null, 2));
        return result.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) process.exitCode = main(process.argv);

module.exports = { runEvidenceFixtures, runEvidenceCheck, main };
