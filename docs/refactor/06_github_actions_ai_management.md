# 06 GitHub Actions + AI 管理规范

> 目标：让 `xhs` 的自动化管理具备白名单、最小权限、可审计、可回滚的边界，同时不让 GitHub Actions 或 AI 绕过 Application/Domain 业务规则。

本文只维护 **GitHub Actions / AI 调度规则**。Canonical/Dedup 当前命令与业务流程以 `10_current_dedup_canonical_operations.md` 为操作 SSOT；内容建设目标以 `08_content_building_goals.md` 为准；legacy Accept 边界见 `09_legacy_canonical_accept_boundary.md`。

历史实现过程、旧 candidate manifest 方案和已完成阶段保留在 Git 历史中，不再复制到当前规范。

---

## 1. 当前架构分工

统一入口：

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

职责分离：

```text
AI / Codex
  -> 理解目标、选择白名单任务、触发 workflow、解释结果

GitHub Actions
  -> 流程编排、权限隔离、环境一致性、日志与 artifact

Interfaces / scripts/xhs.js
  -> 参数解析、调用 Application、格式化结果

Application / Domain
  -> 业务编排、freshness、显式决策、MutationPlan、事务规则

GitHub PR / Issue
  -> 审批、记录、复盘

CI
  -> 回归与质量守门
```

AI 不自由拼接 shell，不直接写业务主数据，不根据 similarity 自动决定 Canonical 关系。

---

## 2. 当前 Workflow

```text
.github/workflows/ci.yml
.github/workflows/xhs-manage.yml
.github/workflows/xhs-weekly-report.yml
```

### CI

触发：

```text
push master
pull_request -> master
```

核心检查：

```bash
npm run ci:check
git diff --exit-code
```

权限：

```yaml
permissions:
  contents: read
```

CI 是最终质量守门；任何生成型或语义变更 PR 都必须继续通过 CI。

---

## 3. xhs-manage 白名单

当前 `workflow_dispatch` 的任务白名单包括：

```text
validate
migrate-check
index-check
canonical-check
canonical-suggest-hotspot
canonical-suggest-entity
answer-validate
answer-validate-strict
quality-report
review-today
review-weak
issue-sync-dry-run
```

禁止新增：

```text
shell=<arbitrary command>
script=<arbitrary path>
command=<caller supplied command>
```

如果需要新能力，应新增一个语义明确的 task，并在 workflow 内固定映射到受控命令。

---

## 4. 任务分类

### 4.1 只读任务

例如：

```text
validate
migrate-check
index-check
canonical-check
answer-validate
answer-validate-strict
review-today
review-weak
issue-sync-dry-run
```

默认要求：

```text
contents: read
不创建业务 PR
不直接修改 master
能使用 --noWrite / --noManifest 时优先使用
```

### 4.2 生成型任务

当前主要是：

```text
canonical-suggest-hotspot
canonical-suggest-entity
quality-report
```

生成结果可以：

```text
默认 -> upload artifact
create_pr=true -> 单独写权限 job 创建 PR
```

生成型任务不能自动升级为业务语义授权。

### 4.3 语义变更

例如：

```text
RelationDecision
Canonical Apply
Canonical merge / split
answer promotion
review state mutation
issue sync apply
```

这类动作不得因为“前一步是 AI/Action 生成的”就自动获得授权。必须保留相应 Application/Domain 的显式审核、freshness、CAS、preflight/commit 边界。

---

## 5. Canonical Suggest 的当前语义

`canonical-suggest-hotspot`：

```bash
node scripts/xhs.js canonical suggest --hotspot --limit "$LIMIT" --noManifest
```

`canonical-suggest-entity`：

```bash
node scripts/xhs.js canonical suggest --entity "$ENTITY" --limit "$LIMIT" --noManifest
```

两者都只生成 Dedup review state：

```text
data/manifests/dedup/relation_candidate_queues.json
```

artifact：

```text
dedup-relation-candidates
```

`create_pr=true` 时，PR 只提交：

```text
data/manifests/dedup/relation_candidate_queues.json
```

**不再生成、上传、提交或创建 PR 更新：**

```text
data/manifests/canonical/canonical_candidates.json
```

Suggest 只产生 `RelationCandidate`，不是 RelationDecision，也不是 Canonical mutation authorization。

完整当前流程见：

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

---

## 6. Suggest 之后为什么不能自动 Apply

正式边界是：

```text
Suggest
  -> RelationCandidate
  -> explicit dedup decide
  -> persisted RelationDecision
  -> dedup apply
  -> freshness revalidation
  -> Canonical planning
  -> MutationPlan
  -> preflight / commit
```

因此 GitHub Actions 生成 review queue 后必须停止。

当前 `xhs-manage` 不自动调用：

```text
dedup decide
dedup apply
canonical merge
canonical split
```

如果未来要 Action 化这些能力，必须单独设计审批模型，不能在 Suggest workflow 中顺手串联。

---

## 7. Legacy `canonical accept`

`canonical accept` 不是当前 Suggest 的下一步。

它只为历史或人工提供的：

```text
data/manifests/canonical/canonical_candidates.json
schema: canonical_candidates.v1
```

保留兼容。

Actions 不得新生成这种 manifest，也不得把 RelationCandidate 转换成 legacy candidate 来绕过显式 Decision。

详细边界和删除条件：

```text
docs/refactor/09_legacy_canonical_accept_boundary.md
```

---

## 8. 权限规则

默认：

```yaml
permissions:
  contents: read
```

生成 PR 时才提升：

```yaml
permissions:
  contents: write
  pull-requests: write
```

同步 Issue 的未来/受控 apply 路径才需要：

```yaml
permissions:
  contents: read
  issues: write
```

原则：

```text
能 read 不 write
能 artifact 不直接提交
需要提交时走 PR
能 dry-run 不 apply
语义变更不直推 master
```

写权限 job 与普通 read-only job 应分离，不为了方便把整个 workflow 提升到写权限。

---

## 9. AI 触发协议

AI 触发 Action 时必须：

```text
1. 只使用 task 白名单
2. 不传任意 shell 命令
3. 说明关键输入，例如 entity / limit / filters
4. 触发后检查 run status 和失败步骤
5. 生成型结果说明 artifact / PR，而不是宣称业务已生效
6. CI 失败先定位原因，不绕过 gate
7. 不因为 RelationCandidate 存在就自动判断 same/alias
```

示例：

```bash
gh workflow run xhs-manage.yml -f task=validate

gh workflow run xhs-manage.yml \
  -f task=canonical-suggest-hotspot \
  -f limit=50

gh workflow run xhs-manage.yml \
  -f task=canonical-suggest-entity \
  -f entity=Redis \
  -f limit=50 \
  -f create_pr=true

gh workflow run xhs-manage.yml -f task=answer-validate-strict

gh workflow run xhs-manage.yml -f task=quality-report

gh workflow run xhs-manage.yml \
  -f task=review-today \
  -f limit=20
```

---

## 10. 当前管理闭环

```text
新增/更新面经数据
  ↓
validate / migrate-check
  ↓
index check/build
  ↓
canonical-suggest-hotspot / entity
  ↓
relation_candidate_queues.json artifact / PR
  ↓
显式 dedup decide
  ↓
受控 dedup apply 或 existing Canonical merge/split
  ↓
canonical-check + index-check
  ↓
answer candidate / audit / promote / validate / sync
  ↓
issue-sync-dry-run
  ↓
人工确认后受控 Issue apply（如启用）
  ↓
review today / mark / weak
  ↓
weekly quality report
```

注意：GitHub Action 目前负责到“生成待审核 RelationCandidate”这一层，不负责自动替人完成 RelationDecision。

---

## 11. 长期资产与 Artifact

长期事实仍提交仓库：

```text
data/questions/*.jsonl
data/indexes/*.json
data/manifests/**/*.json
review/answers/*.md
review/progress.json
review/evidence/*.json
```

Workflow artifact 只是执行结果的便捷载体，不替代 Git 中的正式事实源。

---

## 12. 后续 backlog

优先级应围绕减少人工重复操作，而不是扩大 AI 权限：

```text
1. docs/status drift 自动检查
2. weekly-report 可选创建 Issue
3. issue-sync-apply 独立人工触发 workflow
4. rebuild-index / answer-sync 的 create_pr 路径
5. Relation review 的可视化/审阅入口
```

任何新增写任务都应先回答：

```text
谁授权？
谁决定业务正确性？
依赖哪些 fresh revisions？
如何 fail closed？
是否可以 rollback/retry？
Interface 是否仍然薄？
```

---

## 13. 文档 SSOT

```text
06_github_actions_ai_management.md            -> Actions / AI 调度规范
08_content_building_goals.md                  -> 内容目标 / DoD
09_legacy_canonical_accept_boundary.md        -> legacy Accept 兼容边界
10_current_dedup_canonical_operations.md       -> 当前 Canonical/Dedup 操作 SSOT
```

历史 ADR、review plans 和 Git history 可用于理解演进，但不应覆盖当前命令语义。

---

## 14. 验证

Actions / CLI / Dedup 流程修改提交前至少执行：

```bash
node --test
npm run ci:check
git diff --check
```

验收：

```text
CI 通过
read-only task 不产生意外 diff
Suggest artifact 指向 relation_candidate_queues.json
Suggest 不生成 canonical_candidates.json
RelationDecision 仍需显式 actor
Decision / Apply freshness fail closed
MutationStore CAS / transaction tests 通过
```
