'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJson, writeJsonl } = require('../scripts/lib/io');
const { sha256 } = require('../scripts/lib/answer_quality');
const { queueStatus, closure, reachability, weeklySample, stability } = require('../scripts/lib/answer_completion');
const QUALITY = require('../config/answer_quality.json');

function answer(metadata, title = 'Redis 为什么快？') {
    return [
        `<!-- xhs-answer: ${JSON.stringify(metadata)} -->`, `# ${title}`, '',
        '## 核心结论', '', 'Redis 通过事件循环、内存数据结构和短命令路径降低典型请求的额外开销。', '',
        '## 1 分钟版', '', '先说明事件循环，再说明内存访问和命令复杂度，最后补充大 Key 边界。', '',
        '## 3 分钟版', '', '客户端连接由事件循环推进；命令执行根据具体数据结构产生对应复杂度。', '',
        '## 关键细节', '', '不同版本的网络 I/O 实现需要按官方文档核对。', '',
        '## 原理机制', '', '就绪事件驱动状态机从读取、解析、执行到写回。', '',
        '## 项目经验版', '', '没有真实经历时，只将这里作为项目映射提示，不虚构指标。', '',
        '## 常见追问', '',
        '- 问：大 Key 为什么影响延迟？答：单次命令工作量增加，会延长其他请求等待。',
        '- 问：Redis 是否所有任务都单线程？答：要按版本和具体后台任务区分。',
        '- 问：慢命令如何定位？答：结合慢日志、命令复杂度和数据规模检查。', '',
        '## 易错点', '', '不能把性能只归结为单线程，也不能把复杂度说成恒定。', '',
    ].join('\n');
}

function canonical(id, type = 'concept') {
    return { schema_version: 'canonical_question.v1', canonical_id: id, canonical_title: id === 'cq_redis' ? 'Redis 为什么快？' : `题目 ${id}`, aliases: [], question_ids: [`q_${id}`], primary_domain: { l1: '缓存', l2: 'Redis' }, primary_entities: ['Redis'], companies: [], frequency: 1, review_priority: 'P1', answer_status: 'ready', answer_type: type };
}

function question(id) {
    return { schema_version: 'question.v1', question_id: `q_${id}`, original_question: id === 'cq_redis' ? 'Redis 为什么快？' : `题目 ${id}`, canonical_id: id, is_valid_for_library: true };
}

function evidence(candidateContent, id) {
    return {
        schema_version: 'answer_evidence.v1', canonical_id: id, candidate_sha256: sha256(candidateContent), checked_at: '2026-07-11',
        writer: { writer_id: 'writer-a', writer_version: 'v1' },
        sources: [{ source_id: 'official', title: 'Official Redis docs', locator: 'https://redis.io/docs/', source_type: 'official_documentation', checked_at: '2026-07-11' }],
        claims: [{ claim_id: 'claim-1', text: 'Redis processes client events through an event loop.', source_ids: ['official'], answer_locations: ['原理机制'] }],
        source_question_coverage: [{ question_id: `q_${id}`, covered: true, answer_locations: ['核心结论'] }],
        review: { reviewer_id: 'reviewer-b', review_version: 'v1', independent: true, decision: 'pass', revision_round: 1, hard_failures: [], scores: Object.fromEntries(Object.entries(QUALITY.dimensions).map(([key, value]) => [key, value.weight])), revision_suggestions: [] },
    };
}

function fixture(one = true) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-completion-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    const ids = one ? ['cq_redis'] : Array.from({ length: 60 }, (_, index) => `cq_${String(index).padStart(2, '0')}`);
    const types = ['coding', 'mechanism', 'scenario', 'concept', 'project', 'behavior'];
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), ids.map((id, index) => canonical(id, types[Math.floor(index / 10)])));
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), ids.map(question));
    writeJsonl(path.join(root, 'data', 'manifests', 'quality', 'answer_type_audit.jsonl'), ids.map((id, index) => ({ canonical_id: id, answer_type: types[Math.floor(index / 10)] })));
    fs.mkdirSync(path.join(root, 'review', 'answers'), { recursive: true });
    for (const id of ids) {
        const candidate = answer({ schema_version: 'answer.v1', canonical_id: id, version: 1, status: 'draft', quality_tier: 'candidate', answer_type: 'concept', updated_at: '2026-07-11' }, id === 'cq_redis' ? 'Redis 为什么快？' : `题目 ${id}`);
        const formal = answer({ schema_version: 'answer.v1', canonical_id: id, version: 2, status: 'ready', quality_tier: 'curated', answer_type: 'concept', candidate_sha256: sha256(candidate), updated_at: '2026-07-11' }, id === 'cq_redis' ? 'Redis 为什么快？' : `题目 ${id}`);
        fs.writeFileSync(path.join(root, 'review', 'answers', `${id}.md`), formal, 'utf8');
        if (one) writeJson(path.join(root, 'review', 'evidence', `${id}.json`), evidence(candidate, id));
    }
    writeJson(path.join(root, 'review', 'progress.json'), { schema_version: 'review_progress_store.v1', updated_at: '2026-07-11', items: ids.map((id) => ({ canonical_id: id, status: 'learning', level: 1, review_count: 1, last_reviewed_at: '2026-07-11', next_review_at: '2026-07-12', confidence: 0.6, difficulty: 3, mistake_count: 0, updated_at: '2026-07-11' })) });
    return { root, ids };
}

test('closure and reachability accept a formal answer whose evidence binds the pre-promotion candidate hash', () => {
    const { root } = fixture();
    assert.equal(queueStatus({ root, type: 'concept', 'expect-empty': true }).ok, true);
    const completion = closure({ root, audit: true, full: true, noWrite: true });
    assert.equal(completion.ok, true);
    assert.equal(completion.rows[0].audit_passed, true);
    assert.equal(reachability({ root, full: true, noWrite: true }).ok, true);
    fs.rmSync(root, { recursive: true, force: true });
});

test('weekly stability requires four real sampled weeks, oral evidence, closed feedback and non-regressing snapshots', () => {
    const { root } = fixture(false);
    const weeks = ['2026-W01', '2026-W02', '2026-W03', '2026-W04'];
    const dates = ['2026-01-01', '2026-01-05', '2026-01-12', '2026-01-19'];
    const reports = [];
    for (const [index, week] of weeks.entries()) {
        const sample = weeklySample(week, { root });
        assert.equal(sample.ok, true);
        const session = { schema_version: 'review_session.v1', date: dates[index], events: sample.items.map((item) => ({ canonical_id: item.canonical_id, result: 'good', oral_version: 'one_minute', followup_answered: true, quality_defects: [] })) };
        writeJson(path.join(root, 'review', 'sessions', `${dates[index]}.json`), session);
        reports.push({ week, curated_ready_count: 60, hard_failure_count: 0, reviewed_count: 60, generated_at: dates[index] });
    }
    writeJson(path.join(root, 'data', 'manifests', 'quality', 'weekly_answer_quality.json'), { schema_version: 'weekly_answer_quality.v1', weeks: reports });
    assert.equal(stability({ root, weeks: 4, week: '2026-W04', 'require-zero-hard-fail': true, 'require-no-regression': true, noWrite: true }).ok, true);
    fs.rmSync(root, { recursive: true, force: true });
});
