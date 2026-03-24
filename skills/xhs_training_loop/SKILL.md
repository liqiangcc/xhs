---
name: xhs_training_loop
description: "训练闭环总控：把 note 筛选、开始训练、评分追问、回炉分桶、复盘落盘串成一套稳定流程。适用于：刚刷完一篇 note 需要固化结果；想从 note_selection 无缝进入 practice；想把 same_day/next_day/day3/day7 回炉计划写入 review/。"
---

# XHS Training Loop

## 目标

这个 skill 负责把下面几件事串起来，形成稳定闭环：

1. 选训练上下文（复用 `xhs_note_selector`）
2. 启动训练（复用 `xhs_practice_sop`）
3. 在会话中维护 `question_progress / note_progress / session_progress`
4. 结束一轮 note 后输出回炉队列
5. 按统一格式把结果写入 `review/`，避免会话结束后丢失

---

## 适用场景

### 1. 刚筛完 note，想直接进入训练
- 用户已经有 `note_id` 或 note-selection handoff payload
- 目标：无缝进入 `single_note_review`

### 2. 刚练完一篇 note，想固化结果
- 用户已经完成若干题训练
- 目标：生成回炉清单、次日复述提纲、阶段总结并落盘

### 3. 想按回炉队列继续推进
- 用户说“继续昨天的 same_day_queue”
- 目标：优先回炉，再决定是否继续当前 note 或切下一个 note

---

## 输入优先级

优先消费以下输入：

1. `xhs-note-selection.prompt.md` 的 handoff payload
2. 用户直接给的 `note_id`
3. 当前会话里已经完成的 note 训练结果
4. 如果都没有，再走 `xhs_note_selector`

---

## 核心流程

### Step 0：确认当前阶段
先判断用户当前想做哪一种动作：

- `start_from_selection`：从选 note 进入训练
- `continue_practice`：继续当前 note 训练
- `solidify_result`：固化本轮训练结果
- `rework_review`：按回炉队列复习

如果用户表达模糊，优先根据最近上下文做最小推断，不要重复问太多。

### Step 1：进入训练或读取当前进度
- 如果是新 note：读取 note 元数据，进入 `single_note_review`
- 如果是继续训练：延续当前 note_progress
- 如果是回炉：优先同一 note 的 `same_day_queue > next_day_queue > day3_queue > day7_queue`

### Step 2：训练执行规范
复用 `xhs_practice_sop`（**包括其资深候选人口径——评分、追问、总结均按「结论 → 原理 → 取舍 → 场景 → 边界」执行**）：
- 一次只出 1 题
- 默认先让用户回答
- 用户说“不会 / 直接分析 / 跳过”时，走对应分支
- 每题结束必须产出评分、追问结果、复盘、进度摘要

### Step 3：回炉分桶
每题结束后，至少给出：
- `same_day_queue`
- `next_day_queue`
- `day3_queue`
- `day7_queue`

默认规则：
- 跳过 / 不会 / 关键题失守 → `same_day_queue` 或 `next_day_queue`
- 10~15 分 → `day3_queue`
- 16~20 分 → `next_day_queue`
- 21~25 分 → `day7_queue`

### Step 4：note 结束时必须输出
- 当前 note 基本信息
- 已练题 / 跳过题 / 掌握题 / 回炉题
- 强项主题
- 薄弱主题
- 四级回炉清单
- 次日复述提纲
- 下一步建议（继续当前 note / 切 topic_drill / company_mock）

### Step 5：落盘规则
如果用户明确同意固化结果，写入 `review/`：

#### 建议目录
- `review/sessions/`：单次训练会话记录
- `review/queues/`：回炉队列
- `review/summary/`：阶段总结

#### 建议文件
- `review/sessions/<date>_<note_id>.md`
- `review/queues/same_day.md`
- `review/queues/next_day.md`
- `review/queues/day3.md`
- `review/queues/day7.md`
- `review/summary/<date>.md`

若对应文件不存在，可以新建；若已存在，优先追加本次结果，避免覆盖旧记录。

---

## 推荐落盘内容

### Session 文件至少包含
- 时间
- mode
- note_id / company / position / round
- question_id（每题都保留）
- 本轮练了哪些题
- 每题结论（掌握 / 模糊 / 回炉 / 跳过）
- 强项 / 薄弱项
- 推荐下一步

### Queue 文件至少包含
- note_id
- question_id
- question_text
- 进入该队列的原因
- 推荐复习时间
- 一句话复述骨架

### 训练输出建议
- 进入单题训练时，默认同时展示 `question_id` 和题目原文
- 用户要求“深度分析这题”时，优先基于 `question_id` 交给 `xhs_analyzer`
- 如果题目文本较长，也不要省略 `question_id`

### Summary 文件至少包含
- 今日完成了哪些 note
- 高频薄弱项
- 次日优先事项
- 是否建议继续该公司 mock 或切专题

---

## 输出风格要求

- 主输出仍然以训练为主，不要让“记录”抢占对话
- 当用户说“先把流程走通”时，优先保证闭环，而不是追求复杂文件结构
- 当用户说“固化起来”时，优先产出最小可复用记录，而不是过度设计

---

## 与现有能力的关系

- `xhs_note_selector`：决定刷哪篇 note
- `xhs_practice_sop`：负责逐题训练
- `xhs_training_loop`：负责把训练过程和 review 落盘管理起来

---

## 推荐结束语

当一轮结束时，优先给用户下面三种下一步之一：
- `继续当前 note 下一题`
- `进入回炉快问快答`
- `固化本轮训练结果到 review/`
