# 06 GitHub Actions + AI 管理层优化计划

> 目标：把 `xhs` 从“本地手工运行脚本”升级为“可由 GitHub Actions 编排、可由 AI 安全触发、可审计、可回滚的知识资产管理流水线”。

---

## 1. 背景

`xhs` 当前已经具备较完整的业务内核：

```text
Question -> CanonicalQuestion -> Answer -> ReviewProgress
```

统一入口也已经收敛到：

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

当前的主要矛盾已经不是“有没有脚本”，而是：

```text
1. 管理动作仍然依赖本地手动执行
2. 每次执行哪些命令、顺序是什么，仍然需要人记住
3. AI 可以辅助分析，但还不能稳定触发标准流程
4. 数据、索引、canonical、answer、review 缺少统一自动化守门
5. 语义变更和生成产物缺少统一的 PR / Issue 审批路径
```

因此下一步应该引入 GitHub Actions，形成自动化管理层。

---

## 2. 核心判断

GitHub Actions 不应该替代 `scripts/xhs.js`。

更合理的分工是：

```text
AI / Codex
  负责理解目标、选择任务、触发白名单 workflow、总结结果

GitHub Actions
  负责标准流程编排、权限隔离、环境一致性、日志留存

scripts/xhs.js
  负责业务规则、数据校验、索引构建、canonical / answer / review 状态推进

GitHub Issue / PR
  负责审批、记录、复盘、回滚
```

最终形态：

```text
AI = 调度员
GitHub Actions = 流程执行器
xhs.js = 业务内核
Issue / PR = 审批与记录
CI = 质量守门
```

---

## 3. 设计原则

### 3.1 AI 只能触发白名单任务

不要让 AI 自由拼接 shell 命令。

Action 应该提供明确的 `task` 枚举，例如：

```text
validate
migrate-check
index-check
rebuild-index
canonical-suggest-hotspot
canonical-suggest-entity
canonical-check
answer-validate
answer-sync
review-today
review-weak
issue-sync-dry-run
quality-report
```

AI 只能选择这些任务，并传入有限参数。

---

### 3.2 默认只读，写操作分级

所有 Action 默认只读。

写操作分三类：

```text
A. 只读 / 校验任务
   可直接执行，不提交文件。

B. 可重建产物
   可以由 Action 生成分支或 PR，例如索引、报告、manifest。

C. 语义变更
   必须走 PR 或人工确认，例如 canonical merge / split、答案重写、taxonomy migration。
```

不要让 AI 直接把语义变更提交到 `master`。

---

### 3.3 数据仍然提交到仓库

本项目不依赖外部 S3 / R2 / OSS。

所有长期可复用资产仍然以 Git 友好形式保存在仓库：

```text
data/questions/*.jsonl
data/indexes/*.json
data/manifests/**/*.json
review/answers/*.md
review/progress.json
review/plans/*.md
review/issue_links.json
```

GitHub Actions 可以生成 artifact，但 artifact 只作为临时执行结果，不作为长期事实源。

---

### 3.4 所有流程必须可审计

每次 Action 至少要保留：

```text
1. workflow run 日志
2. 执行命令
3. 输入参数
4. 生成的 manifest / report
5. 如果有写入，必须对应 commit / PR / issue
```

---

## 4. 推荐 Workflow 结构

建议先新增 4 个 workflow。

```text
.github/workflows/ci.yml
.github/workflows/xhs-manage.yml
.github/workflows/xhs-weekly-report.yml
.github/workflows/xhs-reusable-node.yml
```

---

## 5. ci.yml：质量守门

### 5.1 目标

每次 push / PR 自动验证仓库是否仍然一致。

### 5.2 触发方式

```yaml
on:
  push:
    branches: [master]
  pull_request:
    branches: [master]
```

### 5.3 执行命令

```bash
npm test
npm run migrate:check
npm run validate
npm run index:check
npm run canonical:check
npm run answer:validate
```

### 5.4 权限

```yaml
permissions:
  contents: read
```

### 5.5 验收标准

```text
1. 任意 PR 都会自动跑 CI
2. question_id 漂移能被发现
3. schema/hash/index/canonical/answer 元数据问题能被发现
4. 不需要人工在本地重复执行完整检查
```

---

## 6. xhs-manage.yml：AI / 人工统一管理入口

### 6.1 目标

提供一个可由人或 AI 触发的统一入口，执行标准任务。

### 6.2 触发方式

```yaml
on:
  workflow_dispatch:
    inputs:
      task:
        description: Task to run
        required: true
        type: choice
        options:
          - validate
          - migrate-check
          - index-check
          - rebuild-index
          - canonical-suggest-hotspot
          - canonical-suggest-entity
          - canonical-check
          - answer-validate
          - answer-sync
          - review-today
          - review-weak
          - issue-sync-dry-run
          - quality-report
      entity:
        description: Entity for canonical-suggest-entity
        required: false
      canonical_id:
        description: Canonical id for single-item tasks
        required: false
      limit:
        description: Limit for list/suggest tasks
        required: false
        default: "50"
      create_pr:
        description: Create PR for generated changes
        required: false
        type: boolean
        default: false
```

### 6.3 任务映射

| task | 命令 | 是否写入 | 默认策略 |
|---|---|---:|---|
| validate | `npm test && npm run validate && npm run index:check && npm run canonical:check && npm run answer:validate` | 否 | 直接执行 |
| migrate-check | `npm run migrate:check` | 否 | 直接执行 |
| index-check | `npm run index:check` | 否 | 直接执行 |
| rebuild-index | `node scripts/xhs.js index build` | 是 | create_pr=true 时提交 PR |
| canonical-suggest-hotspot | `node scripts/xhs.js canonical suggest --hotspot --limit <limit>` | 是 | 生成候选 manifest，走 PR |
| canonical-suggest-entity | `node scripts/xhs.js canonical suggest --entity <entity> --limit <limit>` | 是 | 生成候选 manifest，走 PR |
| canonical-check | `node scripts/xhs.js canonical check` | 是 | 质量报告可走 PR |
| answer-validate | `node scripts/xhs.js answer validate` | 否 | 直接执行 |
| answer-sync | `node scripts/xhs.js answer validate && node scripts/xhs.js answer sync` | 是 | create_pr=true 时提交 PR |
| review-today | `node scripts/xhs.js review today --limit <limit> --with-issues` | 否 | 直接输出 |
| review-weak | `node scripts/xhs.js review weak --limit <limit> --with-issues` | 否 | 直接输出 |
| issue-sync-dry-run | `node scripts/xhs.js issue sync --priority P0 --repo liqiangcc/xhs` | 否 | 只预览 |
| quality-report | 后续新增 `node scripts/xhs.js report quality` | 是 | 生成报告，走 PR 或 issue |

---

## 7. xhs-weekly-report.yml：定期质量报告

### 7.1 目标

每周自动生成仓库状态报告，减少人工巡检。

### 7.2 建议统计内容

```text
1. questions 总数
2. valid questions 总数
3. canonical 总数
4. canonical 绑定 question rows 数
5. P0 canonical 总数
6. P0 missing answer 数
7. answer ready / draft / missing 分布
8. due review 数
9. weak review 数
10. taxonomy legacy alias 数
11. index check 是否通过
12. canonical check 是否通过
```

### 7.3 输出位置

建议输出到：

```text
data/manifests/reports/weekly_quality_report.json
review/plans/weekly_quality_report.md
```

也可以同步创建 GitHub Issue：

```text
[Weekly XHS Report] 2026-xx-xx
```

---

## 8. xhs-reusable-node.yml：可复用 Node 执行模板

### 8.1 目标

避免每个 workflow 重复写：

```text
checkout
setup-node
npm test
upload artifact
```

### 8.2 推荐抽象

```text
输入：node_version、run_command、upload_paths
输出：执行日志、artifact
```

第一阶段可以不做 reusable workflow，等 `ci.yml` 和 `xhs-manage.yml` 稳定后再抽象。

---

## 9. AI 触发协议

### 9.1 AI 触发原则

AI 触发 Action 时必须遵守：

```text
1. 只触发白名单 task
2. 不传任意 shell 命令
3. 语义变更必须 create_pr=true
4. 不直接向 master 写 semantic data
5. 触发后总结 workflow 结果
6. 如果 CI 失败，先解释失败原因，再给修复建议
```

### 9.2 AI 触发示例

#### 校验全仓库

```bash
gh workflow run xhs-manage.yml -f task=validate
```

#### 生成热点 canonical 候选

```bash
gh workflow run xhs-manage.yml \
  -f task=canonical-suggest-hotspot \
  -f limit=50 \
  -f create_pr=true
```

#### 针对 Redis 生成 canonical 候选

```bash
gh workflow run xhs-manage.yml \
  -f task=canonical-suggest-entity \
  -f entity=Redis \
  -f limit=50 \
  -f create_pr=true
```

#### 查看今日复习

```bash
gh workflow run xhs-manage.yml \
  -f task=review-today \
  -f limit=20
```

#### 同步答案状态

```bash
gh workflow run xhs-manage.yml \
  -f task=answer-sync \
  -f create_pr=true
```

---

## 10. 全流程管理闭环

目标闭环：

```text
新增或更新面经数据
  ↓
AI 触发 validate / migrate-check
  ↓
Action 校验主数据
  ↓
AI 触发 canonical-suggest-hotspot
  ↓
Action 生成 canonical_candidates manifest
  ↓
Action 创建 PR 或 Issue
  ↓
人工确认 accept / merge / split
  ↓
Action 跑 canonical-check + index-check
  ↓
AI 触发 answer init / answer-sync
  ↓
Action 同步 answer_status
  ↓
AI 触发 issue-sync-dry-run / apply
  ↓
GitHub Issues 成为移动端复习卡片
  ↓
AI 触发 review-today / review-weak
  ↓
用户复习并记录掌握度
  ↓
weekly-report 总结下一轮优化方向
```

---

## 11. 写操作策略

### 11.1 可以自动提交 PR 的文件

```text
data/indexes/*.json
data/manifests/**/*.json
review/plans/*.md
review/issue_links.json
```

### 11.2 必须人工确认的文件

```text
data/questions/questions.jsonl
data/questions/canonical_questions.jsonl
review/answers/*.md
review/progress.json
config/taxonomy.json
schemas/*.json
```

### 11.3 不建议 Action 自动修改的内容

```text
note_tagged/**
历史归档 docs/archive/**
旧采集脚本
```

---

## 12. 权限策略

### 12.1 CI

```yaml
permissions:
  contents: read
```

### 12.2 生成 PR

```yaml
permissions:
  contents: write
  pull-requests: write
```

### 12.3 同步 Issue

```yaml
permissions:
  contents: read
  issues: write
```

### 12.4 同时生成文件和 Issue

```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
```

原则：

```text
能 read 不 write
能 PR 不直推 master
能 dry-run 不 apply
```

---

## 13. 分阶段实施计划

## Phase 1：建立 CI 守门

### 目标

先保证所有提交都不会破坏主数据和索引。

### 任务

```text
1. 新增 .github/workflows/ci.yml
2. CI 执行 npm test
3. CI 执行 migrate:check
4. CI 执行 validate
5. CI 执行 index:check
6. CI 执行 canonical:check
7. CI 执行 answer:validate
```

### 验收

```text
push / PR 自动触发 CI
CI 失败时能定位是哪一类问题
master 分支始终处于可校验状态
```

---

## Phase 2：建立 xhs-manage 手动入口

### 目标

让人和 AI 都能通过一个 workflow 触发标准任务。

### 任务

```text
1. 新增 .github/workflows/xhs-manage.yml
2. 支持 validate
3. 支持 canonical-suggest-hotspot
4. 支持 canonical-suggest-entity
5. 支持 answer-sync
6. 支持 review-today / review-weak
7. 支持 issue-sync-dry-run
```

### 验收

```text
可以用 gh workflow run 触发任务
所有 task 都是白名单
不支持任意 shell command
默认不写 master
```

---

## Phase 3：生成 PR / Issue

### 目标

把 Action 输出变成可审查的 PR 或 Issue。

### 任务

```text
1. 对 rebuild-index 支持 create_pr
2. 对 canonical-suggest 支持 create_pr
3. 对 answer-sync 支持 create_pr
4. 对 weekly-report 支持创建 issue
5. PR 自动跑 CI
```

### 验收

```text
AI 可以触发生成候选 PR
PR 中能看到具体变更
CI 通过后再合并
语义变更不直推 master
```

---

## Phase 4：全流程 AI 协作

### 目标

AI 可以完成日常管理流程，但关键语义变更仍有人审查。

### 任务

```text
1. 给 Codex / AI 编写固定触发提示词
2. 每次运行后 AI 总结结果
3. AI 根据报告提出下一轮任务
4. 重要变更进入 PR
5. 人只需要确认 PR / Issue
```

### 验收

```text
AI 可以触发 validate / suggest / sync / review / report
AI 不直接污染主数据
所有变更有日志、有 PR、有 CI
管理复杂度明显下降
```

---

## 14. 建议立即执行的任务

下一步建议按这个顺序做：

```text
[ ] 新增 .github/workflows/ci.yml
[ ] 新增 .github/workflows/xhs-manage.yml
[ ] 在 package.json 增加 check 脚本：npm run test && npm run validate && npm run index:check
[ ] 让 xhs-manage 支持 validate / review-today / review-weak 三个只读任务
[ ] 再支持 canonical-suggest-hotspot，并生成 manifest
[ ] 最后加入 create_pr=true 的写入路径
```

---

## 15. Codex 执行提示词

可以把下面提示词交给 Codex：

```text
请基于当前 liqiangcc/xhs 仓库实现 GitHub Actions 管理层第一阶段。

目标：
1. 新增 .github/workflows/ci.yml。
2. CI 在 push / pull_request 到 master 时运行：
   - npm test
   - npm run migrate:check
   - npm run validate
   - npm run index:check
   - npm run canonical:check
   - npm run answer:validate
3. 新增 .github/workflows/xhs-manage.yml。
4. xhs-manage 使用 workflow_dispatch，支持 task 白名单：
   - validate
   - migrate-check
   - index-check
   - canonical-check
   - answer-validate
   - review-today
   - review-weak
5. 第一阶段所有任务只读，不提交文件，不创建 PR，不同步 issue。
6. 不允许传入任意 shell 命令。
7. 使用 Node 20。
8. 执行后更新 docs/refactor/06_github_actions_ai_management.md 的 Phase 1 状态。
9. 提交前确保 npm test、npm run validate、npm run index:check 通过。

约束：
- 不要修改业务数据。
- 不要修改 note_tagged。
- 不要直接引入外部存储。
- GitHub Action 权限默认 contents: read。
```

---

## 16. 成功标准

本轮优化完成后，`xhs` 应该具备：

```text
1. 每次提交自动校验
2. AI 可以触发标准管理任务
3. 所有任务通过白名单控制
4. 生成类任务可以逐步走 PR
5. 关键语义变更仍由人确认
6. 数据资产继续留在仓库内
7. 后续 canonical / answer / review 管理复杂度下降
```

一句话：

```text
GitHub Actions 应该成为 xhs 的自动化管理层，AI 只负责调度，不负责绕过规则直接改数据。
```
