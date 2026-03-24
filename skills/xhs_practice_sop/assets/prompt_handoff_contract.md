# Prompt Handoff Contract

## 目标

定义 `xhs-note-selection.prompt.md` 与 `xhs-practice-session.prompt.md` 之间的最小交接协议，保证：
- 先选 note，再开始训练的链路稳定
- 训练 prompt 不需要重新猜测上下文
- 未来如需自动化串联时，字段有统一约定

---

## 推荐交接载荷

### 单篇面经模式

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

### 公司模拟模式

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

### 专题突破模式

```json
{
  "mode": "topic_drill",
  "topic": "MySQL",
  "candidate_note_ids": ["noteA", "noteB"],
  "recommended_first_action": "start_practice"
}
```

---

## 输出建议

`xhs-note-selection.prompt.md` 在输出候选结果后，建议额外给出一段：

```markdown
### 推荐交接载荷
+```json
+{ ... }
+```
```

这样用户可以直接复制给 `xhs-practice-session.prompt.md`，或在同一会话中继续使用。

---

## 消费规则

`xhs-practice-session.prompt.md` 收到交接载荷后：
- 优先信任 `mode`
- 若有单个 `note_id`，直接进入 `single_note_review`
- 若有多个 `candidate_note_ids` 且带 `company`，优先进入 `company_mock`
- 若带 `topic`，优先进入 `topic_drill`
- 若载荷缺字段，再做最小澄清，而不是重新从头筛选
