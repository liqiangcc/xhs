# XHS Note Selector 结构化输出模板

## 目标

该文档定义 `xhs_note_selector` 推荐输出的结构化字段，方便：
- 会话内稳定传递上下文
- 后续交给 `xhs_practice_sop` 继续训练
- 未来如需落盘时保持字段统一

---

## 单条候选 note 模板

```json
{
  "note_id": "6833da02000000000303954e",
  "company": "滴滴",
  "position": "后端",
  "round": "一/二面",
  "year": 2025,
  "selection_reason": [
    "目标公司相关",
    "包含 MySQL 高频题",
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

---

## 候选列表模板

```json
{
  "selection_goal": "筛选适合刷的 MySQL 面经",
  "selection_type": "topic_based",
  "candidate_notes": [
    {
      "note_id": "noteA",
      "company": "滴滴",
      "position": "后端",
      "round": "一面",
      "year": 2025,
      "selection_reason": ["MySQL 命中较多"],
      "recommended_mode": "single_note_review",
      "recommended_next_action": "start_practice"
    },
    {
      "note_id": "noteB",
      "company": "美团",
      "position": "后端",
      "round": "二面",
      "year": 2025,
      "selection_reason": ["目标公司相关"],
      "recommended_mode": "company_mock",
      "recommended_next_action": "choose_one_note"
    }
  ],
  "recommended_path": "choose_one_note"
}
```

---

## 枚举约定

### `selection_type`
- `single_note`
- `company_based`
- `topic_based`
- `mixed`
- `ambiguous_start`

### `recommended_mode`
- `single_note_review`
- `topic_drill`
- `company_mock`

### `recommended_next_action`
- `start_practice`
- `preview_questions`
- `choose_one_note`
- `narrow_filters`
- `switch_to_company_mock`
- `switch_to_topic_drill`

---

## 口头输出建议

即使最终不以 JSON 展示给用户，也应保证口头输出能映射回上述字段。

推荐口头输出最少包含：
- `note_id`
- 公司 / 岗位 / 轮次 / 年份
- 为什么推荐
- 更适合哪种训练模式
- 下一步建议动作

---

## 与 Practice SOP 的交接模板

### 单 note 交接

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

### 多 note 交接

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