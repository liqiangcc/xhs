# XHS 文档入口

本目录当前只有一个正式执行入口：

```text
docs/refactor/README.md
```

`docs/refactor/` 是当前重构方案的 source of truth。实施、验收和后续讨论都应以该目录下的文档为准。

## 当前正式文档

建议按以下顺序阅读：

```text
refactor/README.md                  总览与第一阶段最小交付
refactor/01_requirements.md         业务目标与需求边界
refactor/02_domain_model.md         领域模型与核心对象
refactor/03_technical_design.md     技术方案与架构设计
refactor/04_refactor_plan.md        分阶段路线图
refactor/05_execution_checklist.md  执行清单与验收标准
refactor/06_github_actions_ai_management.md  GitHub Actions + AI 管理层
refactor/07_actions_review_todo.md  Actions 管理层 review 后的修复 TODO
```

当前有效方向：

```text
Question 是主数据
CanonicalQuestion 是知识资产
Taxonomy / Schema 是单一事实源
Index 是查询能力
Answer 和 ReviewProgress 绑定 canonical_id
AI / Skill 只生成候选，脚本负责校验、入库和状态推进
GitHub Actions 是自动化管理层，AI 只触发白名单任务
```

## 历史归档

`docs/archive/` 只保留历史讨论和技术预研，不作为当前执行依据。

```text
archive/legacy-agent/  早期 Agent / Skill / 低代码方向探索
archive/research/      价值导向重构与技术预研长文
```

如果归档文档与 `docs/refactor/` 冲突，以 `docs/refactor/` 为准。
