'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, writeJson, writeJsonl } = require('../scripts/lib/io');
const { buildAnswerContext, renderCandidate, runAnswerAudit } = require('../scripts/lib/answer_quality');

const QUALITY = require('../config/answer_quality.json');

function fixtureRoot() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-candidate-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        schema_version: 'canonical_question.v1',
        canonical_id: 'cq_redis',
        canonical_title: 'Redis 为什么快？',
        aliases: ['Redis 快在哪里？'],
        question_ids: ['q1'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节'],
        frequency: 1,
        review_priority: 'P0',
        answer_status: 'needs_update',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{
        question_id: 'q1',
        canonical_id: 'cq_redis',
        original_question: 'Redis 为什么这么快？',
        question_type: '八股文_Concept',
        company: '字节',
    }]);
    return root;
}

function candidateContent() {
    return [
        '<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_redis","version":1,"status":"draft","updated_at":"2026-07-11"} -->',
        '# Redis 为什么快？',
        ...['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '项目经验版', '常见追问', '易错点'].flatMap((title) => ['', `## ${title}`, '', `${title}的题目专属内容。`]),
        '',
    ].join('\n');
}

test('context includes source variants and candidate rendering stays isolated', () => {
    const root = fixtureRoot();
    const context = buildAnswerContext({ root, canonicalId: 'cq_redis' });
    assert.equal(context.ok, true);
    assert.equal(context.answer_type, 'concept');
    assert.deepEqual(context.source_questions.map((row) => row.question_id), ['q1']);
    assert.ok(context.source_variants.includes('Redis 为什么这么快？'));

    const specPath = path.join(root, 'candidate.json');
    writeJson(specPath, { canonical_id: 'cq_redis', answer_type: 'concept', content: candidateContent() });
    const dryRun = renderCandidate({ root, spec: specPath, noWrite: true, date: '2026-07-11' });
    assert.equal(dryRun.dry_run, true);
    assert.equal(fs.existsSync(path.join(root, dryRun.candidate_path)), false);

    const rendered = renderCandidate({ root, spec: specPath, date: '2026-07-11' });
    assert.equal(rendered.ok, true);
    assert.equal(fs.existsSync(path.join(root, rendered.candidate_path)), true);
    assert.equal(fs.existsSync(path.join(root, 'review', 'answers', 'cq_redis.md')), false);
    const content = fs.readFileSync(path.join(root, rendered.candidate_path), 'utf8');
    assert.match(content.split('\n')[0], /"quality_tier":"candidate"/);
    assert.match(content.split('\n')[0], /"status":"draft"/);

    const audit = runAnswerAudit({ root, candidate: path.join(root, rendered.candidate_path), noWrite: true, type: ['concept'] });
    assert.equal(audit.ok, false);
    assert.ok(audit.rows[0].hard_failures.includes('missing_evidence'));
    assert.ok(audit.rows[0].hard_failures.includes('missing_independent_review'));
    assert.equal(fs.existsSync(path.join(root, 'review', 'candidates', 'audits', 'cq_redis.json')), false);
    fs.rmSync(root, { recursive: true, force: true });
});

test('source scenario taxonomy wins over technical conflict wording in title', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-type-scenario-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        schema_version: 'canonical_question.v1',
        canonical_id: 'cq_short_url',
        canonical_title: '百亿级短 URL 如何生成无冲突短码？',
        aliases: ['场景：短URL生成器设计：百亿URL怎么做到无冲突？'],
        question_ids: ['q-short-url'],
        primary_domain: { l1: '系统设计', l2: '分布式ID与幂等' },
        primary_entities: ['短链接', '无冲突'],
        companies: ['阿里'],
        frequency: 1,
        review_priority: 'P2',
        answer_status: 'needs_update',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{
        question_id: 'q-short-url',
        canonical_id: 'cq_short_url',
        original_question: '场景：短URL生成器设计：百亿URL怎么做到无冲突？',
        question_type: '场景设计_Scenario',
        company: '阿里',
    }]);
    const context = buildAnswerContext({ root, canonicalId: 'cq_short_url' });
    assert.equal(context.answer_type, 'scenario');
    fs.rmSync(root, { recursive: true, force: true });
});

test('structured candidate rendering excludes generic type guidance', () => {
    const root = fixtureRoot();
    const specPath = path.join(root, 'structured-candidate.json');
    writeJson(specPath, {
        canonical_id: 'cq_redis',
        answer_type: 'scenario',
        core: 'Redis 候选的题目专属核心结论。',
        points: ['专属要点一。', '专属要点二。', '专属要点三。'],
        deep: 'Redis 候选的题目专属展开。',
        mechanism: 'Redis 候选的题目专属机制。',
        followups: ['Redis 失败怎么办？|按 Redis 的题目边界回答。', 'Redis 热点怎么办？|按 Redis 的热点边界回答。', 'Redis 如何验证？|按 Redis 的验证路径回答。'],
        mistakes: ['不要把 Redis 的题目写成通用系统设计。'],
    });
    const rendered = renderCandidate({ root, spec: specPath, date: '2026-07-11' });
    const content = fs.readFileSync(path.join(root, rendered.candidate_path), 'utf8');
    assert.match(content, /Redis 候选的题目专属展开。/);
    assert.match(content, /Redis 候选的题目专属机制。/);
    assert.doesNotMatch(content, /先澄清规模、QPS、数据量、一致性、延迟和故障目标/);
    assert.doesNotMatch(content, /入口按容量预算接收流量，核心链路用分区\/缓存\/异步扩展/);
    fs.rmSync(root, { recursive: true, force: true });
});

test('curated tier audit reads formal answers without treating them as candidates', () => {
    const root = fixtureRoot();
    const answersDir = path.join(root, 'review', 'answers');
    ensureDir(answersDir);
    fs.writeFileSync(path.join(answersDir, 'cq_redis.md'), candidateContent().replace('"status":"draft"', '"status":"ready"').replace('"updated_at":"2026-07-11"', '"quality_tier":"curated","updated_at":"2026-07-11"'), 'utf8');
    const report = runAnswerAudit({ root, tier: 'curated', noWrite: true });
    assert.equal(report.candidate_count, 1);
    assert.equal(report.rows[0].quality_tier, 'curated');
    assert.equal(report.rows[0].errors.some((row) => row.error === 'invalid_candidate_tier'), false);
    fs.rmSync(root, { recursive: true, force: true });
});
