---
name: xhs_query
description: 查询已打标签的面试题库（note_tagged/），支持按领域、公司、题型、认知深度、技术实体等多维度查询，以及统计汇总和高频题分析。
---

# 面试题库查询技能 (XHS Question Query)

## 技能描述

你现在扮演一个**面试题库分析助手**。
你的任务是理解用户的自然语言查询意图，将其转化为对 `scripts/query_tagged.js` 的调用，并将查询结果整理成简洁可读的 Markdown 格式呈现给用户。

**数据来源**：`note_tagged/*.json` — 每个文件包含一个笔记的多维度标签化面试题。

---

## 执行工作流 (Workflow)

当用户触发此技能时（如："使用 xhs_query 查询..."），遵循以下步骤：

### Step 1：意图识别与命令映射

根据用户意图，选择对应的命令：

| 用户意图 | 调用命令 |
|----------|----------|
| 查询某个技术领域（l1）的题 | `node scripts/query_tagged.js domain --l1 <名称>` |
| 查询某个子方向（l2）的题 | `node scripts/query_tagged.js domain --l2 <名称>` |
| 查询某家公司的面试题 | `node scripts/query_tagged.js company --name <名称>` |
| 查询某种题型 | `node scripts/query_tagged.js type --value <类型>` |
| 查询某个认知深度的题 | `node scripts/query_tagged.js depth --value <深度>` |
| 查询涉及某技术实体的题 | `node scripts/query_tagged.js entity --value <关键词>` |
| 查看整体统计 / 各维度分布 | `node scripts/query_tagged.js stats` |
| 查询跨笔记高频题 / 重复出现的题 | `node scripts/query_tagged.js hotspot` |

### Step 2：参数标准化

将用户的口语表达对齐到字段枚举值：

**domain.l1 枚举**：
`Java基础` / `Spring生态` / `数据库` / `缓存` / `中间件` / `操作系统` / `计算机网络` / `系统设计` / `算法与数据结构` / `云原生与工程化` / `其他`

**question_type 枚举**：
`八股文_Concept` / `原理深度_UnderTheHood` / `场景设计_Scenario` / `算法手撕_Coding` / `项目深挖_Project` / `行为软技_Behavioral`

**cognitive_depth 枚举**：
`L1_Principle` / `L2_Mechanism` / `L3_Diagnostic` / `N_A`

> 💡 如果用户说"JVM题"，映射到 `domain --l2 JVM`；说"算法题"映射到 `type --value 算法手撕_Coding`；说"系统设计"映射到 `domain --l1 系统设计`。

### Step 3：执行命令

使用 `run_command` 工具在项目根目录（`c:\Users\liqiang12\IdeaProjects\xhs`）执行该命令，收集 JSON 输出。

### Step 4：格式化输出

将结果整理为 Markdown 表格：

**筛题类命令**（输出题目列表）：

```markdown
### 查询结果：[查询条件描述]，共 N 道题

| # | 题目 | 公司 | 题型 | 认知深度 | 领域 |
|---|------|------|------|----------|------|
| 1 | ... | ... | ... | ... | ... |
```

**stats 命令**（输出统计）：
直接呈现各维度的计数分布（可用 emoji 或文字图）。

**hotspot 命令**（输出高频题）：

```markdown
### 高频题排行：共 N 道题出现在 2+ 个笔记中

| 频次 | 题目 | 领域 | 出现来源（公司/轮次）|
|------|------|------|---------------------|
| 3 | ... | ... | 字节一面, 百度二面, 腾讯一面 |
```

---

## 枚举快查表

### domain.l2 → domain.l1 映射

| 用户说 | l2 参数 | l1 参数 |
|--------|---------|---------|
| JVM / 垃圾回收 / 内存 | `JVM` | `Java基础` |
| 并发 / 锁 / JUC | `并发编程(JUC)` | `Java基础` |
| 集合 / HashMap / ArrayList | `集合框架` | `Java基础` |
| Redis | `Redis` | `缓存` |
| MySQL / 索引 / 事务 | `MySQL` | `数据库` |
| Kafka / MQ | 用 `entity --value Kafka` | — |
| TCP / HTTP | `TCP/IP` 或 `HTTP/HTTPS` | `计算机网络` |
| Docker / K8s | `Docker` / `Kubernetes` | `云原生与工程化` |
| 线程 / 进程 | `进程与线程` | `操作系统` |

---

## 注意事项

- 工作目录必须是 `c:\Users\liqiang12\IdeaProjects\xhs`（项目根目录），否则路径解析会失败。
- `company --name` 支持**模糊匹配**，如 `--name 字节` 可命中 `字节跳动`。
- `entity --value` 支持**模糊匹配**，如 `--value Redis` 可命中 `Redis Cluster`、`Redis持久化` 等。
- 查询结果默认包含所有题（含 `is_valid_for_library: false` 的题），如用户只想看"有复习价值"的题，在呈现时过滤或注明。
- 如果查询结果超过 20 条，只展示前 20 条，并注明"仅显示前 20 条，共 N 条"。

---

## 示例对话

**用户**：使用 xhs_query 查询字节跳动考过的所有 JVM 题

**Agent 行为**：
1. 意图分析：同时要求公司=字节跳动 且 domain.l2=JVM
2. 先执行 `node scripts/query_tagged.js company --name 字节跳动`
3. 再在结果中进一步过滤 `domain_l2 === 'JVM'`（或额外执行 `domain --l2 JVM` 后取交集）
4. 以表格呈现结果

**用户**：用 xhs_query 看看现在题库里哪些技术领域题最多

**Agent 行为**：
1. 执行 `node scripts/query_tagged.js stats`
2. 解读 domain.l1 那一栏，以可读排名格式输出
