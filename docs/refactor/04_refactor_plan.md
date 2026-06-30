# 04 分阶段重构计划

> 本文定义长期重构的里程碑、交付物、验收标准、推荐顺序和依赖关系。

---

## 1. 重构原则

```text
先稳定主数据，再做价值闭环
先新增新结构，再逐步替换旧脚本
先跑通主链路，再追求架构完整
先支持可重建，再支持自动化
```

不采用一次性大重写，而采用渐进式重构。

---

## 2. 总体路线图

```text
M0：文档与设计冻结
M1：Question 主数据层
M2：Taxonomy / Schema 单一事实源
M3：索引层
M4：CanonicalQuestion 题簇层
M5：Answer 答案资产层
M6：Review 复习闭环层
M7：Pipeline 状态机与迁移体系
M8：旧系统收敛与工程化完善
```

---

## M0：文档与设计冻结

## 目标

先统一业务目标、领域模型、技术方案和重构顺序。

## 交付物

```text
docs/refactor/README.md
docs/refactor/01_requirements.md
docs/refactor/02_domain_model.md
docs/refactor/03_technical_design.md
docs/refactor/04_refactor_plan.md
docs/refactor/05_execution_checklist.md
```

## 验收标准

```text
业务目标明确
核心使用场景明确
领域对象明确
技术分层明确
里程碑明确
执行清单明确
```

## 退出条件

```text
确认 Question 是主数据
确认 CanonicalQuestion 是知识资产
确认 AI 是候选生成器，不是系统内核
确认第一阶段不大改采集层
```

---

## M1：Question 主数据层

## 目标

把 `note_tagged/*.json` 中的题目展开成长期主数据：

```text
data/questions/questions.jsonl
data/questions/question_sources.jsonl
```

## 交付物

```text
scripts/lib/hash.js
scripts/lib/io.js
scripts/lib/question_store.js
scripts/migrate/build_questions_from_tagged.js
data/questions/questions.jsonl
data/questions/question_sources.jsonl
```

## 实施步骤

```text
1. 抽出 scripts/lib/hash.js
2. 实现 JSONL read/write 工具
3. 遍历 note_tagged/*.json
4. 展开 tagged_questions
5. 复制 note-level metadata 到 question
6. 生成 question_sources.jsonl
7. 输出稳定排序
8. 增加 basic validation
```

## 验收标准

```text
questions.jsonl 可重复生成
question_sources.jsonl 可重复生成
每个 question 有 question_id
每个 question 能追溯 source_note_id
question_id 与现有 hash 规则一致
输出结果排序稳定
```

## 非目标

```text
不移动 note_tagged
不删除 query_tagged
不做 canonical 聚类
不生成答案
```

---

## M2：Taxonomy / Schema 单一事实源

## 目标

把标签体系和数据结构从 Prompt/脚本中抽出来，形成统一事实源。

## 交付物

```text
config/taxonomy.json
schemas/question.schema.json
schemas/canonical_question.schema.json
schemas/review_progress.schema.json
scripts/lib/taxonomy.js
scripts/lib/schema.js
scripts/commands/validate.js
```

## 实施步骤

```text
1. 从 xhs_tagger/SKILL.md 提取 domain/question_type/cognitive_depth
2. 合并 normalize_tags.js 中实际存在的映射
3. 定义 taxonomy.v1
4. 定义 question.schema.json
5. 实现 validate taxonomy
6. 实现 validate schema
7. 输出质量报告，不立即强制修复全部历史数据
```

## 验收标准

```text
所有新生成 question 必须通过 schema 校验
所有新生成 question 必须通过 taxonomy 校验
历史数据偏离 taxonomy 时能输出报告
xhs_tagger 后续引用 taxonomy，而不是复制枚举
```

## 非目标

```text
不要求一次性修复所有历史标签
不要求立即删除 normalize_tags.js
```

---

## M3：索引层

## 目标

让查询从实时扫描 `note_tagged` 转为读取 `questions.jsonl + indexes`。

## 交付物

```text
scripts/build_index.js
scripts/lib/index_store.js
data/indexes/entity_index.json
data/indexes/company_index.json
data/indexes/domain_index.json
data/indexes/hotspot_index.json
scripts/commands/query.js
```

## 实施步骤

```text
1. 读取 questions.jsonl
2. 构建 entity_index
3. 构建 company_index
4. 构建 domain_index
5. 构建基础 hotspot_index
6. 实现 query entity/company/domain/hotspot
7. 和旧 query_tagged 做结果对比
```

## 验收标准

```text
entity 查询不再扫描 note_tagged
company 查询不再扫描 note_tagged
domain 查询不再扫描 note_tagged
索引可重复构建
索引输出稳定
查询结果可追溯到 question_id
```

## 非目标

```text
不引入数据库
不做全文搜索
不做 Web UI
```

---

## M4：CanonicalQuestion 题簇层

## 目标

从“原始题目列表”升级为“标准题簇知识资产”。

## 交付物

```text
data/questions/canonical_questions.jsonl
scripts/lib/canonical_store.js
scripts/commands/canonical.js
scripts/migrate/build_canonical_questions.js
```

## 实施步骤

```text
1. 基于 entity_index 找 Top 高频实体
2. 对每个实体召回候选 question
3. 按 domain.l2 + tech_entities + 题干相似度生成候选簇
4. AI 生成 canonical_title 候选
5. 人工或命令确认 merge
6. 写 canonical_questions.jsonl
7. 给 questions.jsonl 回填 canonical_id
8. hotspot_index 改为支持 canonical_id
```

## 验收标准

```text
Top 50 高频实体有 canonical 候选
至少 100 个 question 绑定 canonical_id
canonical merge 可追溯
canonical split 可执行
hotspot 可按 canonical_id 统计
```

## 非目标

```text
不追求全量自动聚类
不要求所有题都有 canonical_id
不要求 AI 自动决定最终 merge
```

---

## M5：Answer 答案资产层

## 目标

把深度答案从 question_id 维度升级到 canonical_id 维度。

## 交付物

```text
review/answers/{canonical_id}.md
review/answers/metadata.json
scripts/commands/answer.js
scripts/ai/generate_answer.js
```

## 实施步骤

```text
1. 选出 P0 canonical questions
2. 定义答案模板
3. 对单个 canonical_id 生成答案
4. 对 P0 批量生成答案
5. answer metadata 记录版本和生成器
6. prepare/review 优先复用已有答案
```

## 验收标准

```text
P0 canonical questions 至少 50 道有答案
答案文件绑定 canonical_id
同义题共享答案
已有答案默认不覆盖
答案结构统一
```

## 非目标

```text
不要求所有题都有答案
不要求一次性生成所有领域答案
```

---

## M6：Review 复习闭环层

## 目标

把题库变成可持续训练系统。

## 交付物

```text
review/progress.json
review/sessions/{date}.json
review/plans/{target}.md
scripts/lib/review_scheduler.js
scripts/commands/prepare.js
scripts/commands/review.js
config/review_strategy.json
```

## 实施步骤

```text
1. 定义 review_strategy
2. 实现 priority score
3. 实现 prepare 命令
4. 生成 N 天 review sessions
5. 初始化 progress
6. 实现 review today
7. 实现 review mark mastered/weak
8. weak 题进入下一轮调度
```

## 验收标准

```text
能按 company/topic/days 生成复习计划
能生成每日 session
能标记 mastered/learning/weak
weak 题会被调度到后续 session
已掌握题权重下降
```

## 非目标

```text
不做复杂间隔重复算法
不做 UI
不做多用户系统
```

---

## M7：Pipeline 状态机与迁移体系

## 目标

建立长期循环能力：新增数据、迁移、校验、索引、canonical、答案、复习都可追溯。

## 交付物

```text
scripts/commands/pipeline.js
scripts/lib/migration_runner.js
data/manifests/pipeline_runs/*.json
data/manifests/migrations/*.json
docs/adr/
```

## 实施步骤

```text
1. 定义 pipeline 状态
2. 每次 pipeline run 写 manifest
3. 定义 migration 文件规范
4. 实现 migrate status/up/apply
5. 每次 schema/taxonomy 变化写 migration
6. 增加 ADR 机制
```

## 验收标准

```text
pipeline run 可追溯
migration 可重复执行或明确跳过
每次数据结构变化有记录
失败任务可定位原因
```

---

## M8：旧系统收敛与工程化完善

## 目标

逐步收敛旧脚本，避免长期双轨。

## 交付物

```text
package.json
test/
.github/workflows/ci.yml
README 更新
docs/architecture.md
docs/taxonomy.md
docs/pipeline.md
docs/review_loop.md
```

## 实施步骤

```text
1. package.json 定义统一命令
2. node --test 增加基础测试
3. CI 跑 validate + index check + tests
4. query_tagged 改为兼容 wrapper
5. generate_review_plan 改用 review_scheduler
6. xhs_batch_analyzer 改用 canonical_id
7. README 只推荐 xhs.js 入口
```

## 验收标准

```text
新入口覆盖主要使用场景
旧脚本有迁移说明
CI 能发现 schema/taxonomy/hash/index 问题
文档能指导新一轮迭代
```

---

## 3. 推荐时间安排

```text
第 1 周：M0 + M1
第 2 周：M2 + M3
第 3 周：M4 PoC
第 4 周：M5 P0 答案
第 5 周：M6 prepare/review 闭环
第 6 周：M7/M8 工程化收敛
```

如果时间有限，优先级为：

```text
M1 > M2 > M3 > M4 > M6 > M5 > M7 > M8
```

原因：

```text
没有 questions.jsonl，后续全是沙子
没有 taxonomy/schema，长期会乱
没有 index，查询和复习都慢
没有 canonical，高频题价值不足
没有 review，无法循环
```

---

## 4. 风险控制

```text
所有新增结构先和旧系统并行
旧数据不立即移动
新脚本默认 dry-run 或可重复执行
每个阶段有验收后再进入下一阶段
```

---

## 5. 最小可行闭环

如果只做最小版本：

```text
M1：questions.jsonl
M3：indexes
M4：canonical Top 50
M6：prepare + sessions + progress
```

这个闭环能实现：

```text
目标输入 → 高频题定位 → 标准题簇 → 复习计划 → 每日任务 → 掌握度反馈
```

这就是长期系统的最小核心。
