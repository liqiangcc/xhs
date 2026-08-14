'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');

function read(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8');
}

test('current human-facing docs route new Canonical relations through explicit Dedup review', () => {
    const readme = read('README.md');
    const operations = read('docs/refactor/10_current_dedup_canonical_operations.md');
    const actions = read('docs/refactor/06_github_actions_ai_management.md');

    for (const body of [readme, operations]) {
        assert.match(body, /canonical suggest/);
        assert.match(body, /dedup decide/);
        assert.match(body, /dedup apply/);
        assert.match(body, /relation_candidate_queues\.json/);
    }

    assert.match(readme, /operational SSOT/);
    assert.match(operations, /当前操作 SSOT/);
    assert.match(actions, /10_current_dedup_canonical_operations\.md/);
    assert.match(actions, /dedup-relation-candidates/);

    for (const stale of [
        /canonical suggest` always writes its business output to `data\/manifests\/canonical\/canonical_candidates\.json/,
        /当前该任务上传 `canonical-candidates` artifact/,
        /Action 生成 canonical_candidates manifest/,
        /人工确认 accept \/ merge \/ split/,
    ]) {
        assert.doesNotMatch(readme, stale);
        assert.doesNotMatch(actions, stale);
    }
});

test('repository and skill guidance cannot route new work through legacy canonical accept', () => {
    const agents = read('AGENTS.md');
    const skill = read('.agents/skills/xhs-answer-curator/SKILL.md');
    const repoMap = read('.agents/skills/xhs-answer-curator/references/repo-map.md');

    for (const body of [agents, skill, repoMap]) {
        assert.match(body, /canonical suggest/);
        assert.match(body, /dedup decide/);
        assert.match(body, /dedup apply/);
        assert.match(body, /canonical_candidates\.v1/);
        assert.match(body, /legacy/i);
    }

    assert.match(agents, /Do not create `canonical_candidates\.v1`/);
    assert.match(skill, /never create a new `canonical_candidates\.v1` manifest/);
    assert.match(repoMap, /Do not create `canonical_candidates\.v1` for new work/);
});

test('GitHub Actions publishes review queues rather than executable legacy candidate manifests', () => {
    const workflow = read('.github/workflows/xhs-manage.yml');

    assert.match(workflow, /data\/manifests\/dedup\/relation_candidate_queues\.json/);
    assert.match(workflow, /name:\s*dedup-relation-candidates/);
    assert.doesNotMatch(workflow, /data\/manifests\/canonical\/canonical_candidates\.json/);
    assert.doesNotMatch(workflow, /name:\s*canonical-candidates/);
});
