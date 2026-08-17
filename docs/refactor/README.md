# XHS 长期重构计划总览

> This directory is the current source of truth for the XHS refactor.

> 目标：把 `xhs` 从“面经采集与处理脚本集合”升级为“长期可迭代、可维护、可循环的面试知识资产系统”。

---

## 1. 文档包结构

本目录是一套完整的长期重构规划文档，建议按顺序阅读：

```text
01_requirements.md                                   业务目标与需求定义
02_domain_model.md                                   领域模型与核心对象
03_technical_design.md                               技术方案与架构设计
04_refactor_plan.md                                  分阶段重构路线图
05_execution_checklist.md                            执行清单与验收标准
06_github_actions_ai_management.md                   当前 GitHub Actions + AI 调度规范
07_actions_review_todo.md                            Actions 管理层历史修复记录
08_content_building_goals.md                         当前内容建设目标与验收门槛
09_answer_content_standard.md                        分题型答案模板与 ready 审查标准
09_legacy_canonical_accept_boundary.md               Legacy Accept 已退役边界与永久回归规则
10_current_dedup_canonical_operations.md             当前 Dedup / Canonical 操作 SSOT
11_legacy_canonical_accept_consumer_inventory.md     Legacy Accept 完整退役证据
11_legacy_canonical_accept_consumer_inventory.json   上述退役证据的机器可检查事实源
12_canonical_read_only_command_audit.md              Canonical list / stats / check 已完成迁移记录
13_review_command_audit.md                           Review namespace 职责审计与迁移顺序
14_naming_convention_audit.md                        Review 架构角色命名完成记录
15_canonical_naming_lifecycle_audit.md               Canonical 生命周期命名完成记录
16_repository_role_term_audit.md                     仓库剩余角色命名完成记录
```

这些文档的关系是：

```text
业务目标 / 内容 DoD
        ↓
领域模型 / 技术方案
        ↓
重构计划 / 执行清单
        ↓
当前操作规则
  ├─ 06：Actions / AI 调度
  ├─ 10：Dedup / Canonical 命令与边界
  └─ 09 legacy：已退役边界 / 永久回归规则
        ↓
11：legacy Accept 完整退役证据
        ↓
12：Canonical read-side 已完成迁移记录
        ↓
13：Review namespace 迁移审计
        ↓
14 / 15：Review 与 Canonical 命名迁移完成记录
        ↓
16：仓库角色命名收口与防回归规则
        ↓
循环迭代
```

当前执行优先级：

```text
1. 10_current_dedup_canonical_operations.md：Canonical/Dedup 当前命令与操作边界
2. 08_content_building_goals.md：内容建设 C0-C10 目标、DoD 与退出条件
3. README.md：当前数据状态和日常入口
4. 06_github_actions_ai_management.md：Actions / AI 当前调度规范
5. 16_repository_role_term_audit.md：仓库架构角色命名已完成记录与防回归规则
6. 15_canonical_naming_lifecycle_audit.md：Canonical 生命周期命名已完成记录
7. 14_naming_convention_audit.md：Review 架构角色命名已完成记录
8. 13_review_command_audit.md：Review namespace 已完成迁移记录
9. 12_canonical_read_only_command_audit.md：Canonical read-side 已完成迁移记录
10. 11_legacy_canonical_accept_consumer_inventory.md：legacy Accept 完整退役证据
11. 05_execution_checklist.md：工程底座长期验收清单
12. 07 / 历史 ADR / review plans：历史证据，不作为当前命令 SSOT
```

如果 `08` 或历史文档中的旧命令示例与 `10_current_dedup_canonical_operations.md` 冲突，**命令语义以 10 和当前代码/测试为准**；08 继续负责业务目标和内容完成定义。Review namespace 的工程迁移顺序以 `13_review_command_audit.md` 为准；`12_canonical_read_only_command_audit.md` 保留为已完成迁移记录。

内容建设中的 60/200、100/300、200/600 都是中间门槛；最终目标以 `08_content_building_goals.md` 为准：所有真实面试题绑定 Canonical、拥有 ready 答案和 ReviewProgress，并能从查询或复习入口实际访问。

截至 2026-08-17，SoC/SRP 工程重构及仓库架构角色命名已经收口；后续主线不再扩大架构改造范围，而是按内容质量合同推进候选、证据、独立审查、人工签核与真实复习闭环。

---

## 2. 最终目标

本项目的长期目标不是“采集更多面经”，而是：

> 持续构建、维护和迭代面试知识资产，并通过复习闭环提升面试准备效率。

系统最终应该支持：

```text
新增面经
  ↓
提取题目
  ↓
打标签
  ↓
归一化为标准题簇
  ↓
生成/更新答案
  ↓
生成复习计划
  ↓
用户复习并反馈掌握度
  ↓
下一轮继续优化题库、答案和计划
```

---

## 3. 核心设计判断

### 3.1 Question 是主数据

当前仓库的历史结构以 `note_id` 为中心，题目嵌在 `note_tagged/{note_id}.json` 里。长期应切换为以 `Question` 为中心。

```text
note_tagged/*.json
  ↓
questions.jsonl
  ↓
canonical_questions.jsonl
  ↓
answers / review_progress / review_sessions
```

### 3.2 CanonicalQuestion 是知识资产

`question_id` 解决原文稳定，`canonical_id` 解决同义题聚合。

例如：

```text
HashMap 为什么线程不安全？
HashMap 并发下有什么问题？
HashMap 多线程 put 会发生什么？
```

应该归到同一个标准题簇：

```text
canonical_id: cq_hashmap_thread_safety
canonical_title: HashMap 为什么线程不安全？
```

### 3.3 大模型是语义加工插件，不是系统内核

大模型适合做：

```text
非结构化题目提取
题目标签候选
canonical 合并建议
深度答案生成
```

代码必须负责：

```text
question_id
schema 校验
taxonomy 校验
索引构建
高频统计
复习调度
状态推进
```

---

## 4. 目标系统能力

最终希望形成以下能力闭环：

```text
Ingestion Loop   新面经稳定入库
Quality Loop     数据质量校验和修复
Index Loop       查询索引可重建
Canonical Loop   同义题聚合和热点统计
Answer Loop      高频题答案持续版本化
Review Loop      复习计划、每日任务、掌握度反馈
Actions Loop     AI 触发白名单任务，GitHub Actions 执行和审计
```

---

## 5. 推荐执行顺序

```text
M1：建立 Question 主数据层
M2：建立 Taxonomy / Schema 单一事实源
M3：建立索引层
M4：建立 CanonicalQuestion 题簇层
M5：建立答案资产层
M6：建立复习闭环
M7：建立迁移、测试、CI 和 ADR 机制
M8：建立 GitHub Actions + AI 管理层
```

工程重构里程碑见 `04_refactor_plan.md`，当前内容建设目标见 `08_content_building_goals.md`，Canonical/Dedup 当前操作见 `10_current_dedup_canonical_operations.md`，Legacy Accept 完整退役证据见 `11_legacy_canonical_accept_consumer_inventory.md`，Canonical read-side 已完成迁移记录见 `12_canonical_read_only_command_audit.md`，Review namespace 迁移审计见 `13_review_command_audit.md`；Review / Canonical 命名完成记录分别见 `14_naming_convention_audit.md`、`15_canonical_naming_lifecycle_audit.md`，仓库剩余角色命名收口见 `16_repository_role_term_audit.md`。

---

## 6. 第一阶段最小交付

第一阶段不要大改采集层，也不要先上数据库。先交付稳定底座：

```text
config/taxonomy.json
schemas/question.schema.json
scripts/lib/hash.js
scripts/migrate/build_questions_from_tagged.js
data/questions/questions.jsonl
scripts/xhs.js validate questions
```

这一步完成后，后续 canonical、答案、复习、索引都能建立在稳定主数据之上。

---

## 7. 成功标准

长期重构成功不看“改了多少文件”，而看这些结果：

```text
新增一批 note 后，能稳定进入 questions.jsonl
所有 question_id 稳定不漂移
所有标签能被 taxonomy 校验
查询索引可重建
canonical merge/split 可追溯
答案绑定 canonical_id 并可版本化
review progress 能持续滚动
AI 输出不合格时不会污染主数据
GitHub Actions 能守住质量边界
旧脚本能逐步淘汰，而不是一次性推翻
```
