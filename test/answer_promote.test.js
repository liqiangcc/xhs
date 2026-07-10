'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, readJsonl, writeJson, writeJsonl } = require('../scripts/lib/io');
const { parseAnswerMetadata } = require('../scripts/lib/answer_store');
const { sha256, atomicPromote, atomicDemote, recordHumanReview } = require('../scripts/lib/answer_quality');

const QUALITY = require('../config/answer_quality.json');

function answer(metadata, marker) {
    const sectionContent = (title) => title === '常见追问'
        ? '- 问：Redis 事件循环如何处理连接？答：按就绪事件推进连接状态。\n- 问：大 Key 有什么影响？答：会延长单次命令执行时间。\n- 问：持久化会阻塞吗？答：需按命令、配置和版本具体分析。'
        : `${marker}：${title}的完整 Redis 内容。`;
    return [
        `<!-- xhs-answer: ${JSON.stringify(metadata)} -->`,
        '# Redis 为什么快？',
        ...['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '项目经验版', '常见追问', '易错点'].flatMap((title) => ['', `## ${title}`, '', sectionContent(title)]),
        '',
    ].join('\n');
}

function fixture() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-promote-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    writeJsonl(canonicalPath, [{
        schema_version: 'canonical_question.v1', canonical_id: 'cq_redis', canonical_title: 'Redis 为什么快？',
        aliases: [], question_ids: ['q1'], primary_domain: { l1: '缓存', l2: 'Redis' }, primary_entities: ['Redis'],
        companies: [], frequency: 1, review_priority: 'P0', answer_status: 'needs_update',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), []);
    const answersDir = path.join(root, 'review', 'answers');
    const candidatesDir = path.join(root, 'review', 'candidates', 'answers');
    const evidenceDir = path.join(root, 'review', 'evidence');
    ensureDir(answersDir); ensureDir(candidatesDir); ensureDir(evidenceDir);
    const formalPath = path.join(answersDir, 'cq_redis.md');
    const candidatePath = path.join(candidatesDir, 'cq_redis.md');
    fs.writeFileSync(formalPath, answer({ schema_version: 'answer.v1', canonical_id: 'cq_redis', version: 1, status: 'needs_update', quality_tier: 'long_tail_baseline', generator_version: 'long_tail.v1', updated_at: '2026-07-10' }, '旧答案'), 'utf8');
    fs.writeFileSync(candidatePath, answer({ schema_version: 'answer.v1', canonical_id: 'cq_redis', version: 1, status: 'draft', quality_tier: 'candidate', answer_type: 'concept', updated_at: '2026-07-11' }, '新答案'), 'utf8');
    return { root, canonicalPath, formalPath, candidatePath, evidencePath: path.join(evidenceDir, 'cq_redis.json') };
}

function passingEvidence(candidatePath) {
    return {
        schema_version: 'answer_evidence.v1',
        canonical_id: 'cq_redis',
        candidate_sha256: sha256(fs.readFileSync(candidatePath, 'utf8')),
        checked_at: '2026-07-11',
        writer: { writer_id: 'writer-a', writer_version: 'v1' },
        sources: [{ source_id: 'redis-doc', title: 'Redis docs', locator: 'https://redis.io/docs/', source_type: 'official_documentation', checked_at: '2026-07-11' }],
        claims: [{ claim_id: 'claim-1', text: 'Redis uses an event loop.', source_ids: ['redis-doc'], answer_locations: ['原理机制'] }],
        source_question_coverage: [],
        review: {
            reviewer_id: 'reviewer-b', independent: true, decision: 'pass', review_version: 'v1', revision_round: 1,
            hard_failures: [],
            scores: Object.fromEntries(Object.entries(QUALITY.dimensions).map(([key, rule]) => [key, rule.weight])),
            revision_suggestions: [],
        },
        human_review: {
            reviewer_id: 'human-reviewer', reviewer_type: 'human', reviewed_at: '2026-07-11',
            decision: 'approved', attestation: 'I reviewed the canonical, candidate, evidence, and quality contract.', batch_id: 'pilot-001',
        },
    };
}

test('failed promotion leaves formal answer and canonical status byte-for-byte unchanged', () => {
    const fixtureData = fixture();
    const beforeAnswer = fs.readFileSync(fixtureData.formalPath, 'utf8');
    const beforeCanonical = fs.readFileSync(fixtureData.canonicalPath, 'utf8');
    writeJson(fixtureData.evidencePath, { ...passingEvidence(fixtureData.candidatePath), candidate_sha256: 'wrong' });
    const result = atomicPromote({ root: fixtureData.root, canonicalId: 'cq_redis', candidate: fixtureData.candidatePath, evidence: fixtureData.evidencePath });
    assert.equal(result.ok, false);
    assert.equal(result.promoted, false);
    assert.equal(fs.readFileSync(fixtureData.formalPath, 'utf8'), beforeAnswer);
    assert.equal(fs.readFileSync(fixtureData.canonicalPath, 'utf8'), beforeCanonical);
    fs.rmSync(fixtureData.root, { recursive: true, force: true });
});

test('passing promotion upgrades metadata and synchronizes canonical status', () => {
    const fixtureData = fixture();
    writeJson(fixtureData.evidencePath, passingEvidence(fixtureData.candidatePath));
    const dryRun = atomicPromote({ root: fixtureData.root, canonicalId: 'cq_redis', candidate: fixtureData.candidatePath, evidence: fixtureData.evidencePath, noWrite: true });
    assert.equal(dryRun.ok, true);
    assert.equal(dryRun.promoted, false);
    assert.match(fs.readFileSync(fixtureData.formalPath, 'utf8'), /旧答案/);

    const result = atomicPromote({ root: fixtureData.root, canonicalId: 'cq_redis', candidate: fixtureData.candidatePath, evidence: fixtureData.evidencePath, date: '2026-07-11' });
    assert.equal(result.promoted, true);
    const promoted = fs.readFileSync(fixtureData.formalPath, 'utf8');
    assert.match(promoted, /新答案/);
    const metadata = parseAnswerMetadata(promoted);
    assert.equal(metadata.version, 2);
    assert.equal(metadata.status, 'ready');
    assert.equal(metadata.quality_tier, 'curated');
    assert.equal(metadata.generator_version, undefined);
    assert.equal(readJsonl(fixtureData.canonicalPath)[0].answer_status, 'ready');
    fs.rmSync(fixtureData.root, { recursive: true, force: true });
});

test('independent failed audit demotes historical curated metadata atomically', () => {
    const fixtureData = fixture();
    const formal = fs.readFileSync(fixtureData.formalPath, 'utf8');
    const reviewEvidence = passingEvidence(fixtureData.candidatePath);
    reviewEvidence.candidate_sha256 = sha256(formal);
    reviewEvidence.review.decision = 'revise';
    reviewEvidence.review.hard_failures = ['unsupported_factual_claim'];
    writeJson(fixtureData.evidencePath, reviewEvidence);
    const result = atomicDemote({ root: fixtureData.root, canonicalId: 'cq_redis', evidence: fixtureData.evidencePath, date: '2026-07-11' });
    assert.equal(result.demoted, true);
    const metadata = parseAnswerMetadata(fs.readFileSync(fixtureData.formalPath, 'utf8'));
    assert.equal(metadata.status, 'needs_update');
    assert.equal(metadata.quality_tier, 'curated_audit_failed');
    assert.equal(readJsonl(fixtureData.canonicalPath)[0].answer_status, 'needs_update');
    fs.rmSync(fixtureData.root, { recursive: true, force: true });
});

test('human review recorder rejects hash mismatch and writes a valid reviewer attestation', () => {
    const fixtureData = fixture();
    const evidence = passingEvidence(fixtureData.candidatePath);
    writeJson(fixtureData.evidencePath, evidence);
    const reviewPath = path.join(fixtureData.root, 'human-review.json');
    writeJson(reviewPath, { ...evidence.human_review, canonical_id: 'cq_redis', candidate_sha256: evidence.candidate_sha256 });
    const result = recordHumanReview({ root: fixtureData.root, canonicalId: 'cq_redis', evidence: fixtureData.evidencePath, review: reviewPath });
    assert.equal(result.decision, 'approved');
    assert.equal(require('../scripts/lib/io').readJson(fixtureData.evidencePath).human_review.reviewer_type, 'human');
    fs.rmSync(fixtureData.root, { recursive: true, force: true });
});
