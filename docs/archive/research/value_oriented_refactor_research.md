# XHS 价值导向重构与技术预研

> Historical note: this document is archived for context. The current execution plan lives in `docs/refactor/`.

> 日期：2026-06-30  
> 仓库：`liqiangcc/xhs`  
> 关键词：价值导向、Question-Centric、Canonical Question、索引层、复习闭环、技术预研

---

## 0. 结论先行

这个仓库不应该继续被定义成“小红书采集脚本仓库”，而应该重构成：

> 面试题知识资产生产与复习训练系统。

当前仓库已经有采集、结构化、打标签、查询、复习计划、答案生成等能力雏形。真正的瓶颈不是“题目数量不够”，而是：

```text
题目没有成为一等实体
同义题没有 canonical 聚合
标签体系没有单一事实源
查询和统计依赖临时扫描
复习计划没有形成状态闭环
Agent 和脚本之间职责边界不清
```

因此重构主线应该是：

```text
note-centric  →  question-centric
脚本集合       →  数据产品流水线
静态题库       →  高频知识资产
一次性分析     →  可持续复习训练系统
```

最小可行重构不建议先大改采集层，而应该先做四件事：

```text
1. 从 note_tagged 生成 data/questions/questions.jsonl
2. 基于 questions.jsonl 生成 entity/company/domain/hotspot 索引
3. 引入 canonical_questions.jsonl，先合并 Top 高频题簇
4. 让 review/answers 和 review/progress 绑定 canonical_id，而不是只绑定 question_id
```

---

## 1. 目标重新定义

### 1.1 当前隐含目标

现有 README 已经表达出仓库目标：从小红书面经中抽取题目、结构化、打标签、查询。

但这只是数据生产链路，不是最终价值目标。

### 1.2 推荐目标

推荐把目标明确成：

> 构建一个面向 Java/后端/大厂面试的高频题库、知识图谱、深度答案和复习训练系统。

它应该能回答这些问题：

```text
美团社招最常问哪些 MySQL 题？
Redis 高频题按 L1/L2/L3 应该怎么刷？
HashMap、ThreadLocal、JVM GC 分别有哪些原题和变体？
哪些题其实是同一类题，只是表述不同？
某个知识点有没有 1 分钟版、项目版、追问版答案？
我哪些题掌握了，哪些题还没有复习？
明天应该刷哪些题？
面试前三天应该优先冲哪些高频题？
```

### 1.3 价值公式

后续所有重构都围绕这个公式：

```text
最终价值 = 题目质量 × 高频准确度 × 标签稳定性 × 答案深度 × 复习闭环
```

采集只是输入，不是核心价值。

---

## 2. 当前仓库的主要结构性问题

## 2.1 问题一：数据中心仍然是 note，不是 question

当前主要产物是：

```text
note_structured/{note_id}.json
note_tagged/{note_id}.json
```

也就是说，题目被嵌在笔记里。

但复习和查询真正关心的是：

```text
question_id
original_question
canonical_id
domain
question_type
cognitive_depth
tech_entities
company
round
level
answer
review_status
```

因此应该把 `question` 提升为一等实体。

### 不合理点

```text
按 note 存储适合溯源，不适合作为题库主表。
按 note 查询会导致统计、热点、复习、答案都反复 flatten。
同一个 question 出现在多个 note 时，缺少统一 question_sources 关系表。
```

### 重构方向

```text
note_tagged/*.json
  ↓ migrate
questions.jsonl
question_sources.jsonl
canonical_questions.jsonl
```

---

## 2.2 问题二：question_id 只解决“原文稳定”，没有解决“同义聚合”

当前 question_id 基于原题文本 hash。

这可以保证同一个原文稳定，但无法合并语义相同的题。

例如：

```text
HashMap 为什么线程不安全？
HashMap 为什么不是线程安全的？
HashMap 并发下有什么问题？
HashMap 多线程 put 会发生什么？
```

这几道题应该属于同一个 canonical question。

### 推荐设计

```text
question_id      = 原始题目 hash，用于可追溯
canonical_id     = 标准题簇 ID，用于热点、高频、答案和复习
canonical_title  = 标准题目名，例如 HashMap 为什么线程不安全？
```

这样 hotspot 才能从“重复原文统计”升级成“同类问题统计”。

---

## 2.3 问题三：标签体系没有单一事实源

当前标签标准分散在：

```text
skills/xhs_tagger/SKILL.md
scripts/normalize_tags.js
scripts/query_tagged.js
README.md
历史 note_tagged 数据
```

这会导致：

```text
打标时一套标准
清洗时另一套标准
查询时第三套标准
统计报告再写死一套领域名
```

### 推荐设计

新增：

```text
config/taxonomy.json
scripts/lib/taxonomy.js
schemas/tagged_question.schema.json
```

所有 Skill、脚本、README、校验、查询、复习计划都引用同一份 taxonomy。

---

## 2.4 问题四：查询层承担了太多职责

当前 `query_tagged.js` 同时负责：

```text
读取 note_tagged
flatten questions
过滤
统计
hotspot 聚合
格式化输出
```

这让它变成“查询 CLI + 数据引擎 + 统计引擎”。

### 推荐拆分

```text
scripts/lib/question_store.js   # 读取 questions.jsonl
scripts/lib/filter.js           # 条件过滤
scripts/lib/stats.js            # 统计
scripts/lib/hotspot.js          # 热点聚合
scripts/build_index.js          # 构建索引
scripts/commands/query.js       # CLI 入口
```

`query_tagged.js` 后续只保留兼容入口。

---

## 2.5 问题五：复习计划已经出现，但还不是复习系统

仓库已经有 `generate_review_plan.js`、`generate_mysql_stats.js`、`xhs_batch_analyzer` 等复习层能力。

但它们仍然更像静态报告生成器。

### 不合理点

```text
复习计划部分逻辑硬编码
答案和 question_id 绑定，未绑定 canonical_id
缺少 review_progress
缺少 review_session
缺少掌握度、复习次数、错题记录
```

### 推荐方向

```text
review/answers/{canonical_id}.md
review/progress.json
review/sessions/{date}.json
review/plans/{date}.md
review/mistakes/{canonical_id}.md
```

复习系统的核心不是“生成答案”，而是“持续知道下一步该复习什么”。

---

## 2.6 问题六：pipeline 还没有成为状态机

当前 pipeline 能发现任务、生成 hash、输出 action。

但真正的结构化和打标仍依赖 Agent 按 Skill 写文件。

### 目标职责划分

```text
pipeline 负责状态机
Agent 负责生成候选内容
脚本负责校验、落盘、索引、状态推进
```

### 推荐状态

```text
raw_note
desc_ready
ocr_ready
structured_ready
tagged_ready
validated
indexed
canonicalized
answer_ready
review_ready
```

每次 pipeline run 写 manifest，而不是只看文件是否存在。

---

# 3. 目标架构

## 3.1 分层架构

```text
┌──────────────────────────────────────────────┐
│ 6. Review / Training Layer                   │
│    复习计划、深度答案、掌握度、每日训练       │
├──────────────────────────────────────────────┤
│ 5. Query / Insight Layer                     │
│    搜索、过滤、热点、公司偏好、知识图谱       │
├──────────────────────────────────────────────┤
│ 4. Index Layer                               │
│    questions.jsonl / entities / hotspots     │
├──────────────────────────────────────────────┤
│ 3. Knowledge Normalization Layer             │
│    canonical question、taxonomy、entity merge │
├──────────────────────────────────────────────┤
│ 2. Structured Data Layer                     │
│    source notes、raw questions、tagged notes  │
├──────────────────────────────────────────────┤
│ 1. Pipeline Layer                            │
│    discover、extract、tag、validate、index    │
└──────────────────────────────────────────────┘
```

## 3.2 新目录结构

```text
xhs/
├── README.md
├── package.json
├── config/
│   ├── taxonomy.json
│   ├── pipeline.json
│   └── review_strategy.json
├── schemas/
│   ├── source_note.schema.json
│   ├── question.schema.json
│   ├── tagged_question.schema.json
│   ├── canonical_question.schema.json
│   └── review_progress.schema.json
├── scripts/
│   ├── xhs.js
│   ├── build_index.js
│   ├── migrate/
│   │   ├── build_questions_from_tagged.js
│   │   └── build_canonical_questions.js
│   ├── lib/
│   │   ├── hash.js
│   │   ├── io.js
│   │   ├── taxonomy.js
│   │   ├── schema.js
│   │   ├── question_store.js
│   │   ├── stats.js
│   │   ├── hotspot.js
│   │   └── review_scheduler.js
│   └── commands/
│       ├── query.js
│       ├── validate.js
│       ├── pipeline.js
│       ├── index.js
│       └── review.js
├── data/
│   ├── sources/
│   │   └── notes.jsonl
│   ├── curated/
│   │   ├── structured_notes/
│   │   └── tagged_notes/
│   ├── questions/
│   │   ├── questions.jsonl
│   │   ├── question_sources.jsonl
│   │   └── canonical_questions.jsonl
│   ├── indexes/
│   │   ├── entity_index.json
│   │   ├── company_index.json
│   │   ├── domain_index.json
│   │   └── hotspot_index.json
│   └── manifests/
│       └── pipeline_runs/
├── review/
│   ├── answers/
│   ├── sessions/
│   ├── progress.json
│   ├── plans/
│   └── mistakes/
├── skills/
├── docs/
└── test/
```

---

# 4. 核心数据模型

## 4.1 SourceNote

来源笔记只负责溯源，不再承担题库职责。

```text
note_id: 65a0d1d8000000001e0081ae
source: 小红书
company: 百度
position: 高级开发工程师
round: 未知
level: 社招
year: 未知
date: 未知
status: tagged
question_count: 1
```

## 4.2 Question

题目是主数据。

```text
question_id: 4068b82fcdc6c006604e375a5fccaa02
original_question: master选举的过程？
source_note_id: 65a0d1d8000000001e0081ae
company: 百度
position: 高级开发工程师
round: 未知
level: 社招
year: 未知
domain.l1: 系统设计
domain.l2: 分布式架构
question_type: 原理深度_UnderTheHood
cognitive_depth: L2_Mechanism
tech_entities: master选举, 选主算法
is_valid_for_library: true
```

## 4.3 QuestionSource

一个 canonical question 可能来自多个 note。

```text
question_id: 4068b82fcdc6c006604e375a5fccaa02
source_note_id: 65a0d1d8000000001e0081ae
company: 百度
round: 未知
level: 社招
source_weight: 1
```

## 4.4 CanonicalQuestion

标准题簇是知识资产核心。

```text
canonical_id: cq_distributed_master_election
canonical_title: 分布式系统中的 master 选举过程是什么？
aliases:
  - master选举的过程？
  - Zookeeper 如何做选主？
  - Raft leader election 怎么实现？
primary_domain: 系统设计 / 分布式架构
primary_entities: 选主算法, Raft, ZooKeeper
question_ids:
  - 4068b82fcdc6c006604e375a5fccaa02
frequency: 1
companies: 百度
review_priority: P1
```

## 4.5 Answer

答案应该绑定 canonical_id。

```text
canonical_id: cq_distributed_master_election
answer_path: review/answers/cq_distributed_master_election.md
style: senior_engineer
version: 1
updated_at: 2026-06-30
```

## 4.6 ReviewProgress

```text
canonical_id: cq_distributed_master_election
status: learning
review_count: 2
last_reviewed_at: 2026-06-30
next_review_at: 2026-07-02
difficulty: 4
confidence: 0.6
mistake_count: 1
```

---

# 5. 技术预研

## 5.1 存储方案预研

### 方案 A：继续使用 note_tagged/*.json

优点：

```text
不用迁移
与现有脚本兼容
按 note 溯源直观
```

缺点：

```text
不适合题库主表
每次查询都要扫描和 flatten
热点统计不准确
复习进度难以绑定
多来源同题无法自然表达
```

结论：只作为兼容层，不作为新主数据层。

### 方案 B：questions.jsonl + 派生 indexes

JSON Lines 每一行是一个合法 JSON 值，并建议用换行符作为行终止；这种格式适合一条记录一行的题库数据，方便增量生成、diff、grep、脚本处理和 Git 管理。参考：https://jsonlines.org/

优点：

```text
最适合当前仓库规模
低依赖
Git diff 友好
容易生成和重建
适合作为 source of truth
方便后续导入 SQLite、DuckDB、向量库
```

缺点：

```text
复杂查询需要自己建索引
事务能力弱
并发写入不适合
```

结论：推荐作为 Phase 1 主方案。

### 方案 C：SQLite + FTS5

SQLite FTS5 是 SQLite 的全文检索虚拟表模块，适合在较大文档集合中高效搜索包含指定词项的文档；SQLite 也内置 JSON 函数和操作符，可处理 JSON 字段。参考：https://www.sqlite.org/fts5.html 和 https://www.sqlite.org/json1.html

优点：

```text
查询能力强
支持 full-text search
支持结构化过滤
适合做本地题库应用
可以把 canonical、review_progress、answers 都关系化
```

缺点：

```text
Git diff 不如 JSONL 直观
需要迁移脚本
需要确定 Node SQLite 依赖
```

结论：推荐作为 Phase 2 查询引擎，不建议一开始替代 JSONL 主数据。

### 方案 D：DuckDB

DuckDB 适合分析型查询，但官方文档显示旧 Node.js client 已 deprecated，并提示应使用 DuckDB Node Neo 包；因此如果主要目标是本地交互式题库和全文搜索，DuckDB 不适合作为第一阶段核心依赖。参考：https://duckdb.org/docs/stable/clients/nodejs/overview

优点：

```text
分析能力强
适合统计报表
可用于离线聚合
```

缺点：

```text
对全文搜索和复习系统不是最短路径
旧 Node client deprecated
引入成本高于 JSONL
```

结论：暂不采用。未来如果要做大规模统计分析，可以作为离线分析工具。

### 存储方案最终选择

```text
Phase 1: JSONL 作为主数据 + JSON indexes
Phase 2: SQLite/FTS5 作为查询加速层
Phase 3: 如需复杂分析，再评估 DuckDB
```

---

## 5.2 查询与索引预研

### 当前方式

```text
query_tagged.js → 读取所有 note_tagged/*.json → flatten → filter/stats/hotspot
```

### 推荐方式

```text
note_tagged/*.json
  ↓ migrate
questions.jsonl
  ↓ build_index
entity_index.json
company_index.json
domain_index.json
hotspot_index.json
  ↓ query
```

### 索引设计

```text
entity_index.json:
  Redis -> [question_id...]
  HashMap -> [question_id...]

company_index.json:
  美团 -> [question_id...]
  字节 -> [question_id...]

domain_index.json:
  数据库/MySQL -> [question_id...]
  Java基础/JVM -> [question_id...]

hotspot_index.json:
  canonical_id -> frequency, companies, entities, question_ids
```

### 查询命令目标

```bash
node scripts/xhs.js query entity Redis --valid
node scripts/xhs.js query company 美团 --level 社招
node scripts/xhs.js query hotspot --domain MySQL
node scripts/xhs.js query canonical cq_hashmap_thread_safety
```

---

## 5.3 Canonical 聚类预研

### 为什么需要 canonical

没有 canonical 层时，热点统计只能统计完全相同或极接近的原文。

有 canonical 层后，可以回答：

```text
同一个知识点的所有问法有哪些？
哪个题簇最高频？
哪个题簇对应哪些公司？
一份答案能覆盖哪些原题？
```

### 聚类策略

推荐三阶段：

```text
阶段 1：规则聚类
- 标准化大小写、标点、空格
- 同义实体归一化，例如 k8s -> Kubernetes
- 去掉问法噪声，例如 为什么/请说说/介绍一下

阶段 2：候选生成
- 同 domain.l2
- 共享 tech_entities
- 题干 token overlap 高
- 编辑距离或 Jaccard 相似度高

阶段 3：人工或 Agent 确认
- 输出候选簇
- 人工确认 merge/split
- 生成 canonical_title
```

### 命令设计

```bash
node scripts/xhs.js canonical suggest --entity HashMap
node scripts/xhs.js canonical merge --ids q1,q2,q3 --title "HashMap 为什么线程不安全？"
node scripts/xhs.js canonical split --canonical-id cq_xxx
node scripts/xhs.js canonical stats
```

### 初始目标

先处理 Top 50 高频实体，不追求一次性全自动。

---

## 5.4 测试与质量门禁预研

Node.js 内置 `node:test` 模块已经是稳定能力，可直接用于最小测试体系，不需要一开始引入 Jest/Vitest。官方文档说明 test runner 稳定，并支持 `node --test` 运行测试。参考：https://nodejs.org/api/test.html

### 推荐测试

```text
test/hash.test.js
- 同一题目 hash 稳定
- 特殊字符归一化稳定

test/taxonomy.test.js
- domain.l1 必须来自 taxonomy
- question_type 必须来自 taxonomy
- cognitive_depth 必须来自 taxonomy

test/build_questions.test.js
- 从 tagged note 展开 questions.jsonl
- note metadata 正确复制到 question

test/build_index.test.js
- entity/company/domain 索引可重建
```

### 推荐 CI

```bash
node --test
node scripts/xhs.js validate taxonomy
node scripts/xhs.js validate questions
node scripts/xhs.js index build --check
```

---

## 5.5 Agent 职责边界预研

### 当前问题

Agent 既负责理解、生成，又负责实际写文件和推进状态。

这会让 pipeline 很难复现。

### 推荐边界

```text
Agent 做：
- 结构化提取候选
- 标签候选
- canonical_title 候选
- 深度答案候选

脚本做：
- schema 校验
- taxonomy 校验
- hash 计算
- manifest 写入
- 状态推进
- 索引生成
- 复习计划生成
```

### 原则

```text
AI 产出候选
代码决定是否入库
状态机决定下一步
```

---

# 6. 推荐重构路线图

## M1：Question 主数据层

目标：把 note-centric 转成 question-centric。

交付物：

```text
scripts/migrate/build_questions_from_tagged.js
data/questions/questions.jsonl
data/questions/question_sources.jsonl
scripts/lib/hash.js
scripts/lib/question_store.js
```

验收标准：

```text
questions.jsonl 题目数 = note_tagged 中有效题展开数
每个 question 都能追溯 source_note_id
query_tagged.js 可以选择从 questions.jsonl 查询
```

---

## M2：Taxonomy 单一事实源

交付物：

```text
config/taxonomy.json
scripts/lib/taxonomy.js
schemas/tagged_question.schema.json
```

验收标准：

```text
normalize_tags.js 不再内置枚举
xhs_tagger/SKILL.md 引用 taxonomy 文档
所有 tagged question 都能通过 taxonomy 校验
```

---

## M3：索引层

交付物：

```text
scripts/build_index.js
data/indexes/entity_index.json
data/indexes/company_index.json
data/indexes/domain_index.json
data/indexes/hotspot_index.json
```

验收标准：

```text
实体查询不再扫描所有 note_tagged
company/domain/hotspot 可从 index 读取
索引可重建、可校验、可 diff
```

---

## M4：Canonical Question

交付物：

```text
data/questions/canonical_questions.jsonl
scripts/migrate/build_canonical_questions.js
scripts/commands/canonical.js
```

验收标准：

```text
Top 50 高频实体有 canonical 聚类候选
至少 100 个 question 绑定 canonical_id
hotspot 以 canonical_id 统计
```

---

## M5：复习闭环

交付物：

```text
review/answers/{canonical_id}.md
review/progress.json
review/sessions/{date}.json
review/plans/{date}.md
scripts/lib/review_scheduler.js
scripts/commands/review.js
```

验收标准：

```text
能生成 7 天复习计划
能标记 mastered/learning/weak
能按 weak list 生成下一次复习任务
答案绑定 canonical_id
```

---

## M6：Pipeline 状态机

交付物：

```text
scripts/commands/pipeline.js
data/manifests/pipeline_runs/*.json
```

验收标准：

```text
每次 run 有 manifest
每个 note/question 有状态
失败可重试
validate/index/review 都可独立执行
```

---

# 7. 最小可行 PoC

建议先开一个小 PoC，不动历史目录结构。

## PoC 范围

```text
输入：note_tagged/*.json
输出：
- data/questions/questions.jsonl
- data/questions/question_sources.jsonl
- data/indexes/entity_index.json
- data/indexes/domain_index.json
- data/indexes/company_index.json
```

## PoC 脚本

```text
scripts/migrate/build_questions_from_tagged.js
scripts/build_index.js
scripts/xhs.js
```

## PoC 命令

```bash
node scripts/migrate/build_questions_from_tagged.js
node scripts/build_index.js
node scripts/xhs.js query entity Redis --valid
node scripts/xhs.js query company 美团 --level 社招
```

## PoC 验收指标

```text
1. questions.jsonl 可稳定重建
2. question_id 不漂移
3. entity 查询结果与 query_tagged.js 结果一致或可解释
4. build_index 可重复执行且输出稳定
5. 新查询入口比旧入口逻辑更薄
```

---

# 8. 关键设计决策

## ADR-001：短期使用 JSONL 作为主数据层

决策：使用 `questions.jsonl` 和 `canonical_questions.jsonl` 作为 Phase 1 主数据。

理由：

```text
当前数据量不大
Git 友好
实现成本低
可读性强
后续容易导入 SQLite
```

不选 SQLite 作为第一步，是因为现阶段最重要的是重构数据模型，而不是优化查询性能。

## ADR-002：canonical_id 绑定答案和复习进度

决策：答案和复习进度不直接绑定原始 question_id，而绑定 canonical_id。

理由：

```text
同义题共享一份核心答案
复习的是知识点，不是原文句子
热点统计需要按题簇计算
```

## ADR-003：taxonomy 放入 config，不再散落在 Prompt 和脚本中

决策：新增 `config/taxonomy.json`。

理由：

```text
Prompt 应该消费标准，不应该定义标准
脚本校验需要稳定枚举
复习计划需要稳定领域层级
```

## ADR-004：Agent 只生成候选，脚本决定入库

决策：Agent 生成结构化、标签、答案、canonical title 候选；脚本负责校验和状态推进。

理由：

```text
可复现
可测试
可回滚
可持续运行
```

---

# 9. 成功指标

## 数据层指标

```text
questions.jsonl 覆盖率：100% 展开 note_tagged 中所有 tagged_questions
question_id 稳定性：历史 hash 快照 100% 不变
taxonomy 校验通过率：>= 99%
空题原因覆盖率：100% 有 status_reason
```

## 查询层指标

```text
entity 查询耗时下降
company/domain/hotspot 查询不再全量扫描 note_tagged
索引可重复生成，diff 稳定
```

## 知识资产指标

```text
Top 50 高频实体完成 canonical 聚类
Top 200 canonical questions 有 review_priority
P0 高频题有深度答案
```

## 复习系统指标

```text
能生成每日复习 session
能记录 mastered/learning/weak
能根据 weak list 自动生成下一轮计划
```

---

# 10. 最终建议

从价值导向看，当前最重要的不是继续扩采集，也不是先把所有脚本重写，而是先建立题库底座。

推荐立即执行：

```text
第一步：build_questions_from_tagged
第二步：build_index
第三步：canonical_questions PoC
第四步：review_progress PoC
```

一句话总结：

```text
SourceNote 只是输入
Question 才是核心
CanonicalQuestion 是知识资产
Index 是查询能力
Answer 是复习内容
ReviewProgress 是最终闭环
```

这个方向一旦打通，后续无论数据来自小红书、牛客、面试记录还是手工录入，都能进入同一套高价值面试训练系统。

---

# 参考资料

- JSON Lines: https://jsonlines.org/
- SQLite FTS5: https://www.sqlite.org/fts5.html
- SQLite JSON functions: https://www.sqlite.org/json1.html
- Node.js test runner: https://nodejs.org/api/test.html
- DuckDB Node.js client note: https://duckdb.org/docs/stable/clients/nodejs/overview
