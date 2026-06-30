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
3. package.json 已新增 ci:* 只读检查脚本
4. validate / migrate-check / index-check / canonical-check / answer-validate / review-today / review-weak 支持 --noWrite 只读运行
5. xhs-manage 已支持 canonical-suggest-hotspot，生成候选 manifest 并上传 artifact，不提交文件
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
answer-validate
review-today
review-weak
```

第一阶段只开放只读任务。当前额外开放 `canonical-suggest-hotspot` 作为受控生成任务：它只生成 `canonical_candidates.json` artifact，不提交文件。`rebuild-index`、`canonical-suggest-entity`、`answer-sync`、`issue-sync-*`、`quality-report` 等仍保留到后续阶段。

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
          - answer-validate
          - review-today
          - review-weak
      limit:
        description: Limit for review list or canonical suggestion tasks
        required: false
        default: "50"
```

### 6.3 任务映射

| task | 命令 | 是否写入 | 默认策略 |
|---|---|---:|---|
| validate | `npm run ci:check` | 否 | 直接执行 |
| migrate-check | `npm run ci:migrate:check` | 否 | 直接执行 |
| index-check | `npm run ci:index:check` | 否 | 直接执行 |
| canonical-check | `npm run ci:canonical:check` | 否 | 直接执行 |
| canonical-suggest-hotspot | `node scripts/xhs.js canonical suggest --hotspot --limit <limit> --noManifest` | 是 | 上传 `canonical_candidates.json` artifact，不提交 |
| answer-validate | `npm run ci:answer:validate` | 否 | 直接执行 |
| review-today | `node scripts/xhs.js review today --limit <limit> --with-issues --noWrite` | 否 | 直接输出 |
| review-weak | `node scripts/xhs.js review weak --limit <limit> --with-issues --noWrite` | 否 | 直接输出 |

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

`canonical-suggest-hotspot` 是第一批开放的生成型任务：

```bash
node scripts/xhs.js canonical suggest --hotspot --limit 50 --noManifest
```

它会更新工作区里的 `data/manifests/canonical/canonical_candidates.json`，workflow 随后把该文件上传为 `canonical-candidates` artifact。该任务当前不提交文件、不创建 PR；`create_pr=true` 仍属于后续阶段。

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
  -f limit=50
```

当前该任务上传 `canonical-candidates` artifact，不创建 PR。

#### 针对 Redis 生成 canonical 候选（后续阶段）

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

#### 同步答案状态（后续阶段）

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
Action 上传 artifact；后续阶段再创建 PR 或 Issue
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
8. 支持 canonical-suggest-hotspot 生成候选 artifact
9. 不支持任意 shell command
```

### 验收

```text
可以用 gh workflow run 触发任务
所有 task 都是白名单
不支持任意 shell command
默认不写 master；canonical-suggest-hotspot 只上传 artifact
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
[x] 新增 .github/workflows/ci.yml
[x] 新增 .github/workflows/xhs-manage.yml
[x] 在 package.json 增加 ci:* 只读检查脚本
[x] 让 xhs-manage 支持 validate / review-today / review-weak 等只读任务
[x] 再支持 canonical-suggest-hotspot，并生成 manifest artifact
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

仓库已经具备 `npm test`、`validate`、`index:check`、`migrate:check`、`canonical:check`、`answer:validate` 等脚本，但当前没有稳定的 GitHub Actions CI 守门流程。

#### 影响

```text
1. AI 或人工提交后，不能自动发现 schema / hash / index / canonical / answer 元数据问题
2. 数据变更、索引变更、文档变更缺少统一验收
3. 后续让 AI 管理仓库时，风险会集中在 master 分支
```

#### 建议

优先新增：

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

`docs/refactor/05_execution_checklist.md` 中大量 M1-M8 任务仍然标记为 `TODO`，但代码中已经存在对应实现和测试，例如：

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

`answer.js` 已经支持答案初始化、校验、状态同步，但当前主要能力仍是“答案文件管理”，还没有形成 P0 答案生产闭环。

当前 canonical 中大量 `answer_status` 仍是：

```text
missing
```

#### 影响

```text
1. review today 能列题，但无法直接沉淀可背诵答案
2. GitHub Issue review card 的价值有限
3. 面试准备场景还没有真正跑通
```

#### 建议

拆成两个阶段：

```text
Phase A：先补齐 P0 answer init + 人工/AI 填写答案
Phase B：再实现 answer generate / answer improve
```

Action 任务：

```text
xhs-manage task: answer-validate
xhs-manage task: answer-sync
xhs-manage task: answer-missing-p0-report
```

后续再新增：

```text
node scripts/xhs.js answer missing --priority P0
node scripts/xhs.js answer init-batch --priority P0 --limit 20
```

#### 验收标准

```text
1. P0 canonical 至少 20 个 answer_status != missing
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

建议 Action 化报告：

```text
xhs-manage task: taxonomy-report
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

当前质量信息分散在多个 manifest 中：

```text
data/manifests/quality/*.json
data/manifests/canonical/*.json
review/progress.json
review/answers/*.md
```

需要人工分别查看。

#### 影响

```text
1. AI 很难用一个入口判断下一步优先级
2. 人也无法快速看到项目当前健康度
3. weekly report 无法自然生成
```

#### 建议

新增命令：

```bash
node scripts/xhs.js report quality
```

输出：

```text
data/manifests/reports/quality_report.json
review/plans/quality_report.md
```

Action 任务：

```text
xhs-manage task: quality-report
xhs-weekly-report.yml
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

Action 中先只开放：

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

| Review 问题 | 优先级 | 对应 Action / 命令 | 验收信号 |
|---|---:|---|---|
| CI 缺失 | P0 | `ci.yml` | push/PR 自动校验 |
| 文档状态过期 | P0 | `docs-status-check` / 人工修正 | checklist 与代码一致 |
| canonical 覆盖不足 | P0 | `canonical-suggest-hotspot` / `canonical-suggest-entity` | canonical >= 100 |
| P0 答案缺失 | P0 | `answer-missing-p0-report` / `answer-sync` | P0 missing 下降 |
| Review 未真实使用 | P1 | `review-today` / `review-weak` | review_count 增长 |
| taxonomy legacy alias 多 | P1 | `taxonomy-report` | legacy_alias_count 可跟踪 |
| 质量报告分散 | P1 | `quality-report` | 单一报告生成 |
| issue sync 需要权限控制 | P2 | `issue-sync-dry-run` / `issue-sync-apply` | dry-run 先行，apply 受控 |

---

## 19. 下一轮执行顺序

结合本次 review，下一轮不要先做复杂的全自动流程，而应该按下面顺序推进：

```text
1. 保持 ci.yml 和 xhs-manage.yml 的只读任务稳定
2. 修正并持续维护 docs/refactor/05_execution_checklist.md 状态
3. 新增 create_pr=true，让 canonical-suggest-hotspot 可生成候选 PR
4. 新增 answer-missing-p0-report 或质量报告命令
5. weekly-report 汇总 canonical / answer / review / taxonomy 指标
6. 最后再考虑 issue-sync-apply
```

原因：

```text
没有 CI，AI 管理风险太高
没有状态同步，AI 会重复做错任务
没有 canonical 覆盖，答案和复习价值不足
没有答案，review 只是题目列表
没有 report，AI 无法稳定判断下一轮重点
```

---

## 20. 更新后的 Codex 执行提示词

```text
请基于当前 liqiangcc/xhs 仓库继续推进 GitHub Actions + AI 管理层第二阶段。

目标：
1. 保持第一阶段只读任务不回退，所有新增 task 继续走白名单。
2. 为 canonical-suggest-hotspot 增加 create_pr=true 分支/PR 路径。
3. 新增其他写入型任务时，默认只允许 create_pr=true 的分支/PR 路径。
4. 不允许传入任意 shell command。
5. 默认权限 contents: read；需要写权限时单独说明。
6. 不修改 note_tagged，不引入外部存储。
7. 提交前确认 node --test、npm run ci:check、git diff --check 通过。

验收：
- 第一阶段 validate / review 只读任务仍不产生业务数据变更。
- canonical-suggest-hotspot 可选择 artifact 预览或 PR 审批路径。
- docs/refactor/06_github_actions_ai_management.md 同步更新任务状态。
```
