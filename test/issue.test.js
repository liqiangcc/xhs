'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { ensureDir, readJson, writeJson, writeJsonl } = require('../scripts/lib/io');
const { runRender, runSync, runCheck } = require('../scripts/commands/issue');

function canonical(canonicalId, status = 'ready') {
    return {
        canonical_id: canonicalId,
        canonical_title: 'Redis为什么快',
        aliases: ['Redis为什么快'],
        question_ids: ['95ffbd750b81df63a427ad0d630a6b1d'],
        primary_domain: { l1: '缓存', l2: 'Redis' },
        primary_entities: ['Redis'],
        companies: ['字节', '快手'],
        frequency: 4,
        review_priority: 'P0',
        answer_status: status,
        schema_version: 'canonical_question.v1',
    };
}

function writeReadyAnswer(root, canonicalId) {
    const answersDir = path.join(root, 'review', 'answers');
    ensureDir(answersDir);
    fs.writeFileSync(
        path.join(answersDir, `${canonicalId}.md`),
        [
            `<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"${canonicalId}","version":1,"status":"ready","updated_at":"2026-06-30"} -->`,
            '# Redis为什么快',
            '',
            '## 核心结论',
            '',
            'Redis 快主要因为内存存储、单线程事件循环、IO 多路复用和紧凑的数据结构。',
            '',
            '## 关键细节',
            '',
            '- 纯内存读写避免磁盘随机 IO。',
            '- 单线程执行命令避免锁竞争。',
            '- epoll 等 IO 多路复用提升连接处理效率。',
            '',
            '## 常见追问',
            '',
            '- Redis 单线程为什么还能支撑高并发？',
            '- Redis 6 之后多线程主要解决什么问题？',
            '',
        ].join('\n'),
        'utf8'
    );
}

function writeProgress(root, canonicalId, status = 'new') {
    writeJson(path.join(root, 'review', 'progress.json'), {
        schema_version: 'review_progress_store.v1',
        updated_at: '2026-06-30',
        items: [
            {
                canonical_id: canonicalId,
                status,
                level: status === 'weak' ? 0 : 1,
                review_count: status === 'new' ? 0 : 1,
                last_reviewed_at: status === 'new' ? null : '2026-06-30',
                next_review_at: '2026-06-30',
                confidence: status === 'weak' ? 0.3 : 0.5,
                difficulty: status === 'weak' ? 4 : 3,
                mistake_count: status === 'weak' ? 1 : 0,
                updated_at: '2026-06-30',
            },
        ],
    });
}

test('renders a mobile issue card from answer markdown', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-render-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    writeReadyAnswer(root, 'cq_redis_fast');

    const rendered = runRender({ root, 'canonical-id': 'cq_redis_fast', repo: 'liqiangcc/xhs' });
    assert.equal(rendered.ok, true);
    assert.equal(rendered.title, '[Review][P0] cq_redis_fast Redis为什么快');
    assert.deepEqual(rendered.labels, ['review', 'priority:P0', 'answer:ready', 'domain:缓存', 'review:new']);
    assert.match(rendered.body, /1 分钟结论/);
    assert.match(rendered.body, /单线程事件循环/);
    assert.match(rendered.body, /https:\/\/github.com\/liqiangcc\/xhs\/blob\/master\/review\/answers\/cq_redis_fast.md/);
    assert.equal(typeof rendered.body_hash, 'string');

    fs.rmSync(root, { recursive: true, force: true });
});

test('dry-run sync does not call GitHub or write issue links', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-dry-run-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    writeReadyAnswer(root, 'cq_redis_fast');
    let called = false;

    const result = runSync({ root, 'canonical-id': 'cq_redis_fast', repo: 'liqiangcc/xhs' }, {
        runner: () => {
            called = true;
            return '';
        },
    });

    assert.equal(result.ok, true);
    assert.equal(result.applied, false);
    assert.equal(result.rows[0].action, 'create');
    assert.equal(called, false);
    assert.equal(fs.existsSync(path.join(root, 'review', 'issue_links.json')), false);

    fs.rmSync(root, { recursive: true, force: true });
});

test('apply sync creates a GitHub issue through the runner and records the link', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-apply-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    writeReadyAnswer(root, 'cq_redis_fast');
    const calls = [];
    const runner = (args) => {
        calls.push(args);
        if (args[0] === 'issue' && args[1] === 'create') {
            return 'https://github.com/liqiangcc/xhs/issues/12';
        }
        return '';
    };

    const result = runSync({
        root,
        'canonical-id': 'cq_redis_fast',
        repo: 'liqiangcc/xhs',
        apply: true,
        date: '2026-06-30',
    }, { runner });

    assert.equal(result.ok, true);
    assert.equal(result.synced_count, 1);
    assert.equal(calls.filter((args) => args[0] === 'label' && args[1] === 'create').length, 5);
    assert.equal(calls.some((args) => args[0] === 'issue' && args[1] === 'create'), true);
    const links = readJson(path.join(root, 'review', 'issue_links.json'));
    assert.equal(links.items[0].canonical_id, 'cq_redis_fast');
    assert.equal(links.items[0].issue_number, 12);
    assert.equal(links.items[0].issue_url, 'https://github.com/liqiangcc/xhs/issues/12');
    assert.equal(links.items[0].review_status, 'new');
    assert.deepEqual(links.items[0].labels, ['review', 'priority:P0', 'answer:ready', 'domain:缓存', 'review:new']);
    assert.equal(runCheck({ root }).ok, true);

    fs.rmSync(root, { recursive: true, force: true });
});

test('apply sync updates managed labels and keeps unrelated labels intact', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-update-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    writeReadyAnswer(root, 'cq_redis_fast');
    writeProgress(root, 'cq_redis_fast', 'weak');
    writeJson(path.join(root, 'review', 'issue_links.json'), {
        schema_version: 'review_issue_links.v1',
        updated_at: '2026-06-30',
        items: [
            {
                canonical_id: 'cq_redis_fast',
                issue_number: 12,
                issue_url: 'https://github.com/liqiangcc/xhs/issues/12',
                answer_status: 'draft',
                review_status: 'new',
                labels: ['review', 'priority:P1', 'answer:draft', 'domain:数据库', 'review:new'],
                body_hash: 'old-hash',
            },
        ],
    });
    const calls = [];
    const runner = (args) => {
        calls.push(args);
        if (args[0] === 'issue' && args[1] === 'view') {
            return JSON.stringify({
                labels: [
                    { name: 'review' },
                    { name: 'priority:P1' },
                    { name: 'answer:draft' },
                    { name: 'domain:数据库' },
                    { name: 'review:new' },
                    { name: 'custom:keep' },
                ],
            });
        }
        return '';
    };

    const result = runSync({
        root,
        'canonical-id': 'cq_redis_fast',
        repo: 'liqiangcc/xhs',
        apply: true,
        date: '2026-06-30',
    }, { runner });

    assert.equal(result.ok, true);
    assert.equal(result.rows[0].action, 'update');
    const edit = calls.find((args) => args[0] === 'issue' && args[1] === 'edit');
    assert.ok(edit);
    assert.equal(edit.includes('custom:keep'), false);
    assert.equal(edit.includes('priority:P1'), true);
    assert.equal(edit.includes('answer:draft'), true);
    assert.equal(edit.includes('domain:数据库'), true);
    assert.equal(edit.includes('review:new'), true);
    assert.equal(edit.includes('priority:P0'), true);
    assert.equal(edit.includes('answer:ready'), true);
    assert.equal(edit.includes('domain:缓存'), true);
    assert.equal(edit.includes('review:weak'), true);
    const links = readJson(path.join(root, 'review', 'issue_links.json'));
    assert.equal(links.items[0].review_status, 'weak');
    assert.deepEqual(links.items[0].labels, ['review', 'priority:P0', 'answer:ready', 'domain:缓存', 'review:weak']);

    fs.rmSync(root, { recursive: true, force: true });
});

test('apply sync repairs label drift when body hash is unchanged', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-label-drift-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    writeReadyAnswer(root, 'cq_redis_fast');
    writeProgress(root, 'cq_redis_fast', 'weak');
    const dryRun = runSync({ root, 'canonical-id': 'cq_redis_fast', repo: 'liqiangcc/xhs' });
    writeJson(path.join(root, 'review', 'issue_links.json'), {
        schema_version: 'review_issue_links.v1',
        updated_at: '2026-06-30',
        items: [
            {
                canonical_id: 'cq_redis_fast',
                issue_number: 12,
                issue_url: 'https://github.com/liqiangcc/xhs/issues/12',
                answer_status: 'ready',
                review_status: 'weak',
                labels: dryRun.rows[0].labels,
                body_hash: dryRun.rows[0].body_hash,
            },
        ],
    });
    const calls = [];
    const runner = (args) => {
        calls.push(args);
        if (args[0] === 'issue' && args[1] === 'view') {
            return JSON.stringify({
                labels: [
                    { name: 'review' },
                    { name: 'priority:P0' },
                    { name: 'answer:ready' },
                    { name: 'domain:缓存' },
                    { name: 'review:new' },
                    { name: 'custom:keep' },
                ],
            });
        }
        return '';
    };

    const result = runSync({
        root,
        'canonical-id': 'cq_redis_fast',
        repo: 'liqiangcc/xhs',
        apply: true,
        date: '2026-06-30',
    }, { runner });

    assert.equal(result.ok, true);
    assert.equal(result.rows[0].action, 'sync_labels');
    assert.deepEqual(result.rows[0].labels_removed, ['review:new']);
    assert.deepEqual(result.rows[0].labels_added, ['review:weak']);
    const edit = calls.find((args) => args[0] === 'issue' && args[1] === 'edit');
    assert.ok(edit);
    assert.equal(edit.includes('--body-file'), false);
    assert.equal(edit.includes('custom:keep'), false);

    fs.rmSync(root, { recursive: true, force: true });
});

test('check reports invalid issue link mappings', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-check-'));
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [canonical('cq_redis_fast')]);
    writeJson(path.join(root, 'review', 'issue_links.json'), {
        schema_version: 'review_issue_links.v1',
        updated_at: '2026-06-30',
        items: [
            {
                canonical_id: 'cq_redis_fast',
                issue_number: 12,
                issue_url: 'https://github.com/liqiangcc/xhs/issues/12',
                body_hash: 'hash-a',
            },
            {
                canonical_id: 'cq_unknown',
                issue_number: 12,
                issue_url: 'https://github.com/liqiangcc/xhs/issues/12',
                body_hash: 'hash-b',
            },
        ],
    });

    const checked = runCheck({ root });
    assert.equal(checked.ok, false);
    assert.equal(checked.errors.some((error) => error.error === 'unknown_canonical_id'), true);
    assert.equal(checked.errors.some((error) => error.error === 'duplicate_issue_number'), true);

    fs.rmSync(root, { recursive: true, force: true });
});
