---
name: xhs_batch_analyzer
description: 按技术实体批量查询面试题并逐题深度分析，自动将结果写入 review/ans/ 目录。
---

# 技术实体批量分析工作流 (XHS Batch Analyzer)

> **执行入口**：推荐使用 `/xhs_batch_analyzer` workflow 触发。

## 技能目标

你现在扮演一个**批量复习编排器**。你的职责只有 3 步：

1. 根据技术实体查询题目 `question_id`
2. 逐题执行 `xhs_analyzer` 同等分析流程
3. 将每题分析结果写入 `review/ans/analysis_{question_id}.md`

**禁止跳过落盘步骤。** 这是一个“查询 + 分析 + 保存”的闭环工作流。
**同时必须避免重复分析。** 如果 `review/ans/analysis_{question_id}.md` 已存在，则跳过该题，不重复生成。

---

## 输入格式

用户通常会这样调用：

- `使用 xhs_batch_analyzer 分析 MySQL 相关题目`
- `使用 xhs_batch_analyzer 分析 Redis 的 5 道高频题`
- `使用 xhs_batch_analyzer 分析 ThreadLocal 相关题，限定美团社招`

如果用户没有明确数量：
- 默认取 **前 5 道有效题**。

如果用户给了附加过滤条件，则一并带上：
- 公司：`--filter-company`
- 层级：`--filter-level`
- 年份：`--filter-year`
- 轮次：`--filter-round`
- 仅有效题：默认始终加 `--filter-valid`

---

## 唯一查询入口

所有题目查询 **必须** 通过下面的脚本完成，禁止直接扫描 `note_tagged/*.json`：

```bash
node scripts/query_tagged.js entity --value <技术实体> --filter-valid --slim
```

如果用户提供了额外过滤条件，则拼接到同一条命令后面，例如：

```bash
node scripts/query_tagged.js entity --value MySQL --filter-valid --filter-company 美团 --filter-level 社招 --slim
```

### 查询结果处理规则

查询结果 stdout 是 JSON 数组，每项至少包含：
- `question_id`
- `original_question`

拿到结果后必须：
1. 按 `question_id` 去重
2. 使用下面的 JS 脚本检查是否已经分析过：

```bash
node scripts/check_existing_analyses.js --ids <id1,id2,id3>
```

3. 跳过已存在 `review/ans/analysis_{question_id}.md` 的题目
4. 对剩余未分析题目按返回顺序截取前 N 条（默认 N=5）
5. 如果无结果，明确告诉用户“没有匹配题目”或“题目已全部分析过”，并结束

---

## 逐题分析流程

对每个 `question_id`，严格执行以下步骤。

### Step 1：定位原题与题型

在真正分析之前，先检查：

```bash
node scripts/check_existing_analyses.js --id <question_id>
```

如果返回 `exists=true`，直接跳过该题，并在最终汇总中标记为“已存在，未重复分析”。

优先通过搜索题目 ID 定位其来源，再读取包含该题的记录，拿到：
- `question_id`
- `original_question`
- `question_type`
- `domain`
- `tech_entities`

### Step 2：路由分析框架

根据 `question_type` 选择 prompt：

| question_type | prompt |
|---|---|
| `八股文_Concept` | `prompts/concept.md` |
| `原理深度_UnderTheHood` | `prompts/under_the_hood.md` |
| `场景设计_Scenario` | `prompts/scenario.md` |
| `算法手撕_Coding` | `prompts/coding.md` |
| 其他 | 使用 `xhs_analyzer` 中的通用兜底框架 |

prompt 位置优先读取：
- `skills/xhs_analyzer/prompts/*.md`

### Step 3：按 `xhs_analyzer` 风格输出分析

输出必须遵守以下约束：
- 中文回答，技术术语保留英文
- 默认代码语言为 Java
- 禁止背诵式回答，要讲 WHY
- 每题至少给出 2 个追问方向
- 结构要与对应 prompt 保持一致

### Step 4：立即写入文件

每完成一题分析，必须立刻写入：

```text
review/ans/analysis_{question_id}.md
```

要求：
- 单题单文件
- 已存在同名文件时，默认跳过，不覆盖更新
- 文件内容直接写分析正文，不要加额外提示语

---

## 批处理执行顺序

完整工作流如下：

### A. 查询题目列表
执行：
```bash
node scripts/query_tagged.js entity --value <技术实体> --filter-valid --slim [其他过滤参数]
```

### B. 截取题目
- 去重后，先执行：

```bash
node scripts/check_existing_analyses.js --ids <逗号分隔的question_id列表>
```

- 跳过已存在分析文件的题目
- 对剩余未分析题目取前 N 条

### C. 循环分析
对题目列表中的每个 `question_id` 依次执行：
1. 再次检查 `review/ans/analysis_{question_id}.md` 是否存在
2. 不存在时，定位题目原文与题型
3. 读取对应 prompt
4. 生成结构化分析
5. 写入 `review/ans/analysis_{question_id}.md`

### D. 最终汇总
全部完成后，向用户输出：
- 本次查询的技术实体
- 实际分析并写入的题目数
- 生成的文件路径列表
- 如果有跳过项，说明原因（如“已存在，未重复分析”）

---

## 默认策略

如果用户只说“分析 MySQL 相关题目”，按以下默认参数执行：

```bash
node scripts/query_tagged.js entity --value MySQL --filter-valid --slim
```

然后：
- 去重
- 跳过已分析题目
- 取前 5 条未分析题
- 全部写入 `review/ans/`

---

## 示例调用

### 示例 1：按技术实体批量分析

用户说：
`使用 xhs_batch_analyzer 分析 MySQL 相关题目`

你应执行：
1. 查询 MySQL 相关有效题
2. 跳过 `review/ans/` 中已存在分析文件的题
3. 取前 5 道未分析题
4. 逐题分析
5. 写入 `review/ans/analysis_{question_id}.md`

### 示例 2：限定数量

用户说：
`使用 xhs_batch_analyzer 分析 Redis 的 3 道题`

你应执行：
1. 查询 Redis 相关有效题
2. 跳过已分析题目
3. 取前 3 道未分析题
4. 逐题分析并落盘

### 示例 3：附加过滤

用户说：
`使用 xhs_batch_analyzer 分析 ThreadLocal 相关题，限定美团社招，取 4 道`

你应执行：
```bash
node scripts/query_tagged.js entity --value ThreadLocal --filter-valid --filter-company 美团 --filter-level 社招 --slim
```

然后取前 4 道，逐题分析并写入文件。

---

## 失败处理

- 查询为空：直接告诉用户没有匹配题目，不创建文件
- 查询有结果但都已分析：直接告诉用户“匹配题目已全部分析过”，不重复创建文件
- 单题定位失败：跳过该题并继续下一个，同时在最终汇总中说明
- 某题分析完成但写文件失败：优先重试一次
- 不要因为单题失败而中断整个批处理

---

## 注意事项

- **查询阶段不得直接读 JSON 全量扫描替代脚本**
- **去重检查阶段统一使用 `node scripts/check_existing_analyses.js`**
- **分析阶段要复用 `xhs_analyzer` 的题型路由思想**
- **保存阶段必须写入 `review/ans/`，不能只在对话里输出**
- 批量分析时，题与题之间在聊天输出里可以用 `---` 分隔，但文件按单题拆分保存
