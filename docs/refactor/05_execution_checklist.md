# 05 执行清单与验收标准

> 本文把长期重构拆成可执行任务清单，方便逐项推进、验证和复盘。

---

## 1. 使用方式

每个任务都包含：

```text
目标
任务
验收标准
状态
```

建议状态：

```text
TODO
IN_PROGRESS
DONE
BLOCKED
DEFERRED
```

---

## 2. M0：文档与设计冻结

## 2.1 需求文档

状态：DONE

任务：

```text
编写 docs/refactor/01_requirements.md
明确长期业务目标
明确核心使用场景
明确非目标
明确成功指标
```

验收：

```text
目标不是采集面经，而是面试知识资产系统
P0 使用场景包含目标准备、专项突破、高频发现、复习闭环
```

## 2.2 领域模型文档

状态：DONE

任务：

```text
编写 docs/refactor/02_domain_model.md
定义 SourceNote / Question / CanonicalQuestion / Answer / ReviewProgress
定义对象关系
定义数据生命周期
```

验收：

```text
Question 被定义为主数据
CanonicalQuestion 被定义为知识资产
Answer 和 ReviewProgress 绑定 canonical_id
```

## 2.3 技术方案文档

状态：DONE

任务：

```text
编写 docs/refactor/03_technical_design.md
定义分层架构
定义存储/索引方案
定义 AI / Skill 边界
定义迁移和校验机制
```

## 2.4 重构计划文档

状态：DONE

任务：

```text
编写 docs/refactor/04_refactor_plan.md
定义 M1-M8 里程碑
定义每个里程碑交付物和验收标准
```

---

## 3. M1：Question 主数据层

## 3.1 抽取 hash 工具

状态：TODO

任务：

```text
新增 scripts/lib/hash.js
导出 normalizeQuestion(text)
导出 computeQuestionId(text)
```

验收：

```text
generate_hashes.js 可复用该模块
xhs_pipeline.js 可复用该模块
validate_tagged.js 可复用该模块
check_consistency.js 可复用该模块
历史 question_id 不漂移
```

## 3.2 增加 JSONL IO 工具

状态：TODO

任务：

```text
新增 scripts/lib/io.js
支持 readJsonl(path)
支持 writeJsonl(path, records)
支持 ensureDir(path)
支持 stableStringify(record)
```

验收：

```text
输出排序稳定
重复运行结果稳定
空文件和不存在文件有明确行为
```

## 3.3 构建 questions.jsonl

状态：TODO

任务：

```text
新增 scripts/migrate/build_questions_from_tagged.js
读取 note_tagged/*.json
展开 tagged_questions
生成 data/questions/questions.jsonl
生成 data/questions/question_sources.jsonl
```

验收：

```text
questions.jsonl 行数 = 所有 tagged_questions 展开数量
每行有 question_id
每行有 source_note_id
每行保留 company / position / round / level / year
重复执行输出一致
```

## 3.4 增加 question_store

状态：TODO

任务：

```text
新增 scripts/lib/question_store.js
支持 loadQuestions()
支持 findById(questionId)
支持 filterQuestions(filters)
```

验收：

```text
query 命令可以复用
review_scheduler 可以复用
build_index 可以复用
```

---

## 4. M2：Taxonomy / Schema

## 4.1 提取 taxonomy

状态：TODO

任务：

```text
新增 config/taxonomy.json
定义 domain_l1
定义 domain_l2_by_l1
定义 question_types
定义 cognitive_depths
定义 entity_synonyms
```

验收：

```text
taxonomy 覆盖当前 xhs_tagger 中的枚举
taxonomy 能表达 normalize_tags 中的历史映射
```

## 4.2 增加 taxonomy 工具

状态：TODO

任务：

```text
新增 scripts/lib/taxonomy.js
支持 validateDomain(domain)
支持 validateQuestionType(type)
支持 validateCognitiveDepth(depth)
支持 normalizeEntity(entity)
```

验收：

```text
validate 命令可调用
query/review 不再硬编码 taxonomy
```

## 4.3 增加 schema

状态：TODO

任务：

```text
新增 schemas/question.schema.json
新增 schemas/canonical_question.schema.json
新增 schemas/review_progress.schema.json
```

验收：

```text
validate schema 能检查字段完整性
schema_version 字段存在
```

## 4.4 增加 validate 命令

状态：TODO

任务：

```text
新增 scripts/commands/validate.js
支持 validate schema
支持 validate taxonomy
支持 validate hash
支持 validate all
```

验收：

```text
能输出错误数量
能输出问题记录 ID
支持 CI 调用
```

---

## 5. M3：索引层

## 5.1 构建 entity index

状态：TODO

任务：

```text
读取 questions.jsonl
按 tech_entities 构建 data/indexes/entity_index.json
```

验收：

```text
Redis / MySQL / HashMap 等实体可查到 question_id 列表
输出排序稳定
```

## 5.2 构建 company index

状态：TODO

任务：

```text
按 company 构建 data/indexes/company_index.json
```

验收：

```text
美团 / 字节 / 百度等公司可查到题目列表
```

## 5.3 构建 domain index

状态：TODO

任务：

```text
按 domain.l1/domain.l2 构建 data/indexes/domain_index.json
```

验收：

```text
数据库/MySQL、Java基础/JVM 等可查
```

## 5.4 构建基础 hotspot index

状态：TODO

任务：

```text
第一阶段按 question_id 统计
第二阶段按 canonical_id 统计
```

验收：

```text
能输出 Top N 高频题
支持 company/domain/entity 过滤
```

## 5.5 新 query 命令

状态：TODO

任务：

```text
新增 scripts/commands/query.js
支持 query entity
支持 query company
支持 query domain
支持 query hotspot
```

验收：

```text
查询读取 indexes 和 questions.jsonl
不再直接扫描 note_tagged
```

---

## 6. M4：CanonicalQuestion

## 6.1 设计 canonical 数据文件

状态：TODO

任务：

```text
新增 data/questions/canonical_questions.jsonl
定义 canonical_id / canonical_title / aliases / question_ids / frequency / companies
```

验收：

```text
schema 校验通过
question_ids 均存在于 questions.jsonl
```

## 6.2 实现 canonical suggest

状态：TODO

任务：

```text
根据 entity/domain/token overlap 生成候选题簇
可选调用 AI 生成 canonical_title 候选
```

验收：

```text
node scripts/xhs.js canonical suggest --entity HashMap 可输出候选簇
```

## 6.3 实现 canonical merge

状态：TODO

任务：

```text
支持 merge 多个 question_id
写入 canonical_questions.jsonl
回填 questions.jsonl 中 canonical_id
```

验收：

```text
merge 可重复检查
重复 merge 不产生重复 question_id
```

## 6.4 实现 canonical split

状态：TODO

任务：

```text
支持从 canonical 中拆出 question_id
更新 canonical frequency
更新 questions.jsonl canonical_id
```

验收：

```text
split 后 validate canonical 通过
```

---

## 7. M5：Answer 答案资产层

## 7.1 定义答案模板

状态：TODO

任务：

```text
定义 review/answers/{canonical_id}.md 模板
包括 1 分钟版 / 3 分钟版 / 原理机制 / 项目经验版 / 追问 / 易错点
```

验收：

```text
所有新生成答案结构一致
```

## 7.2 实现 answer generate

状态：TODO

任务：

```text
新增 scripts/commands/answer.js
支持 answer generate --canonical-id
支持 answer batch --priority P0 --limit N
```

验收：

```text
答案绑定 canonical_id
已有答案默认不覆盖
```

## 7.3 答案元数据

状态：TODO

任务：

```text
新增 review/answers/metadata.json
记录 canonical_id / answer_path / version / generator / updated_at
```

验收：

```text
可查询某个 canonical 是否已有答案
可知道答案版本
```

---

## 8. M6：Review 复习闭环

## 8.1 review strategy

状态：TODO

任务：

```text
新增 config/review_strategy.json
定义 priority score 权重
定义 P0/P1/P2 策略
```

验收：

```text
prepare 和 review_scheduler 从配置读取策略
```

## 8.2 review progress

状态：TODO

任务：

```text
新增 review/progress.json
记录 canonical_id 状态
```

验收：

```text
支持 new / learning / weak / mastered / archived
```

## 8.3 review scheduler

状态：TODO

任务：

```text
新增 scripts/lib/review_scheduler.js
根据 priority score 生成 sessions
```

验收：

```text
weak 题优先进入下一轮
mastered 题权重下降
高频 P0 题优先
```

## 8.4 prepare 命令

状态：TODO

任务：

```text
新增 scripts/commands/prepare.js
支持 --company / --topic / --level / --days
生成 review/plans 和 review/sessions
```

验收：

```text
输入目标后可生成可执行复习计划
```

## 8.5 review 命令

状态：TODO

任务：

```text
支持 review today
支持 review mark --status
支持 review weak
支持 review next
```

验收：

```text
用户可以持续记录掌握度
系统可以持续调整后续计划
```

---

## 9. M7：Pipeline / Migration / ADR

## 9.1 pipeline manifest

状态：TODO

任务：

```text
新增 data/manifests/pipeline_runs/
每次 pipeline run 写入 run_id / steps / counts / errors
```

验收：

```text
失败可定位
成功可复盘
```

## 9.2 migration runner

状态：TODO

任务：

```text
新增 scripts/lib/migration_runner.js
支持 migrate status / up / apply
```

验收：

```text
每次 schema/taxonomy 变更有 migration
migration 执行有 manifest
```

## 9.3 ADR

状态：TODO

任务：

```text
新增 docs/adr/
至少添加：
001-question-centric-architecture.md
002-jsonl-primary-store.md
003-canonical-question-as-knowledge-asset.md
004-ai-as-candidate-generator.md
```

验收：

```text
关键设计决策可追溯
```

---

## 10. M8：工程化完善

## 10.1 package.json

状态：TODO

任务：

```text
新增 package.json
定义 npm scripts
```

建议命令：

```json
{
  "scripts": {
    "test": "node --test",
    "validate": "node scripts/xhs.js validate all",
    "index": "node scripts/xhs.js index build",
    "check": "npm run test && npm run validate"
  }
}
```

## 10.2 tests

状态：TODO

任务：

```text
新增 test/hash.test.js
新增 test/taxonomy.test.js
新增 test/build_questions.test.js
新增 test/build_index.test.js
新增 test/review_scheduler.test.js
```

## 10.3 CI

状态：TODO

任务：

```text
新增 .github/workflows/ci.yml
运行 node --test
运行 validate all
运行 index build --check
```

## 10.4 README 更新

状态：TODO

任务：

```text
README 改为推荐 node scripts/xhs.js 统一入口
旧脚本放入 Legacy 章节
```

---

## 11. 每次迭代的固定检查

```text
1. 是否破坏 question_id 稳定性？
2. 是否引入新的 taxonomy 值？
3. 是否需要 schema migration？
4. 是否需要 rebuild index？
5. 是否影响 canonical_id？
6. 是否影响 answer 绑定？
7. 是否影响 review progress？
8. 是否有 validate/test 覆盖？
```

---

## 12. 第一轮建议执行任务

建议立即开始：

```text
[ ] scripts/lib/hash.js
[ ] scripts/lib/io.js
[ ] scripts/migrate/build_questions_from_tagged.js
[ ] data/questions/questions.jsonl
[ ] data/questions/question_sources.jsonl
[ ] scripts/xhs.js validate questions
```

这 6 项完成后，系统就有了长期可迭代的主数据底座。
