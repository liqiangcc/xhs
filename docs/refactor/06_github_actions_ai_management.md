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

当前第一阶段已落地：

```text
1. .github/workflows/ci.yml 已新增
2. .github/workflows/xhs-manage.yml 已新增
3. .github/workflows/xhs-weekly-report.yml 已新增
4. package.json 已新增 ci:* 只读检查脚本
5. validate / migrate-check / index-check / canonical-check / answer-validate / review-today / review-weak 支持 --noWrite 只读运行
6. xhs-manage 已支持 canonical-suggest-hotspot / canonical-suggest-entity，生成候选 manifest 并上传 artifact；create_pr=true 时走 PR
7. xhs-manage 已支持 quality-report，生成 JSON + Markdown 报告并上传 artifact；create_pr=true 时走 PR
8. xhs-manage 已支持 issue-sync-dry-run，默认不写 GitHub Issue
```

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
canonical-check
canonical-suggest-hotspot
canonical-suggest-entity
answer-validate
quality-report
review-today
review-weak
issue-sync-dry-run
```

默认开放只读任务；生成型任务必须走受控路径。当前 `canonical-suggest-*` 和 `quality-report` 可以上传 artifact，且仅在 `create_pr=true` 时由单独写权限 job 创建 PR。`issue-sync-dry-run` 只做预览，不调用 GitHub 写接口。`rebuild-index`、`answer-sync`、`issue-sync-apply` 等仍保留到后续阶段。

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
npm run ci:check
git diff --exit-code
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
          - canonical-check
          - canonical-suggest-hotspot
          - canonical-suggest-entity
          - answer-validate
          - quality-report
          - review-today
          - review-weak
          - issue-sync-dry-run
      entity:
        description: Entity for canonical-suggest-entity
        required: false
      canonical_id:
        description: Canonical id for single-item issue sync
        required: false
      priority:
        description: Priority filter for issue sync
        required: false
        default: "P0"
      answer_status:
        description: Answer status filter for issue sync
        required: false
      repo:
        description: GitHub repository for issue sync
        required: false
        default: "liqiangcc/xhs"
      limit:
        description: Limit for review list or canonical suggestion tasks
        required: false
        default: "50"
      create_pr:
        description: Create a pull request for generated reports or candidates
        required: false
        type: boolean
        default: false
```

### 6.3 任务映射

| task | 命令 | 是否写入 | 默认策略 |
|---|---|---:|---|
| validate | `npm run ci:check` | 否 | 直接执行 |
| migrate-check | `npm run ci:migrate:check` | 否 | 直接执行 |
| index-check | `npm run ci:index:check` | 否 | 直接执行 |
| canonical-check | `npm run ci:canonical:check` | 否 | 直接执行 |
| canonical-suggest-hotspot | `node scripts/xhs.js canonical suggest --hotspot --limit <limit> --noManifest` | 是 | 默认上传 artifact；`create_pr=true` 时创建 PR |
| canonical-suggest-entity | `node scripts/xhs.js canonical suggest --entity <entity> --limit <limit> --noManifest` | 是 | 默认上传 artifact；`create_pr=true` 时创建 PR |
| answer-validate | `npm run ci:answer:validate` | 否 | 直接执行 |
| quality-report | `node scripts/xhs.js report quality --noManifest` | 是 | 默认上传 artifact；`create_pr=true` 时创建 PR |
| review-today | `node scripts/xhs.js review today --limit <limit> --with-issues --noWrite` | 否 | 直接输出 |
| review-weak | `node scripts/xhs.js review weak --limit <limit> --with-issues --noWrite` | 否 | 直接输出 |
| issue-sync-dry-run | `node scripts/xhs.js issue sync --repo <repo> [filters] --noManifest` | 否 | 只预览 issue create/update，不调用 GitHub 写接口 |

### 6.4 只读契约

第一阶段的 Actions 必须使用 `--noWrite` 或 `ci:*` 脚本：

```bash
npm run ci:migrate:check
npm run ci:validate
npm run ci:index:check
npm run ci:canonical:check
npm run ci:answer:validate
node scripts/xhs.js review today --limit 20 --with-issues --noWrite
node scripts/xhs.js review weak --limit 20 --with-issues --noWrite
```

`--noWrite` 的语义是：

```text
1. 不写 data/manifests/runs/latest_*.json
2. 不写 validate / canonical 质量报告
3. review today / review weak 不初始化或保存 review/progress.json
4. workflow 最后用 git diff --exit-code 验证没有生成变更
```

### 6.5 canonical 候选生成

`canonical-suggest-hotspot` 和 `canonical-suggest-entity` 是第一批开放的生成型任务：

```bash
node scripts/xhs.js canonical suggest --hotspot --limit 50 --noManifest
node scripts/xhs.js canonical suggest --entity Redis --limit 50 --noManifest
```

它会更新工作区里的 `data/manifests/canonical/canonical_candidates.json`。默认路径只上传 `canonical-candidates` artifact；当 `create_pr=true` 时，workflow 会使用单独的写权限 job 创建分支和 PR。

权限边界：

```text
1. 普通 xhs-manage 任务使用 contents: read
2. canonical-suggest-* + create_pr=true 才使用 contents: write / pull-requests: write
3. 生成 PR 只提交 data/manifests/canonical/canonical_candidates.json
```

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

当前输出到：

```text
data/manifests/reports/quality_report.json
review/plans/quality_report.md
```

后续也可以同步创建 GitHub Issue：

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
  -f limit=50
```

当前该任务上传 `canonical-candidates` artifact，不创建 PR。

#### 生成热点 canonical 候选 PR

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

#### 生成质量报告

```bash
gh workflow run xhs-manage.yml \
  -f task=quality-report
```

#### 生成质量报告 PR

```bash
gh workflow run xhs-manage.yml \
  -f task=quality-report \
  -f create_pr=true
```

#### 查看今日复习

```bash
gh workflow run xhs-manage.yml \
  -f task=review-today \
  -f limit=20
```

#### 预览 GitHub Issue 同步

```bash
gh workflow run xhs-manage.yml \
  -f task=issue-sync-dry-run \
  -f priority=P0 \
  -f answer_status=ready
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
Action 上传 artifact；create_pr=true 时创建候选 PR
  ↓
人工确认 accept / merge / split
  ↓
Action 跑 canonical-check + index-check
  ↓
AI 触发 answer init / answer-sync
  ↓
Action 同步 answer_status
  ↓
AI 触发 issue-sync-dry-run
  ↓
人工确认后再本地或后续 issue-sync-apply 创建移动端复习卡片
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

状态：DONE

### 任务

```text
1. 新增 .github/workflows/ci.yml
2. CI 执行 npm run ci:check
3. CI 执行 git diff --exit-code
4. ci:* 脚本使用 --noWrite，避免写 report / manifest / progress
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

状态：DONE

### 任务

```text
1. 新增 .github/workflows/xhs-manage.yml
2. 支持 validate
3. 支持 migrate-check
4. 支持 index-check
5. 支持 canonical-check
6. 支持 answer-validate
7. 支持 review-today / review-weak
8. 支持 canonical-suggest-hotspot / canonical-suggest-entity 生成候选 artifact
9. 支持 quality-report artifact / PR
10. 支持 issue-sync-dry-run
11. 不支持任意 shell command
```

### 验收

```text
可以用 gh workflow run 触发任务
所有 task 都是白名单
不支持任意 shell command
默认不写 master；canonical-suggest-hotspot 只上传 artifact
生成型任务默认只上传 artifact；create_pr=true 才创建 PR
```

---

## Phase 3：生成 PR / Issue

### 目标

把 Action 输出变成可审查的 PR 或 Issue。

状态：PARTIAL

说明：`canonical-suggest-*` 和 `quality-report` 已支持 `create_pr=true` 的 PR 路径；`issue-sync-dry-run` 已支持预览。`rebuild-index`、`answer-sync`、`issue-sync-apply` 仍未开放为 Action 写入任务。

### 任务

```text
1. 对 rebuild-index 支持 create_pr
2. 对 canonical-suggest 支持 create_pr [DONE]
3. 对 quality-report 支持 create_pr [DONE]
4. 对 issue sync 支持 dry-run [DONE]
5. 对 answer-sync 支持 create_pr
6. 对 weekly-report 支持创建 issue
7. 对 issue-sync-apply 增加人工触发和 issues: write 权限
8. PR 自动跑 CI
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
[x] 新增 .github/workflows/ci.yml
[x] 新增 .github/workflows/xhs-manage.yml
[x] 在 package.json 增加 ci:* 只读检查脚本
[x] 让 xhs-manage 支持 validate / review-today / review-weak 等只读任务
[x] 再支持 canonical-suggest-hotspot，并生成 manifest artifact
[x] 为 canonical-suggest-hotspot 加入 create_pr=true 的写入路径
[x] 支持 canonical-suggest-entity
[x] 支持 quality-report artifact / PR
[x] 支持 issue-sync-dry-run
[ ] 用 canonical suggest 扩大覆盖到 200+ assigned rows
[ ] 针对新 canonical 批量补答案并运行 answer validate / sync
[ ] 将 issue-sync-apply 设计为单独人工触发 workflow
[ ] 为 weekly-report 增加可选创建 GitHub Issue 的路径
```

---

## 15. Codex 执行提示词

以下是第一阶段的历史执行提示词，当前已完成；下一轮执行应参考第 20 节。

```text
请基于当前 liqiangcc/xhs 仓库实现 GitHub Actions 管理层第一阶段。

目标：
1. 新增 .github/workflows/ci.yml。
2. CI 在 push / pull_request 到 master 时运行：
   - npm run ci:check
   - git diff --exit-code
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
9. 提交前确保 node --test、npm run ci:check、git diff --check 通过。

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

---

## 17. 本次 Review 发现的问题

> 以下问题来自对当前 `liqiangcc/xhs` 仓库 README、docs、核心脚本、测试、数据 manifest 和 workflow 状态的复盘。它们不是泛泛的优化建议，而是下一步应该纳入 Action 管理层的具体 backlog。

### 17.1 P0：CI 守门缺失

#### 现象

该问题已解决。仓库已经具备 `.github/workflows/ci.yml`，并在 push / PR 到 `master` 时运行 `npm run ci:check` 和 `git diff --exit-code`。

#### 影响

```text
1. schema / hash / index / canonical / answer 元数据问题会在 CI 中暴露
2. 数据变更、索引变更、文档变更有统一验收入口
3. 后续重点是保持新增命令遵守 noWrite / noManifest 契约
```

#### 建议

当前入口：

```text
.github/workflows/ci.yml
```

并执行：

```bash
npm run ci:check
git diff --exit-code
```

#### 验收标准

```text
push / pull_request 到 master 时自动运行
失败时能明确定位到 test / migrate / validate / index / canonical / answer 哪个阶段
默认权限为 contents: read
```

---

### 17.2 P0：文档执行清单状态过期

#### 现象

该问题已部分解决。`docs/refactor/05_execution_checklist.md` 已按当前代码状态同步 M1-M8，并区分 `DONE` / `PARTIAL` / `TODO`。后续仍需要持续维护，避免新能力落地后文档再次漂移。

```text
scripts/lib/hash.js
scripts/lib/io.js
scripts/lib/question_store.js
scripts/lib/index_store.js
scripts/commands/canonical.js
scripts/commands/answer.js
scripts/commands/review.js
test/hash.test.js
test/build_questions.test.js
test/build_index.test.js
test/canonical.test.js
test/answer.test.js
test/review.test.js
test/issue.test.js
```

#### 影响

```text
1. 后续 AI / Codex 会误判任务状态，可能重复实现已完成能力
2. 人工 review 时无法快速判断真实进度
3. 当前 source of truth 变得不可靠
```

#### 建议

新增一个状态同步任务：

```text
xhs-manage task: docs-status-check
```

第一阶段可以先人工修正文档状态，把 `05_execution_checklist.md` 中已完成部分改为：

```text
DONE
PARTIAL
TODO
```

不要只用 TODO / DONE，避免把部分完成的能力误判为完成。

#### 验收标准

```text
1. M1-M6/M8 已实现项状态与代码一致
2. 未实现项明确标记为 TODO 或 PARTIAL
3. 每个 PARTIAL 项写清楚缺失部分
```

---

### 17.3 P0：内容资产覆盖不足

#### 现象

当前主数据已经有较多题目，但 canonical 覆盖仍然很低：

```text
questions.jsonl: 9620 rows
canonical_questions.jsonl: 18 records
assigned question rows: 83 rows
```

#### 影响

```text
1. 高频题无法充分聚合为稳定知识资产
2. Answer / ReviewProgress 的价值无法放大
3. 复习闭环只能覆盖很小一部分题库
4. 当前系统更像“题目数据库”，还没有充分变成“知识资产系统”
```

#### 建议

建立 canonical 扩展 Action：

```text
xhs-manage task: canonical-suggest-hotspot
xhs-manage task: canonical-suggest-entity
```

优先目标：

```text
第一阶段：18 -> 50 canonical
第二阶段：50 -> 100 canonical
第三阶段：100 -> 200 canonical
```

优先策略：

```text
1. 先处理 hotspot frequency >= 3
2. 再处理 P0 高频实体：Redis / MySQL / JVM / JUC / Spring / MQ / 系统设计
3. 每轮生成候选 manifest
4. 人确认后 accept / merge / split
```

#### 验收标准

```text
1. canonical_questions.jsonl 至少达到 100 records
2. assigned question rows 至少达到 300 rows
3. canonical check 通过
4. hotspot_index 能按 canonical_id 聚合
```

---

### 17.4 P0：P0 答案缺失，Answer 层还没释放价值

#### 现象

该问题已在 2026-06-30 的内容建设迭代中处理：

```text
1. 12 个 P0 canonical 已补齐 ready 答案
2. answer validate 通过
3. answer sync 后 canonical_questions.jsonl 中 P0 missing answer = 0
4. 剩余 6 个 missing answers 均为 P1 canonical
```

#### 影响

```text
1. P0 复习卡片已经可以用于 GitHub Issue 和移动端查看
2. 后续新增 canonical 时仍需要继续走 missing / init-batch / validate / sync
3. P1 答案和新 canonical 答案仍会影响复习覆盖面
```

#### 建议

后续拆成两个阶段：

```text
Phase A：对新 canonical 和 P1 canonical 继续补答案
Phase B：再实现 answer generate / answer improve
```

Action 任务：

```text
xhs-manage task: answer-validate
本地命令：answer missing / answer init-batch / answer sync
后续 Action：answer-sync create_pr
```

后续再新增：

```text
node scripts/xhs.js answer missing --priority P1
node scripts/xhs.js answer init-batch --priority P1 --limit 20
```

#### 验收标准

```text
1. P0 canonical answer_status 全部为 ready
2. answer validate 通过
3. answer sync 后 canonical_questions.jsonl 状态正确
4. review issue card 能展示答案摘要
```

---

### 17.5 P1：Review 闭环还没有真实使用反馈

#### 现象

`review/progress.json` 已经存在，并且每个 canonical 都有初始 progress，但是大部分状态仍然是：

```text
status: new
review_count: 0
last_reviewed_at: null
```

#### 影响

```text
1. 系统还无法根据掌握度调整下一轮计划
2. weak / mastered 的价值没有体现
3. weekly report 无法判断真实学习进展
```

#### 建议

先 Action 化只读查询，再逐步 Action 化更新：

```text
xhs-manage task: review-today
xhs-manage task: review-weak
```

人工复习后再本地或 PR 更新：

```bash
node scripts/xhs.js review mark --canonical-id <cq_id> --result good
node scripts/xhs.js review mark --canonical-id <cq_id> --result again
```

后续可以增加：

```text
review-session-report
review-progress-pr
```

#### 验收标准

```text
1. review today 能通过 Action 触发
2. review weak 能通过 Action 触发
3. 每周能看到 reviewed_count / weak_count / mastered_count
4. review/progress.json 的语义更新必须走 PR 或人工确认
```

---

### 17.6 P1：Taxonomy legacy alias 数量较高

#### 现象

schema 校验通过，但 taxonomy summary 中 `strict_ok` 为 false，并存在大量 legacy alias。

#### 影响

```text
1. 标签体系短期可用，但长期不够干净
2. 高频统计可能受历史标签漂移影响
3. 新旧标签并存会增加查询和复习分组理解成本
```

#### 建议

短期不要强制修复全部历史数据。

当前可以先通过 `quality-report` 跟踪，后续再拆独立 taxonomy task：

```text
xhs-manage task: quality-report
后续：xhs-manage task: taxonomy-report
```

并按频次逐步迁移：

```text
1. Top 20 legacy alias 优先确认
2. 明确哪些保留为兼容 alias
3. 明确哪些需要写 migration 修正主数据
4. 每次 taxonomy 变更必须触发 validate + index check
```

#### 验收标准

```text
1. weekly report 输出 legacy_alias_count
2. Top legacy aliases 有明确处理状态
3. 新增数据不再引入未登记 taxonomy 值
```

---

### 17.7 P1：缺少统一质量报告入口

#### 现象

该问题已通过 `report quality` 和 `xhs-weekly-report.yml` 初步解决。当前质量报告会汇总：

```text
questions / canonical / answers / review / taxonomy / indexes / issues
```

输出位置：

```text
data/manifests/reports/quality_report.json
review/plans/quality_report.md
```

#### 影响

```text
1. AI 和人工现在可以用一个入口判断下一步优先级
2. weekly report 已经可以上传 artifact
3. 后续仍需要把报告结论转成 Issue 或 PR 审查任务
```

#### 建议

当前命令：

```bash
node scripts/xhs.js report quality
```

Action 任务：

```text
xhs-manage task: quality-report
xhs-weekly-report.yml
```

后续增强：

```text
1. weekly-report 可选创建 GitHub Issue
2. quality-report 可按 company / domain / priority 输出子报告
3. AI 根据 next_actions 自动提出下一轮任务
```

#### 验收标准

```text
1. 一个命令能看到 questions / canonical / answer / review / taxonomy / index 总览
2. 支持 markdown 输出，方便手机端查看
3. AI 可以根据 report 给出下一轮建议
```

---

### 17.8 P2：Issue 同步能力已有，但还需要纳入安全流程

#### 现象

`issue sync` 已经支持 dry-run 和 apply，并能维护 labels。但 issue 同步涉及 GitHub 写操作，不适合默认开启。

#### 影响

```text
1. 如果 AI 直接 apply，可能批量创建或修改 issue
2. 如果缺少 dry-run 审查，移动端 review card 可能被错误更新
```

#### 建议

Action 中已开放：

```text
issue-sync-dry-run
```

等 dry-run 稳定后再增加：

```text
issue-sync-apply
```

并要求：

```text
1. apply 只能手动触发
2. apply 需要 issues: write 权限
3. apply 前先自动跑 answer-validate + canonical-check
```

#### 验收标准

```text
1. dry-run 不写入 GitHub Issue
2. apply 只同步 P0 或指定 canonical_id
3. labels drift 可以被修复，但保留非 managed labels
```

---

## 18. Review 问题到 Action 任务的映射

| Review 问题 | 优先级 | 当前状态 | 对应 Action / 命令 | 验收信号 |
|---|---:|---|---|---|
| CI 缺失 | P0 | DONE | `ci.yml` | push/PR 自动校验 |
| 文档状态过期 | P0 | PARTIAL | 人工修正 | checklist 与代码一致 |
| canonical 覆盖不足 | P0 | IN_PROGRESS | `canonical-suggest-hotspot` / `canonical-suggest-entity` | canonical >= 100 |
| P0 答案缺失 | P0 | DONE | `answer missing` / `answer sync` | P0 missing = 0 |
| Review 未真实使用 | P1 | TODO | `review-today` / `review-weak` / `review mark` | review_count 增长 |
| taxonomy legacy alias 多 | P1 | IN_PROGRESS | `quality-report` | legacy_alias_count 可跟踪 |
| 质量报告分散 | P1 | DONE | `quality-report` / `xhs-weekly-report.yml` | 单一报告生成 |
| issue sync 需要权限控制 | P2 | PARTIAL | `issue-sync-dry-run` / 后续 `issue-sync-apply` | dry-run 先行，apply 受控 |

---

## 19. 下一轮执行顺序

结合当前状态，下一轮不要先做复杂的全自动流程，而应该按下面顺序推进：

```text
1. 保持 ci.yml 和 xhs-manage.yml 的只读任务稳定
2. 用 canonical-suggest-hotspot / canonical-suggest-entity 扩大覆盖到 200+ assigned rows
3. 对新增 canonical 和剩余 P1 canonical 补答案，运行 answer validate / answer sync
4. 对 P0 ready answers 先跑 issue-sync-dry-run，人工确认后再设计 issue-sync-apply
5. 开始真实复习：review today / review mark / review next，让 reviewed_count 增长
6. 每周查看 quality-report，处理 taxonomy legacy alias Top 项
```

原因：

```text
没有 canonical 覆盖，答案和复习价值不足
没有 issue dry-run 审查，移动端复习卡片容易批量误改
没有真实 review mark，系统无法根据掌握度调整下一轮
没有 weekly report 复盘，taxonomy 和覆盖率问题会再次分散
```

---

## 20. 更新后的 Codex 执行提示词

```text
请基于当前 liqiangcc/xhs 仓库继续推进内容覆盖和受控 GitHub Issue 复习卡片。

目标：
1. 保持第一阶段只读任务不回退，所有新增 task 继续走白名单。
2. 使用 canonical-suggest-hotspot / canonical-suggest-entity 扩大 canonical 覆盖。
3. 对新增 canonical 继续补答案，运行 answer validate / answer sync。
4. issue sync 先使用 dry-run；如果要新增 apply，必须单独 workflow、手动触发、issues: write 权限。
5. 新增写入型任务时，默认只允许 artifact 预览或 create_pr=true 的分支/PR 路径。
6. 不允许传入任意 shell command。
7. 默认权限 contents: read；需要写权限时单独说明。
8. 不修改 note_tagged，不引入外部存储。
9. 提交前确认 node --test、npm run ci:check、git diff --check 通过。

验收：
- 第一阶段 validate / review 只读任务仍不产生业务数据变更。
- canonical assigned rows 增长，且 canonical check 通过。
- 新增答案 answer validate 通过，answer sync 状态正确。
- issue dry-run 能清楚展示将创建/更新哪些复习卡片。
- docs/refactor/06_github_actions_ai_management.md 同步更新任务状态。
```
