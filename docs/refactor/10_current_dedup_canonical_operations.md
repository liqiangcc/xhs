# 10 Current Dedup / Canonical Operations

> 本文是当前 Canonical 候选发现、显式审核和应用流程的**当前操作 SSOT**。业务目标与内容完成标准仍以 `08_content_building_goals.md` 为准；legacy 退役边界见 `09_legacy_canonical_accept_boundary.md`。

## 1. 当前唯一新增关系流程

```text
Question / Index facts
  ↓
Dedup Detect
  ↓
RelationCandidate
  ↓
explicit RelationDecision
  ↓
ApplyDecision
  ↓
Canonical planning
  ↓
MutationPlan
  ↓
preflight / commit / post-commit validation
```

对应 CLI：

```bash
# Detect
node scripts/xhs.js canonical suggest --hotspot --limit 50
node scripts/xhs.js canonical suggest --entity Redis --limit 50

# Decide
node scripts/xhs.js dedup decide \
  --relation-candidate-key '<key>' \
  --relation same \
  --actor-type human \
  --actor-id '<reviewer-id>' \
  --rationale '<reason>'

# Apply same / alias
node scripts/xhs.js dedup apply \
  --relation-candidate-key '<key>' \
  --canonical-id <cq_id> \
  --canonical-title '<title>'
```

`parent_child`、`followup`、`related` 当前只记录 relation；`unrelated` 是显式 no-op。Interface 不自行决定这些业务语义。

## 2. Suggest 输出

Entity / Hotspot Suggest 都写入：

```text
data/manifests/dedup/relation_candidate_queues.json
```

队列对象是 `dedup_relation_candidate.v1`，只是待审核事实，不是 mutation authorization。

禁止：

```text
RelationCandidate → canonical_id
Similarity score  → Canonical mutation
Suggest            → direct mutation
AI suggestion      → implicit Decision
```

## 3. Detect / Decide / Apply 责任边界

### Detect

负责：

- 召回候选；
- similarity / same-question-id 等 evidence；
- 生成 RelationCandidate。

不负责：

- 决定正式 relation；
- 生成 Canonical ID；
- 修改 Canonical。

### Decide

`dedup decide`：

- 要求显式 actor；
- 重新验证 source freshness；
- DecisionStore 做 CAS；
- 产生可审计 `RelationDecision`。

### Apply

`dedup apply`：

- 重新加载 persisted Decision；
- 再验证 freshness；
- 生成 fresh `RelationApplyIntent`；
- 调用 Canonical planning / mutation；
- 执行 `preflight → commit → post-commit validation`。

Interface 不得注入 snapshot、revision、MutationPlan 或 commit evidence。

## 4. 已有 Canonical 的维护

```bash
node scripts/xhs.js canonical merge \
  --target <cq_id> \
  --source <cq_id> \
  --reason '<reason>'

node scripts/xhs.js canonical split \
  --canonical-id <cq_id> \
  --question-id <qid> \
  --new-canonical-id <cq_id> \
  --title '<title>'

node scripts/xhs.js canonical list --priority P0 --answer-status missing
node scripts/xhs.js canonical check
node scripts/xhs.js canonical stats
```

`merge/split` 只维护**已经存在的 Canonical 正式状态**，不能代替 Detect/Decide。

## 5. Legacy `canonical accept`

Legacy `canonical accept` 已在仓库内完全退役。

已删除：

```text
CLI / Presenter / help
Production canonical.accept capability
Accept Application
Legacy Candidate Repository / FS adapter / aliases
canonical-candidate:<id> Filesystem CAS
MutationPlan operation=accept
candidate-specific in-memory test support
legacyCandidateManifest / candidateManifest paths
checked-in canonical_candidates.json
```

当前不存在任何 repository-local runtime、contract、test-support、path 或 data manifest 能重新执行 `canonical_candidates.v1` 流程。

新 Suggest、GitHub Actions、Agent 和人工操作必须继续使用：

```text
Suggest → explicit Decide → Apply
```

历史 ADR / review plan 中的旧术语仅作为历史证据。

## 6. GitHub Actions

`xhs-manage.yml` 中：

```text
canonical-suggest-hotspot
canonical-suggest-entity
```

发布：

```text
data/manifests/dedup/relation_candidate_queues.json
artifact: dedup-relation-candidates
```

`create_pr=true` 时也只提交 review queue。Actions 不自动执行 `dedup decide` 或 `dedup apply`。

## 7. 内容建设批次

`08_content_building_goals.md` 中的 Canonical 推进按以下方式解释：

```text
候选召回
  ↓
canonical suggest
  ↓
人工 / AI 辅助审核 evidence
  ↓
dedup decide
  ↓
dedup apply（same / alias）
  或 canonical merge / split（维护已有 Canonical）
  ↓
answer validate / sync
  ↓
canonical check
```

## 8. Agent 规则

Agent 必须遵守：

1. 不手工编辑 `canonical_id` 绕过 Application；
2. 不根据 similarity 自动决定 `same`；
3. 新增/吸收关系走 Suggest → Decide → Apply；
4. 已有 Canonical 合并/拆分走 Merge/Split；
5. 正式写入前保留 explicit review、freshness、CAS；
6. 不恢复任何 legacy Accept runtime/data path。

## 9. 文档优先级

```text
10_current_dedup_canonical_operations.md   ← 当前操作 SSOT
09_legacy_canonical_accept_boundary.md     ← legacy 退役边界 / 防回归
08_content_building_goals.md               ← 内容目标与 DoD
06_github_actions_ai_management.md         ← Actions 管理规范
历史 ADR / review plans                    ← 历史证据
```

## 10. 验证

涉及该流程的修改至少运行：

```bash
node --test
npm run ci:check
```

并确认：

```text
Suggest 使用 relation_candidate_queues.json
RelationCandidate 需要 explicit Decision
stale source 在 Decision / Apply 前 fail-closed
MutationStore preflight/commit CAS 生效
Canonical post-commit invariants 通过
GitHub Actions artifact = dedup-relation-candidates
legacy canonical accept 不存在可执行/contract/test/path/data 回流
```
