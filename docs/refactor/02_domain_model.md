# 02 领域模型

> 本文定义长期重构后的核心领域对象、对象关系、数据生命周期和命名规则。

---

## 1. 领域建模原则

长期系统不应以 `note`、`script`、`Skill` 为中心，而应以面试知识资产为中心。

核心原则：

```text
SourceNote 只是输入
Question 是主数据
CanonicalQuestion 是知识资产
Answer 是复习内容
ReviewProgress 是闭环状态
PipelineRun 是可追溯过程
```

---

## 2. 当前模型问题

当前仓库的题目主要嵌在：

```text
note_tagged/{note_id}.json
```

这种模型适合按来源笔记追溯，但不适合作为长期题库主表。

问题：

```text
查询需要反复 flatten note_tagged
同一道题的多个来源难以表达
同义题无法稳定归并
答案难以复用
复习进度难以绑定
```

因此需要新增 question-centric 模型。

---

## 3. 核心领域对象

```text
SourceNote
Question
QuestionSource
CanonicalQuestion
Answer
ReviewProgress
ReviewSession
Taxonomy
PipelineRun
Migration
```

对象关系：

```text
SourceNote 1 ── N QuestionSource N ── 1 Question
Question N ── 1 CanonicalQuestion
CanonicalQuestion 1 ── N AnswerVersion
CanonicalQuestion 1 ── 1 ReviewProgress
ReviewSession N ── N CanonicalQuestion
Taxonomy 约束 Question / CanonicalQuestion
PipelineRun 记录数据处理过程
Migration 记录结构演进过程
```

---

## 4. SourceNote

## 4.1 定义

来源笔记，用于记录面经来源和上下文。

SourceNote 不再承担题库职责，只负责溯源。

## 4.2 字段

```json
{
  "note_id": "65a0d1d8000000001e0081ae",
  "source": "小红书",
  "company": "百度",
  "position": "高级开发工程师",
  "round": "未知",
  "level": "社招",
  "year": "未知",
  "date": "未知",
  "status": "tagged",
  "question_count": 1,
  "schema_version": "source_note.v1",
  "created_at": "2026-06-30",
  "updated_at": "2026-06-30"
}
```

## 4.3 状态枚举

```text
raw
desc_ready
ocr_ready
structured_ready
tagged_ready
validated
indexed
skipped_invalid
failed
```

---

## 5. Question

## 5.1 定义

Question 是题库主数据，表示一个原始面试题。

它保留原始问法，不强行改写成标准题。

## 5.2 字段

```json
{
  "question_id": "4068b82fcdc6c006604e375a5fccaa02",
  "original_question": "master选举的过程？",
  "source_note_id": "65a0d1d8000000001e0081ae",
  "company": "百度",
  "position": "高级开发工程师",
  "round": "未知",
  "level": "社招",
  "year": "未知",
  "date": "未知",
  "domain": {
    "l1": "系统设计",
    "l2": "分布式架构"
  },
  "question_type": "原理深度_UnderTheHood",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": ["master选举", "选主算法"],
  "business_context": [],
  "is_valid_for_library": true,
  "canonical_id": null,
  "schema_version": "question.v1",
  "taxonomy_version": "taxonomy.v1"
}
```

## 5.3 ID 规则

```text
question_id = hash(normalized_original_question)
```

要求：

```text
稳定
确定性
不依赖大模型
所有脚本共用 scripts/lib/hash.js
历史题目不漂移
```

---

## 6. QuestionSource

## 6.1 定义

QuestionSource 表示题目和来源笔记之间的关系。

一个 Question 可能来自多个 SourceNote；一个 SourceNote 可以贡献多道 Question。

## 6.2 字段

```json
{
  "question_id": "4068b82fcdc6c006604e375a5fccaa02",
  "source_note_id": "65a0d1d8000000001e0081ae",
  "company": "百度",
  "position": "高级开发工程师",
  "round": "未知",
  "level": "社招",
  "year": "未知",
  "source_weight": 1,
  "created_at": "2026-06-30"
}
```

## 6.3 价值

```text
计算公司出现频次
计算题簇热度
追溯题目来源
支持未来多数据源合并
```

---

## 7. CanonicalQuestion

## 7.1 定义

CanonicalQuestion 是标准题簇，用来聚合语义相同或高度相似的原始题目。

这是长期系统最重要的知识资产对象。

## 7.2 字段

```json
{
  "canonical_id": "cq_hashmap_thread_safety",
  "canonical_title": "HashMap 为什么线程不安全？",
  "aliases": [
    "HashMap 为什么线程不安全？",
    "HashMap 并发下有什么问题？",
    "HashMap 多线程 put 会发生什么？"
  ],
  "question_ids": ["q1", "q2", "q3"],
  "primary_domain": {
    "l1": "Java基础",
    "l2": "集合框架"
  },
  "primary_entities": ["HashMap", "并发安全", "扩容"],
  "companies": ["美团", "字节", "百度"],
  "frequency": 12,
  "review_priority": "P0",
  "answer_status": "ready",
  "schema_version": "canonical_question.v1"
}
```

## 7.3 ID 规则

第一阶段建议人工或规则命名：

```text
cq_<entity>_<topic>
```

例如：

```text
cq_hashmap_thread_safety
cq_mysql_mvcc
cq_redis_cache_breakdown
```

后续可以支持自动生成，但必须可人工修正。

## 7.4 操作

```text
suggest    生成候选题簇
merge      合并多个 question_id
split      从题簇拆出 question_id
rename     修改 canonical_title
stats      查看题簇频次
```

---

## 8. Answer

## 8.1 定义

Answer 是标准题簇的答案资产。

答案应绑定 `canonical_id`，而不是绑定单个 `question_id`。

## 8.2 文件路径

```text
review/answers/{canonical_id}.md
```

## 8.3 内容结构

```md
# HashMap 为什么线程不安全？

## 1 分钟面试版

## 3 分钟深入版

## 原理机制

## 项目经验版

## 高频追问

## 易错点
```

## 8.4 元数据

```json
{
  "canonical_id": "cq_hashmap_thread_safety",
  "answer_path": "review/answers/cq_hashmap_thread_safety.md",
  "answer_version": 1,
  "style": "senior_backend_engineer",
  "generator": "xhs_analyzer@v1",
  "created_at": "2026-06-30",
  "updated_at": "2026-06-30"
}
```

---

## 9. ReviewProgress

## 9.1 定义

ReviewProgress 记录用户对某个 CanonicalQuestion 的掌握状态。

## 9.2 字段

```json
{
  "canonical_id": "cq_hashmap_thread_safety",
  "status": "learning",
  "review_count": 3,
  "last_reviewed_at": "2026-06-30",
  "next_review_at": "2026-07-03",
  "confidence": 0.6,
  "difficulty": 4,
  "mistake_count": 1,
  "updated_at": "2026-06-30"
}
```

## 9.3 状态枚举

```text
new
learning
weak
mastered
archived
```

---

## 10. ReviewSession

## 10.1 定义

每日训练任务集合。

## 10.2 字段

```json
{
  "session_id": "2026-06-30-meituan-java",
  "date": "2026-06-30",
  "target": {
    "company": "美团",
    "position": "Java后端",
    "level": "社招"
  },
  "new_questions": ["cq_mysql_mvcc"],
  "review_questions": ["cq_hashmap_thread_safety"],
  "weak_questions": ["cq_rocketmq_reliability"],
  "created_at": "2026-06-30"
}
```

---

## 11. Taxonomy

## 11.1 定义

Taxonomy 是标签体系的单一事实源。

## 11.2 路径

```text
config/taxonomy.json
```

## 11.3 约束对象

```text
Question.domain
Question.question_type
Question.cognitive_depth
CanonicalQuestion.primary_domain
Review priority rules
```

---

## 12. PipelineRun

## 12.1 定义

记录一次数据处理运行。

## 12.2 字段

```json
{
  "run_id": "2026-06-30-001",
  "type": "ingest",
  "started_at": "2026-06-30T10:00:00+09:00",
  "finished_at": "2026-06-30T10:05:00+09:00",
  "steps": [
    {
      "name": "extract",
      "input_count": 10,
      "success_count": 8,
      "failed_count": 2
    },
    {
      "name": "tag",
      "input_count": 8,
      "success_count": 8
    },
    {
      "name": "validate",
      "input_count": 8,
      "success_count": 7,
      "needs_review_count": 1
    }
  ]
}
```

---

## 13. 数据生命周期

```text
SourceNote(raw)
  ↓
SourceNote(structured_ready)
  ↓
Question(new)
  ↓
Question(validated)
  ↓
Question(indexed)
  ↓
CanonicalQuestion(suggested)
  ↓
CanonicalQuestion(confirmed)
  ↓
Answer(ready)
  ↓
ReviewProgress(learning/mastered/weak)
```

---

## 14. 长期演进规则

```text
新增字段必须更新 schema_version
变更 taxonomy 必须提供 migration
canonical merge/split 必须可追溯
answer 不默认覆盖旧版本
review progress 不由 AI 直接写入
AI 输出只能作为 candidate，不能直接成为最终事实
```
