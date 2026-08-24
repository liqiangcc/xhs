# 10 Current Dedup / Canonical Operations

> 本文是当前 Canonical 候选发现、显式审核和应用流程的**当前操作 SSOT**。业务目标与内容完成标准仍以 `08_content_building_goals.md` 为准；legacy 退役边界见 `09_legacy_canonical_accept_boundary.md`。

## 1. 当前唯一新增关系流程

```text
Question / Index facts
  ↓
Dedup Detect / Explicit Pair Selection
  ↓
RelationCandidate
  ↓
explicit RelationDecision
  ↓
ApplyDecision
  ↓
current ownership resolution
  ↓
Canonical planning / reviewed Canonical consolidation
  ↓
MutationPlan
  ↓
preflight / commit / post-commit validation
```

对应 CLI：

```bash
# Discover duplicate-like candidates among unassigned Questions
node scripts/xhs.js canonical suggest --hotspot --limit 50
node scripts/xhs.js canonical suggest --entity Redis --limit 50

# Select exactly two current Questions for a bounded source-first relation review.
# This works even when the Questions are already canonicalized and performs no
# similarity-based relation inference.
node scripts/xhs.js canonical suggest --question-ids '<qid1>,<qid2>'

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

Entity / Hotspot / Explicit Pair Suggest 都写入：

```text
data/manifests/dedup/relation_candidate_queues.json
```

队列对象中的候选是 `dedup_relation_candidate.v1`，只是待审核事实，不是 mutation authorization。

三种入口的边界不同：

- `--entity` / `--hotspot` 是发现模式，只召回当前 valid 且尚未绑定 Canonical 的 Question；
- `--question-ids q1,q2` 是显式选择模式，只用于已经由 source-first 审查明确要求比较的两个当前 Question；它允许 Question 已绑定 Canonical；
- Explicit Pair 的 evidence 只记录 `explicit_review_selection` 与 `relation_inference=none`，不得把“被选中比较”解释为 `same`、`alias` 或任何其他正式 relation。

禁止：

```text
RelationCandidate → canonical_id
Similarity score  → Canonical mutation
Explicit selection → semantic relation
Suggest            → direct mutation
AI suggestion      → implicit Decision
```

## 3. Detect / Decide / Apply 责任边界

### Detect / Select

负责：

- Entity / Hotspot：召回 duplicate-like 候选并记录 similarity / same-question-id 等 evidence；
- Explicit Pair：按两个 `question_id` 读取当前 Question facts，验证两者都存在且可进入 library，并记录“需要人工/AI 显式判断”的选择 evidence；
- 生成 RelationCandidate；
- 把 source revisions 冻结到 queue，供 Decide / Apply 再校验。

不负责：

- 决定正式 relation；
- 生成 Canonical ID；
- 修改 Canonical；
- 因为 Explicit Pair 被选中就推断语义关系。

### Decide

`dedup decide`：

- 要求显式 actor；
- 重新验证 source freshness；
- DecisionStore 做 CAS；
- 产生可审计 `RelationDecision`。

Explicit Pair 的 source revision 只覆盖被选择的 Question snapshot；任一被选择 Question 在 Suggest 之后变化，Decision 必须 fail-closed 并重新 Suggest。

### Apply

`dedup apply`：

- 重新加载 persisted Decision；
- 再验证 freshness；
- 生成 fresh `RelationApplyIntent`；
- 从 Port 重新读取当前 Question→Canonical ownership，Interface 不能提供或覆盖 source Canonical；
- 若 `same/alias` 的 reviewed Questions 没有其它 Canonical owner，走普通 Question-group Canonical planning；
- 若 `same/alias` 跨越一个已有 source Canonical，并且该 source Canonical 的**全部 Question 都在当前已审核 RelationCandidate 内**，Application 才可把 source Canonical 合并进指定 target Canonical；
- Canonical consolidation 复用正式 Merge transaction，因此同步迁移 ReviewProgress/session、归档 source Answer、使 target Answer 失效、重建索引并执行完整 post-commit integrity；
- 若一个 Question 多 owner、跨多个非 target Canonical、target 不存在，或 source Canonical 含任何未审核 Question，Apply 必须 fail-closed；需要扩大 source-first review，不能顺手移动未审核内容；
- 执行 `preflight → commit → post-commit validation`。

Interface 不得注入 snapshot、revision、source Canonical、ApplyStrategy、MutationPlan 或 commit evidence。

这意味着：

```text
Explicit Pair + same/alias Decision
  ↓
Application reloads current ownership
  ├─ no external owner → Question-group canonicalization
  └─ one fully-reviewed source Canonical → reviewed Canonical consolidation
       └─ source contains unreviewed member → FAIL CLOSED
```

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

`merge/split` 只维护**已经存在的 Canonical 正式状态**，不能代替 Detect/Select → Decide。若 source-first 内容审查要求先形成新的关系结论，即使两边已经有 Canonical，也必须先用 Explicit Pair 产生 fresh RelationCandidate，再显式 Decide / Apply；不能用 `canonical merge` 绕过关系审核。

当显式 `same/alias` Decision 证明两个已存在 Canonical 需要收敛时，`dedup apply` 会在 Application 内根据**当前 ownership**选择 reviewed consolidation，并调用与 `canonical merge` 相同的正式事务能力；caller 仍然只能指定 target，不能指定 source，也不能让未进入本次 review 的 source members 被连带迁移。

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
Suggest / Select → explicit Decide → Apply
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

Explicit Pair 是有明确 source-first 边界结论后的 bounded remediation 操作；当前通过 CLI / 受审查的批次 workflow 调用，不开放“批量自动配对”入口。任何批次 workflow 也只能先 Select，再以明确 rationale 执行 Decide / Apply，不能把选择步骤当成 relation authorization。

## 7. 内容建设批次

`08_content_building_goals.md` 中的 Canonical 推进按以下方式解释：

```text
候选召回 / source-first 指定关系对
  ↓
canonical suggest
  ↓
人工 / AI 辅助审核 source facts + evidence
  ↓
dedup decide
  ↓
dedup apply（same / alias；必要时内部执行 reviewed Canonical consolidation）
  或 relation-only apply（related / parent_child / followup / unrelated）
  或 canonical merge / split（仅维护已有正式 Canonical，不能绕过新增关系审核）
  ↓
answer validate / sync
  ↓
canonical check
```

当内容批次已经确认“两个已绑定 Canonical 的 Question 必须重新做当前关系判断”时，使用：

```bash
node scripts/xhs.js canonical suggest --question-ids '<qid1>,<qid2>'
```

随后仍必须完成 explicit Decision；不得因为历史 Canonical 状态、旧 review 记录或 similarity 结果直接应用关系。若 Decision 为 `same/alias` 且两题属于不同 Canonical，`dedup apply` 只能在 source Canonical 的全部成员都已被本次 review 覆盖时收敛 Canonical，否则 fail-closed。

## 8. Agent 规则

Agent 必须遵守：

1. 不手工编辑 `canonical_id` 绕过 Application；
2. 不根据 similarity 自动决定 `same`；
3. 新增/吸收关系走 Suggest/Select → Decide → Apply；
4. 已有 Canonical 之间若 source-first 审查要求新的关系判断，先走 Explicit Pair → Decide → Apply；
5. `same/alias` Apply 的 source Canonical 由 Application 根据当前 ownership 推导，Agent 不得注入；
6. 若 source Canonical 包含当前 RelationCandidate 未审核的 Question，不扩大授权，必须 fail-closed 并先扩展 review；
7. 只有不涉及新增关系判断的既有 Canonical 维护才直接走 Merge/Split；
8. 正式写入前保留 explicit review、freshness、CAS；
9. Explicit Pair 必须恰好两个 Question，且 selection evidence 永远不代表 relation inference；
10. 不恢复任何 legacy Accept runtime/data path。

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
Entity / Hotspot 仍只发现未 canonicalized Question
Explicit Pair 可比较已 canonicalized Question，但不推断 relation
Explicit Pair 任一 Question 变化后 Decision / Apply fail-closed
same/alias 跨 Canonical 时 source owner 由 Application 当前状态推导
source Canonical 含未审核 Question 时 reviewed consolidation fail-closed
reviewed consolidation 复用 Canonical Merge 的 review/answer/index/integrity 事务边界
stale source 在 Decision / Apply 前 fail-closed
DecisionStore / MutationStore CAS 生效
Canonical post-commit invariants 通过
GitHub Actions artifact = dedup-relation-candidates
legacy canonical accept 不存在可执行/contract/test/path/data 回流
```
