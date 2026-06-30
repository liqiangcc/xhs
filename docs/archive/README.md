# Docs Archive

本目录保存历史讨论材料。它们有参考价值，但不是当前执行计划。

当前正式执行文档在：

```text
docs/refactor/
```

## legacy-agent

`legacy-agent/` 保存早期 Agent / Skill / 低代码方向的探索文档。

这些文档强调由 Agent 动态执行数据处理和面试辅导，但当前方案已经收敛为：

```text
代码内核负责稳定数据、校验、索引和状态推进
AI / Skill 负责语义候选、答案生成和辅助判断
```

## research

`research/` 保存长篇技术预研和背景分析。

这类文档可以帮助理解设计取舍，但实施时应以 `docs/refactor/` 中的需求、领域模型、技术方案和执行清单为准。
