# 10 Current Dedup / Canonical Operations

> 本文是当前 Canonical 候选发现、人工审核和应用流程的**操作 SSOT**。业务目标与内容完成标准仍以 `08_content_building_goals.md` 为准；legacy 兼容边界见 `09_legacy_canonical_accept_boundary.md`。

## 1. 当前正式流程

新候选不得再走 `canonical_candidates.v1 -> canonical accept` 快捷路径。

当前唯一正式的新增关系流程是：

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
# 1. 发现待审核关系
node scripts/xhs.js canonical suggest --hotspot --limit 50
node scripts/xhs.js canonical suggest --entity Redis --limit 50

# 2. 显式审核
node scripts/xhs.js dedup decide \
  --relation-candidate-key '<key>' \
  --relation same \
  --actor-type human \
  --actor-id '<reviewer-id>' \
  --rationale '<reason>'

# 3. 对 same / alias 应用到目标 Canonical
node scripts/xhs.js dedup apply \
  --relation-candidate-key '<key>' \
  --canonical-id <cq_id> \
  --canonical-title '<title>'
```

`parent_child`、`followup`、`related` 当前是 relation-record-only；`unrelated` 是显式 no-op。CLI 不自行决定这些业务语义，最终策略由 Domain/Application 决定。

## 2. Suggest 输出

Entity 和 Hotspot Suggest 都写入同一 Review Queue：

```text
data/manifests/dedup/relation_candidate_queues.json
```

队列中的对象是 `dedup_relation_candidate.v1`，它只是待审核事实，不是 Canonical mutation authorization。

禁止：

```text
RelationCandidate -> canonical_id
Similarity score  -> Canonical mutation
Suggest            -> canonical_candidates.v1
Suggest            -> direct Accept
```

## 3. Detect / Decide / Apply 边界

### Detect

负责发现信号和候选关系：

- Entity：归一化实体召回 + similarity / same-question-id evidence；
- Hotspot：基于 hotspot index 的重复 question_id facts；
- 不生成 Canonical ID；
- 不做正式 relation 决策；
- 不写 Canonical。

### Decide

`dedup decide` 调用 `app.dedup.recordDecision()`：

- 必须有 explicit actor；
- 重新验证 source freshness；
- DecisionStore 再做 CAS；
- 结果是可审计 `RelationDecision`，不是 Apply command。

### Apply

`dedup apply` 调用 `app.dedup.applyDecision()`：

- 重新加载 persisted Decision；
- 再次验证 source freshness；
- 生成 fresh `RelationApplyIntent`；
- Canonical Application 解析 create / extend；
- 构造 `canonical_mutation_plan.v1`；
- `preflight -> commit -> post-commit validation`。

Interface 不得注入 snapshot、revision、MutationPlan 或 commit evidence。

## 4. Canonical 维护命令

已经存在的正式 Canonical 维护继续使用独立用例：

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

node scripts/xhs.js canonical check
node scripts/xhs.js canonical stats
```

`merge/split` 是对**已经存在的 Canonical 正式状态**进行维护；它们不是 Detect/Decide 的替代品。

## 5. Legacy `canonical accept`

`canonical accept` CLI、Production `canonical.accept` capability、旧 Accept Application、Legacy Candidate Repository 层、`canonical-candidate:<id>` Filesystem CAS revision bridge、MutationPlan `operation=accept`，以及 candidate-specific in-memory test support 都已移除。

当前 `src/` 中没有运行时代码、MutationPlan contract 或共享测试 adapter 能表达/读取 legacy canonical candidate。仅剩最后一层不可执行残余：

```text
legacyCandidateManifest / candidateManifest path
empty checked-in canonical_candidates.json
```

它们只是待删除的路径名与空历史数据，不能形成任何 Canonical mutation。下一阶段完成最终 path/data cleanup 后，legacy `canonical accept` 退役即可收口。

新 Suggest、GitHub Actions、Agent 或日常人工操作不得生成新的 `canonical_candidates.v1`，也不得绕过 RelationCandidate / RelationDecision / ApplyDecision 边界。

正常工作中看到 `candidate_id` 时先确认它是否属于其它 review 模型；当前 Dedup review identity 是 `relation_candidate_key`，两者不是同一个概念。

## 6. GitHub Actions

`xhs-manage.yml` 中：

```text
canonical-suggest-hotspot
canonical-suggest-entity
```

现在生成并发布：

```text
data/manifests/dedup/relation_candidate_queues.json
artifact: dedup-relation-candidates
```

`create_pr=true` 时，PR 也只提交这个 review queue 文件。

Actions 生成 RelationCandidate **不等于审核通过**。生成队列后仍必须有显式 `dedup decide`，之后才能 `dedup apply`。

当前 Actions 不自动执行 `dedup decide` 或 `dedup apply`，因此生成任务本身没有 Canonical mutation 权限。

## 7. 内容建设批次如何使用

`08_content_building_goals.md` 中“候选召回 -> 去重与边界确认 -> Canonical 推进”的当前执行解释是：

```text
候选召回
  ↓
canonical suggest
  ↓
人工 / AI 辅助审核证据
  ↓
dedup decide
  ↓
dedup apply（same / alias）
  或 canonical merge / split（维护已有 Canonical）
  ↓
answer validate / sync
  ↓
canonical check
  ↓
加入复习队列
```

不要把旧文档中的 `canonical accept` 当成新候选的默认步骤。

## 8. Agent 规则

Agent 在发现 Canonical 边界问题时：

1. 不手工编辑 `canonical_id` 绕过 Application；
2. 不制造 `canonical_candidates.v1`；
3. 不根据 similarity score 自动决定 `same`；
4. 需要新增/吸收关系时使用 Suggest -> Decide -> Apply；
5. 已有 Canonical 之间需要正式合并/拆分时使用 Merge/Split；
6. 在正式写入前保留 explicit review、freshness 和 CAS 边界。

## 9. 文档优先级

关于 Canonical/Dedup **当前命令和操作方式**，优先级如下：

```text
10_current_dedup_canonical_operations.md   ← 当前操作 SSOT
09_legacy_canonical_accept_boundary.md     ← legacy compatibility / removal rules
08_content_building_goals.md               ← 内容目标与 DoD，不作为命令 SSOT
06_github_actions_ai_management.md         ← Actions 演进记录；历史段落可能保留旧术语
历史 ADR / review plans                    ← 历史证据，不作为当前操作说明
```

若历史文档与本文的操作路径冲突，以本文和当前代码/测试为准。

## 10. 验证

涉及该流程的修改至少运行：

```bash
node --test
npm run ci:check
```

并确认：

```text
Suggest 不生成 canonical_candidates.json
RelationCandidate 需要 explicit Decision
stale source 在 Decision / Apply 前 fail-closed
MutationStore preflight/commit CAS 生效
Canonical post-commit invariants 通过
GitHub Actions artifact 指向 relation_candidate_queues.json
canonical accept 不再由 CLI 暴露
Production Root 不暴露 canonical.accept
Accept Application 文件不存在
Legacy Candidate Repository 层不存在
canonical-candidate:* Filesystem CAS revision routing 不存在
MutationPlan 不支持 operation=accept
in-memory Canonical adapter 不包含 legacy candidate test support
```