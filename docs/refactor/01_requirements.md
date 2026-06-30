# 01 业务目标与需求定义

> 本文定义 `xhs` 长期重构的业务目标、核心使用场景、系统边界、成功标准。技术方案不在本文展开。

---

## 1. 背景

当前仓库已经具备以下能力雏形：

```text
采集面经 → 提取正文/图片 → AI 提取题目 → 结构化 JSON → 多维标签 JSON → 查询/统计 → 批量答案分析
```

但当前系统仍然偏“脚本和过程产物集合”，长期问题是：

```text
题目没有成为主数据
同义题没有统一题簇
标签体系不够收敛
查询依赖实时扫描历史 JSON
答案和复习进度没有稳定绑定对象
每轮处理依赖 Agent/Skill 行为，缺少可重跑状态机
```

因此需要从业务目标重新梳理，而不是直接开始改代码。

---

## 2. 长期业务目标

长期目标：

> 构建一个可长期迭代的面试知识资产系统，持续吸收面经数据，沉淀高频标准题簇，生成深度答案，并根据用户复习反馈形成训练闭环。

这意味着本项目的目标不是：

```text
持续采集更多原始面经
维护一组临时查询脚本
生成一次性的复习 Markdown
```

而是：

```text
把零散面经转化为稳定题库
把原始题目归并为标准题簇
把题簇转化为可复用答案
把答案纳入复习计划
把复习反馈反哺下一轮计划
```

---

## 3. 核心价值公式

系统价值由以下因素决定：

```text
最终价值 = 题目质量 × 高频准确度 × 标签稳定性 × 答案深度 × 复习闭环
```

因此：

```text
题多但重复混乱，价值低
题有标签但标签漂移，价值低
题有答案但无法复用，价值低
有计划但无法跟踪掌握度，价值低
有 AI 生成但没有校验，价值不可持续
```

---

## 4. 一级使用场景

## 4.1 目标面试准备

用户输入：

```text
公司：美团
岗位：Java后端
层级：社招
周期：10 天
```

系统输出：

```text
公司/岗位高频画像
Top canonical questions
10 天复习计划
每日 review session
P0 高频题答案
初始 review_progress
```

理想命令：

```bash
node scripts/xhs.js prepare --company 美团 --position Java后端 --level 社招 --days 10
```

---

## 4.2 技术专项突破

用户输入：

```text
Redis / MySQL / JVM / JUC / Spring / MQ / 系统设计
```

系统输出：

```text
该技术方向的高频 canonical questions
按认知深度 L1/L2/L3 排序
对应公司来源和出现频次
已有答案和待生成答案
专项复习计划
```

理想命令：

```bash
node scripts/xhs.js prepare --topic Redis --days 3
```

---

## 4.3 高频题发现

用户想知道：

```text
后端面试最常考的 100 个标准问题是什么？
某个技术方向真正高频的问题有哪些？
哪些题在多家公司重复出现？
```

系统输出：

```text
canonical_id
canonical_title
frequency
companies
entities
review_priority
answer_status
review_status
```

理想命令：

```bash
node scripts/xhs.js query hotspot --canonical --limit 100
```

---

## 4.4 深度答案生成

用户希望对高频题生成可面试表达的答案。

答案形态：

```text
1 分钟面试版
3 分钟深入版
原理机制
项目经验版
高频追问
易错点
```

答案应该绑定 `canonical_id`，而不是绑定某一个原始 `question_id`。

---

## 4.5 每日复习闭环

用户每天打开系统时，系统直接告诉他：

```text
今天新刷哪些题？
哪些题需要复刷？
哪些题是 weak？
哪些题已经 mastered？
下一轮应该怎么调整？
```

理想命令：

```bash
node scripts/xhs.js review today
node scripts/xhs.js review mark cq_hashmap_thread_safety --status mastered
node scripts/xhs.js review weak
```

---

## 4.6 增量面经吸收

每新增一批面经，系统应该能够：

```text
提取新题
识别已有 canonical question
新增 question source
更新题簇频次
更新公司画像
更新复习优先级
触发答案补齐
```

新增数据的价值不是“多了一篇 note”，而是：

```text
某个 canonical question 的频次 +1
某个公司画像更准确
某个知识点优先级上升
```

---

## 5. 非目标

第一阶段不追求：

```text
重写所有采集脚本
一次性迁移所有旧目录
立即引入复杂数据库
一次性全自动 canonical 聚类
一次性生成所有题目的答案
立即做 Web UI
```

长期目标是循环迭代，不是一次性大爆炸重写。

---

## 6. 系统边界

## 6.1 系统内核

系统内核必须稳定、可测试、可复现：

```text
question_id 生成
schema 校验
taxonomy 校验
questions.jsonl 构建
index 构建
canonical 存储
review progress 更新
```

## 6.2 AI / Skill 边界

AI 和 Skill 负责语义候选：

```text
题目提取候选
标签候选
canonical 合并建议
答案生成
```

代码负责最终入库：

```text
校验
去重
状态推进
索引重建
版本记录
```

---

## 7. 成功指标

## 7.1 数据指标

```text
questions.jsonl 覆盖 note_tagged 中所有有效题
question_id 100% 稳定不漂移
所有 question 都能追溯 source_note_id
所有标签都能被 taxonomy 校验
```

## 7.2 知识资产指标

```text
Top 50 高频实体完成 canonical 候选聚类
至少 100 个 question 绑定 canonical_id
hotspot 以 canonical_id 统计
P0 canonical questions 有答案
```

## 7.3 复习指标

```text
能生成目标公司/技术方向复习计划
能生成每日 review session
能标记 mastered / learning / weak
weak 题能进入下一轮复习
```

## 7.4 工程指标

```text
核心数据可重建
核心命令幂等
每次 schema/taxonomy 变更有 migration
每次提交能 validate
旧脚本可逐步淘汰
```

---

## 8. 需求优先级

```text
P0：Question 主数据层
P0：Taxonomy / Schema 单一事实源
P0：Index 构建和查询
P1：CanonicalQuestion 题簇层
P1：Answer 绑定 canonical_id
P1：ReviewProgress 和 ReviewSession
P2：Pipeline 状态机
P2：Migration Runner / CI / ADR
P3：SQLite / Web UI / 知识图谱可视化
```

---

## 9. 一句话需求定义

```text
用户输入面试目标，系统基于长期积累的标准题簇和复习状态，生成高价值复习计划、深度答案和每日训练任务，并在每次新增数据和用户反馈后持续迭代。
```
