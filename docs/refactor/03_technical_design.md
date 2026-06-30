# 03 技术方案

> 本文定义长期重构的技术架构、存储方案、索引方案、AI/Skill 边界、校验机制和迁移策略。

---

## 1. 技术目标

技术目标不是单纯“重写脚本”，而是建立一套长期可循环的系统内核：

```text
可重建主数据
可重建索引
可校验标签
可追溯题簇
可版本化答案
可持续复习
可渐进迁移旧系统
```

最终技术形态：

```text
Legacy note_tagged
  ↓ adapter / migrate
Question Store
  ↓ build index
Index Store
  ↓ canonical
Canonical Store
  ↓ answer / review
Review System
```

---

## 2. 总体架构

```text
┌──────────────────────────────────────────────┐
│ Application Layer                            │
│ prepare / query / review / answer / canonical│
├──────────────────────────────────────────────┤
│ Review Layer                                 │
│ answers / progress / sessions / scheduler    │
├──────────────────────────────────────────────┤
│ Knowledge Layer                              │
│ canonical questions / aliases / hotspots     │
├──────────────────────────────────────────────┤
│ Index Layer                                  │
│ entity / company / domain / hotspot indexes  │
├──────────────────────────────────────────────┤
│ Data Layer                                   │
│ questions.jsonl / sources / schemas          │
├──────────────────────────────────────────────┤
│ Legacy Adapter + AI Adapter                  │
│ note_tagged / skills / extract / tag / answer│
└──────────────────────────────────────────────┘
```

---

## 3. 推荐目录结构

```text
xhs/
├── config/
│   ├── taxonomy.json
│   ├── review_strategy.json
│   └── pipeline.json
├── schemas/
│   ├── source_note.schema.json
│   ├── question.schema.json
│   ├── canonical_question.schema.json
│   ├── answer.schema.json
│   └── review_progress.schema.json
├── scripts/
│   ├── xhs.js
│   ├── commands/
│   │   ├── ingest.js
│   │   ├── migrate.js
│   │   ├── index.js
│   │   ├── query.js
│   │   ├── canonical.js
│   │   ├── answer.js
│   │   ├── prepare.js
│   │   ├── review.js
│   │   └── validate.js
│   ├── lib/
│   │   ├── hash.js
│   │   ├── io.js
│   │   ├── schema.js
│   │   ├── taxonomy.js
│   │   ├── question_store.js
│   │   ├── canonical_store.js
│   │   ├── index_store.js
│   │   ├── review_scheduler.js
│   │   └── migration_runner.js
│   ├── migrate/
│   │   ├── build_questions_from_tagged.js
│   │   └── build_canonical_questions.js
│   └── ai/
│       ├── extract_questions.js
│       ├── tag_questions.js
│       ├── suggest_canonical.js
│       └── generate_answer.js
├── data/
│   ├── legacy/
│   ├── sources/
│   ├── questions/
│   ├── indexes/
│   └── manifests/
├── review/
│   ├── answers/
│   ├── sessions/
│   ├── plans/
│   ├── mistakes/
│   └── progress.json
├── docs/
└── test/
```

---

## 4. 存储方案

## 4.1 Phase 1：JSONL + JSON Index

第一阶段使用：

```text
data/questions/questions.jsonl
data/questions/question_sources.jsonl
data/questions/canonical_questions.jsonl
data/indexes/*.json
```

理由：

```text
实现快
Git 友好
可读性强
可 diff
可重建
适合当前题库规模
后续可迁移 SQLite
```

## 4.2 Phase 2：SQLite + FTS

当 JSONL/index 形成稳定结构后，可以引入：

```text
data/xhs.db
```

用途：

```text
全文搜索
复杂组合查询
快速统计
本地应用或 Web UI 查询后端
```

但不建议第一阶段直接上数据库，因为当前最重要的是领域模型和循环机制，而不是查询性能。

## 4.3 Phase 3：分析型存储可选

如果后续要做更大规模统计，可以评估 DuckDB 或其他分析引擎。

当前不作为主路径。

---

## 5. 主数据构建

## 5.1 输入

```text
note_tagged/*.json
```

## 5.2 输出

```text
data/questions/questions.jsonl
data/questions/question_sources.jsonl
data/sources/notes.jsonl
```

## 5.3 构建脚本

```bash
node scripts/migrate/build_questions_from_tagged.js
```

## 5.4 构建规则

```text
遍历 note_tagged/*.json
读取 note-level metadata
展开 tagged_questions
每道题生成一条 Question
每道题生成一条 QuestionSource
保持排序稳定
输出 JSONL
```

## 5.5 稳定性要求

```text
同样输入，多次构建输出一致
question_id 不漂移
question_sources 可追溯
无效空题 note 可记录 status_reason
```

---

## 6. Hash 方案

统一实现：

```text
scripts/lib/hash.js
```

接口：

```js
normalizeQuestion(text): string
computeQuestionId(text): string
```

规则：

```text
转小写
移除非 \w 和中文字符
MD5
```

要求：

```text
generate_hashes.js
xhs_pipeline.js
validate_tagged.js
check_consistency.js
build_questions_from_tagged.js
全部调用同一实现
```

---

## 7. Taxonomy 方案

## 7.1 单一事实源

```text
config/taxonomy.json
```

包含：

```text
domain_l1
domain_l2_by_l1
question_types
cognitive_depths
entity_synonyms
review_priority_rules
```

## 7.2 使用方

```text
xhs_tagger Skill
normalize_tags.js
query command
validate command
review scheduler
README / docs/taxonomy.md
```

## 7.3 原则

```text
Prompt 不定义标准，只引用标准
脚本不硬编码标准，只读取 taxonomy
历史数据偏离标准时输出 quality report
```

---

## 8. Schema 方案

## 8.1 Schema 文件

```text
schemas/question.schema.json
schemas/canonical_question.schema.json
schemas/review_progress.schema.json
schemas/answer.schema.json
```

## 8.2 校验命令

```bash
node scripts/xhs.js validate schema
node scripts/xhs.js validate taxonomy
node scripts/xhs.js validate hash
node scripts/xhs.js validate all
```

## 8.3 校验内容

```text
字段完整性
枚举合法性
question_id 与 original_question 一致
canonical_id 存在性
answer_path 存在性
review_progress 状态合法
```

---

## 9. 索引方案

## 9.1 Index 输入

```text
questions.jsonl
canonical_questions.jsonl
review/progress.json
```

## 9.2 Index 输出

```text
data/indexes/entity_index.json
data/indexes/company_index.json
data/indexes/domain_index.json
data/indexes/hotspot_index.json
data/indexes/review_index.json
```

## 9.3 示例

```json
{
  "Redis": ["q1", "q2", "q3"],
  "HashMap": ["q4", "q5"]
}
```

## 9.4 构建命令

```bash
node scripts/xhs.js index build
node scripts/xhs.js index check
```

## 9.5 查询策略

第一阶段：

```text
query 读取 questions.jsonl + indexes
```

第二阶段：

```text
query 可切换 SQLite/FTS
```

---

## 10. Canonical 方案

## 10.1 构建思路

```text
规则召回候选
  ↓
AI 辅助判断同义
  ↓
人工或脚本确认
  ↓
写入 canonical_questions.jsonl
```

## 10.2 候选召回规则

```text
同 domain.l2
共享 tech_entities
题干 token overlap 高
实体同义词归一化后接近
问题模板接近
```

## 10.3 命令

```bash
node scripts/xhs.js canonical suggest --entity HashMap
node scripts/xhs.js canonical merge --ids q1,q2,q3 --title "HashMap 为什么线程不安全？"
node scripts/xhs.js canonical split --canonical-id cq_xxx --ids q2
node scripts/xhs.js canonical stats
```

## 10.4 数据规则

```text
canonical merge 必须可追溯
canonical split 必须可执行
answer 和 review_progress 绑定 canonical_id
hotspot 以 canonical_id 统计
```

---

## 11. Answer 方案

## 11.1 路径

```text
review/answers/{canonical_id}.md
```

## 11.2 生成命令

```bash
node scripts/xhs.js answer generate --canonical-id cq_hashmap_thread_safety
node scripts/xhs.js answer batch --priority P0 --limit 50
node scripts/xhs.js answer improve --canonical-id cq_xxx
```

## 11.3 答案结构

```text
1 分钟面试版
3 分钟深入版
原理机制
项目经验版
高频追问
易错点
```

## 11.4 版本规则

```text
默认不覆盖已有答案
可生成 answer metadata
支持 improve 生成新版本
答案绑定 canonical_id
```

---

## 12. Review 方案

## 12.1 数据文件

```text
review/progress.json
review/sessions/{date}.json
review/plans/{target}.md
```

## 12.2 命令

```bash
node scripts/xhs.js prepare --company 美团 --level 社招 --days 10
node scripts/xhs.js review today
node scripts/xhs.js review mark cq_xxx --status mastered
node scripts/xhs.js review weak
node scripts/xhs.js review next
```

## 12.3 调度公式第一版

```text
score =
  frequency_weight
+ target_company_weight
+ not_reviewed_weight
+ weak_status_weight
+ cognitive_depth_weight
+ answer_ready_weight
```

## 12.4 状态规则

```text
new       新题
learning 练习中
weak      薄弱题
mastered  已掌握
archived  暂不复习
```

---

## 13. AI / Skill 边界

## 13.1 AI 负责

```text
从非结构化原文提取题目候选
给题目打标签候选
判断 canonical 合并候选
生成 canonical_title 候选
生成答案内容
```

## 13.2 代码负责

```text
question_id 生成
schema 校验
taxonomy 校验
索引构建
高频统计
复习调度
状态推进
入库决策
```

## 13.3 原则

```text
AI 生成候选
代码决定入库
Prompt 不是标准
Skill 不是状态机
```

---

## 14. Pipeline 方案

## 14.1 状态机

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

## 14.2 Manifest

每次运行写入：

```text
data/manifests/pipeline_runs/{run_id}.json
```

记录：

```text
input_count
success_count
failed_count
changed_records
output_paths
error_summary
```

---

## 15. 迁移方案

## 15.1 迁移原则

```text
不破坏旧目录
先新增新数据层
新旧查询并行一段时间
迁移脚本可重复执行
迁移结果可校验
```

## 15.2 Migration Runner

命令：

```bash
node scripts/xhs.js migrate status
node scripts/xhs.js migrate up
node scripts/xhs.js migrate apply 001_build_questions
```

记录：

```text
data/manifests/migrations/*.json
```

---

## 16. 测试与 CI

## 16.1 测试目录

```text
test/hash.test.js
test/taxonomy.test.js
test/build_questions.test.js
test/build_index.test.js
test/review_scheduler.test.js
```

## 16.2 最小命令

```bash
node --test
node scripts/xhs.js validate all
node scripts/xhs.js index build --check
```

---

## 17. 第一阶段最小技术闭环

```text
note_tagged/*.json
  ↓ build_questions_from_tagged
questions.jsonl
  ↓ build_index
entity/company/domain indexes
  ↓ query
canonical suggest
  ↓ merge
canonical_questions.jsonl
  ↓ prepare
review plan + sessions
```

这条链路跑通后，再逐步重构旧脚本和 Skill。
