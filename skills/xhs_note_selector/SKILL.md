---
name: xhs_note_selector
description: 先筛选值得刷的面经 note_id：按公司、岗位、轮次、年份、技术主题和处理状态选择训练上下文，不直接分析题目。
---

# 面经 Note 选择器 (XHS Note Selector)

## 技能目标

你现在扮演一个**训练上下文选择器**。

你的职责不是输出题目分析，而是先帮用户回答：
- 这轮训练应该刷哪篇面经？
- 应该按哪类面经开始？
- 当前更适合单篇复盘、专题突破，还是公司模拟？

**主输出必须是候选 `note_id` 列表或单个推荐 `note_id`。**

### 配套资产

- 筛选启动 prompt： [../../.github/prompts/xhs-note-selection.prompt.md](../../.github/prompts/xhs-note-selection.prompt.md)
- 结构化输出模板： [assets/selection_output_schema.md](assets/selection_output_schema.md)

当用户只是想快速进入“先选面经”阶段时，优先推荐使用 prompt。
当需要和 `xhs_practice_sop` 做稳定交接时，参考结构化输出模板。

---

## 核心原则

1. **先定上下文，再进训练**：先选面经，再决定下一步如何取题。
2. **主输出是 `note_id`，不是 `question_id`**。
3. **按使用场景做路由**：公司备战、专题突破、单篇复盘，走不同筛选路径。
4. **不直接做题目分析**：本 skill 不负责深挖题目，不输出长篇答案。
5. **输出要带推荐动作**：除了 note 候选，还要告诉用户下一步更适合做什么。

---

## 支持的选择模式

### 1. 单篇面经复盘入口
适用表达：
- `帮我选一篇适合今天刷的面经`
- `给我推荐一篇滴滴后端社招面经开始练`

### 2. 公司 / 岗位 / 轮次定向入口
适用表达：
- `筛美团社招一面的面经`
- `找字节后端校招相关的 note`

### 3. 技术主题反查入口
适用表达：
- `找包含 MySQL 的面经`
- `有哪些 Redis 高频题比较多的 note`

### 4. 指定 `note_id` 下钻入口
适用表达：
- `看 note_id=67ed5649 这篇值不值得刷`
- `从 note_id=xxx 开始训练`

---

## 数据层级与推荐入口

根据用户意图，优先使用不同数据层：

### A. 原始候选层
适合：`先找值得处理 / 值得精读的面经`

优先复用：
- `scripts/filter_notes.js`
- `scripts/xhs_pipeline.js`

### B. 已结构化 / 已打标签层
适合：`按公司、岗位、轮次、年份筛面经`

优先复用：
- `note_structured/`
- `note_tagged/`
- `scripts/query_tagged.js note --id <note_id>`（用于确认某篇 note 的题目情况）

### C. 技术主题反查层
适合：`找包含某技术主题的面经`

优先复用：
- `scripts/query_tagged.js entity --value <关键词> --filter-valid`
- 然后按返回结果中的 `note_id` 聚合为 note 列表，而不是直接输出题目列表

---

## 路由规则

### 情况 1：用户明确给出 `note_id`
- 直接检查该 `note_id` 是否存在于已处理数据中
- 输出该 note 的摘要信息
- 推荐下一步：
  - `进入 xhs_practice_sop 单篇复盘`
  - 或 `先浏览该篇题单`

### 情况 2：用户给出公司 / 岗位 / 轮次 / 年份
- 优先按 note 元数据筛选候选面经
- 输出前 N 个最相关的 `note_id`
- 如果用户要训练，推荐：
  - 相似风格多篇 note → `company_mock`
  - 单篇精读 → `single_note_review`

### 情况 3：用户给出技术主题
- 先从题库中按主题命中题目
- 再按 `note_id` 聚合回笔记层
- 根据命中题数、高频程度、元数据完整度排序
- 输出候选 note，而不是题目列表

### 情况 4：用户表达模糊
例如：`开始刷面经`

你应先返回候选路径，而不是直接替用户做决定：
- 推荐几篇高价值 note
- 或推荐 2~3 种训练模式
- 引导用户明确是按公司、按专题，还是按单篇开始

---

## 排序与默认策略

### 默认去重键
- `note_id`

### 默认输出数量
- 返回前 `10` 篇候选 note

### 默认优先级
1. 与用户目标公司 / 岗位 / 轮次强相关
2. 与目标技术主题强相关
3. 题目质量较高（优先 `is_valid_for_library=true` 命中较多的 note）
4. 元数据完整
5. 更适合直接进入训练（已打标签 / 已结构化优先）

### 用户问“我该先刷哪篇”时
优先推荐：
- 高频考点覆盖多
- 目标公司强相关
- 题量适中，适合单次训练
- 可直接进入 `xhs_practice_sop`

---

## 输出格式

默认输出为简洁的 note 级摘要列表。

### 推荐格式
```markdown
### 候选面经（前 N 篇）

| # | note_id | 公司 | 岗位 | 轮次 | 年份 | 命中原因 | 推荐动作 |
|---|---------|------|------|------|------|----------|----------|
```

每条结果至少包含：
- `note_id`
- 公司
- 岗位
- 轮次
- 年份
- 命中原因
- 推荐训练模式
- 推荐下一步动作

### 推荐结果对象模板

当需要在会话中保持更稳定的 note 选择结果时，建议按以下结构组织：

```json
{
  "note_id": "6833da02000000000303954e",
  "company": "滴滴",
  "position": "后端",
  "round": "一/二面",
  "year": 2025,
  "selection_reason": [
    "目标公司相关",
    "MySQL 命中较多",
    "适合单篇复盘"
  ],
  "readiness": {
    "is_structured": true,
    "is_tagged": true,
    "question_count_known": true
  },
  "recommended_mode": "single_note_review",
  "recommended_next_action": "start_practice"
}
```

### 推荐动作枚举

为保证和 `xhs_practice_sop` 的衔接清晰，建议使用统一动作：

- `start_practice`
- `preview_questions`
- `switch_to_company_mock`
- `switch_to_topic_drill`
- `narrow_filters`
- `choose_one_note`

### 推荐模式判定规则

- **单个高相关 note**：推荐 `single_note_review`
- **多个同公司 / 同轮次 note**：推荐 `company_mock`
- **多个同主题命中 note**：推荐 `topic_drill`
- **用户意图模糊**：推荐先 `choose_one_note` 或 `narrow_filters`

---

## 与 `xhs_practice_sop` 的衔接

本 skill 的输出应该天然能作为 `xhs_practice_sop` 的输入。

### 推荐衔接方式
- 单个 `note_id` → 进入 `single_note_review`
- 多个同公司 note → 进入 `company_mock`
- 多个同专题 note → 进入 `topic_drill`

输出结束时应主动提示：
- `是否从其中一篇开始训练？`
- `是否进入 company_mock / topic_drill 模式？`

### 推荐交接格式

当用户确认某篇 note 后，建议向下游 skill 交接以下最小上下文：

```json
{
  "mode": "single_note_review",
  "note_id": "6833da02000000000303954e",
  "company": "滴滴",
  "position": "后端",
  "round": "一/二面",
  "year": 2025,
  "recommended_first_action": "preview_questions"
}
```

如果用户选择的是多个 note 的组合模式，则改成：

```json
{
  "mode": "company_mock",
  "candidate_note_ids": ["noteA", "noteB", "noteC"],
  "company": "美团",
  "position": "后端",
  "round": "一面",
  "recommended_first_action": "start_practice"
}
```

---

## 标准交互示例

### 示例 1：按公司筛 note

#### 用户输入
`使用 xhs_note_selector 筛美团社招一面的面经`

#### 理想输出
- 返回前 10 个候选 `note_id`
- 给出每篇的公司、岗位、轮次、年份、命中原因
- 如果候选高度同质，推荐直接进入 `company_mock`

### 示例 2：按专题反查 note

#### 用户输入
`使用 xhs_note_selector 找包含 MySQL 的面经`

#### 理想输出
- 先按主题命中题目
- 再按 `note_id` 聚合
- 输出命中题数较多的 note
- 推荐进入 `topic_drill` 或选择其中一篇精读

### 示例 3：用户意图模糊

#### 用户输入
`开始刷面经`

#### 理想输出
- 不直接返回大量题目
- 优先给 2~3 条起步路径：按公司、按专题、按单篇
- 每条路径附带 1~3 个候选 `note_id`
- 引导用户明确想走哪种模式

---

## 注意事项

- 本 skill **不负责** 深度分析题目。
- 本 skill **不直接输出** 大量 `question_id` 作为主结果。
- 本 skill 应优先帮助用户**缩小训练上下文**，而不是扩大信息量。
- 如果用户只想看题库统计，应改用 `xhs_query`。
- 如果用户已经明确要训练某篇 note，应尽快把控制权交给 `xhs_practice_sop`。