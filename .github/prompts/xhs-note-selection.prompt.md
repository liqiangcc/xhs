---
description: "启动一轮面经筛选：按公司、岗位、轮次、年份、技术主题和训练目标筛选候选 note_id，并给出推荐训练模式与下一步动作"
name: "XHS Note Selection"
argument-hint: "输入筛选目标，例如：筛美团社招一面的面经 / 找包含 MySQL 的面经 / 推荐一篇适合今天刷的 note"
agent: "agent"
---
基于当前工作区中的 [xhs_note_selector](../skills/xhs_note_selector/SKILL.md) 启动一轮面经筛选。

如需把结果继续交给训练阶段，请遵循 [prompt handoff contract](../../skills/xhs_practice_sop/assets/prompt_handoff_contract.md)。

请严格遵守以下流程：

1. 先识别用户是在按哪类目标筛 note：
   - 公司 / 岗位 / 轮次 / 年份
   - 技术主题 / 实体
   - 单篇精读
   - 模糊起步（不知道先刷什么）
2. 主输出必须是候选 `note_id`，而不是题目列表或题目分析
3. 如果用户按技术主题筛选：
   - 先通过题目命中相关 note
   - 再按 `note_id` 聚合回笔记层
4. 每条候选结果尽量包含：
   - `note_id`
   - 公司 / 岗位 / 轮次 / 年份
   - 命中原因
   - 推荐训练模式：`single_note_review` / `topic_drill` / `company_mock`
   - 推荐下一步动作：`start_practice` / `preview_questions` / `choose_one_note` / `narrow_filters`
5. 如果用户意图模糊，不要直接替用户决定；先给 2~3 条推荐路径，再引导用户明确选择
6. 输出结束时，主动提示是否进入 [xhs_practice_sop](../skills/xhs_practice_sop/SKILL.md)
7. 如果已经有明确推荐结果，额外输出一段 **推荐交接载荷**，供后续直接交给 [XHS Practice Session](xhs-practice-session.prompt.md)

重要限制：
- 不要直接输出大量 `question_id` 作为主结果
- 不要在 note 选择阶段做长篇题目分析
- 优先缩小训练上下文，而不是扩大信息量

开始时请先用 1~3 句话确认筛选目标，然后给出候选 note 列表。

输出结尾建议追加：

```markdown
### 推荐交接载荷
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
```