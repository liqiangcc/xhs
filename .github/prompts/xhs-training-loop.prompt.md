---
description: "启动一轮完整训练闭环：接收 note 选择结果或当前训练上下文，继续逐题训练，或将本轮训练结果固化到 review/。适用于：刚练完一篇 note 想生成回炉清单；想继续昨天的 same_day_queue；想把 note_selection 和 practice 串起来。"
name: "XHS Training Loop"
argument-hint: "例如：固化今天这篇 note 的训练结果 / 继续昨天的回炉 / 从 note_id=xxx 开始并在结束时写入 review"
agent: "agent"
---

基于当前工作区中的 [xhs_training_loop](../skills/xhs_training_loop/SKILL.md)、[xhs_practice_sop](../skills/xhs_practice_sop/SKILL.md) 和 [xhs_note_selector](../skills/xhs_note_selector/SKILL.md) 启动一轮完整训练闭环。

**口径继承**：本 prompt 涉及的训练、评分、追问、总结均继承 `xhs_practice_sop` 的资深候选人口径——默认按「结论 → 原理 → 取舍 → 场景 → 边界」组织回答与评分，不要长期停留在校招式定义背诵。

请严格遵守以下优先级：

1. 如果用户已经给出 note-selection 的交接载荷或明确 `note_id`：
   - 直接进入训练或结果固化，不要重新筛 note
2. 如果当前会话已经完成了一轮 note 训练，且用户表达“固化 / 记录 / 回炉 / 下一步流程”：
   - 优先进入 `solidify_result`
   - 输出回炉清单、次日复述提纲、下一步建议
   - 如果用户同意，按 `review/` 统一格式落盘
3. 如果用户说“继续 / 下一题 / 继续昨天的回炉”：
   - 优先恢复当前进度或回炉队列，而不是重新从头开始
4. 只有当上下文缺失时，才回退到 `xhs_note_selector`

请将当前动作路由为以下之一：
- `start_from_selection`
- `continue_practice`
- `solidify_result`
- `rework_review`

如果是 `solidify_result`，主输出至少包含：
- 当前 note 信息
- 已练题 / 跳过题 / 回炉题概览
- `same_day_queue / next_day_queue / day3_queue / day7_queue`
- 次日复述提纲
- 推荐下一步动作

如果用户明确同意固化结果，请将内容写入：
- `review/sessions/`
- `review/queues/`
- `review/summary/`

开始时请先用 2~4 句话确认：
- 当前阶段属于哪个动作
- 将使用什么上下文
- 是继续训练，还是先固化结果
