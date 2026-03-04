---
name: xhs_pipeline
description: 全自动驱动小红书面经笔记的完整处理管线：筛选 → 提取 → Hash → 打标 → 提交。调用本 Skill 时无需额外参数，AI 将自主循环执行直到无剩余任务。
---

# 小红书面经全流程自动化管线 (XHS Pipeline Orchestrator)

> **执行入口**：请使用 `/xhs_pipeline` workflow 触发，该 workflow 包含 `// turbo-all` 注解，所有命令自动执行。

## 技能描述

你现在是一个**全自动化数据处理管线的执行者**。你的唯一入口脚本是 `scripts/xhs_pipeline.js`，**禁止直接调用** `generate_hashes.js`、`xhs_process.js`、`filter_notes.js` 等其他脚本。

---

## ⚠️ 关键规则

1. **唯一脚本入口**：只允许调用 `node scripts/xhs_pipeline.js` 和 `node scripts/commit_changes.js`，禁止调用其他脚本。
2. **自动循环**：一批处理完并提交后，**立即**执行 `node scripts/xhs_pipeline.js` 获取下一批，循环直到输出的 `summary` 中所有 actionable 任务为 0。
3. **SafeToAutoRun = true**：所有 `run_command` 调用都必须设置此参数。
4. **禁止 shell 命令做文件检查**：不允许运行 `ls`、`dir`、`Get-Item`、`head`、`cat` 等命令。文件检查必须使用 `find_by_name`、`list_dir`、`view_file` 等内置工具。

---

## 执行流程

### 步骤 A：获取任务清单

执行（`SafeToAutoRun = true`）：
```bash
node scripts/xhs_pipeline.js
```

输出 JSON 包含 `tasks` 数组，每个任务的 `action` 字段决定 AI 的操作：

| action | AI 操作 |
|--------|---------|
| `extract_and_tag` | 需要提取 + 打标（见步骤 B1） |
| `tag_only` | 只需打标，hash 已在 JSON 中（见步骤 B2） |
| `skip` | 无需操作 |

**终止条件**：如果 `summary.extract_and_tag == 0 && summary.tag_only == 0`，说明没有待处理任务，输出汇总并结束。

---

### 步骤 B：逐个处理任务

#### B1: `extract_and_tag` 类型

1. 使用 `view_file` 读取任务中的 `desc_path` 和 `img_path`（如非 null）
2. **提取面试题**（遵循 `xhs_extractor` 规则）：
   - 忠于原味，保留原话
   - 代码题加 `算法：` 前缀，设计题加 `场景：` 前缀
   - 过滤情绪吐槽、项目隐私、答案思路
   - desc 和 img 重复部分只保留一份
   - 无效笔记 → `questions` 设为 `[]`
3. 使用 `write_to_file` 写入 `note_structured/{uuid}.json`：
   ```json
   {
     "note_id": "{uuid}", "source": "小红书",
     "company": "...", "position": "...", "round": "...",
     "level": "...", "year": "...", "date": "...",
     "questions": ["问题1", "算法：手写快排"]
   }
   ```
4. **获取 hash**——执行（`SafeToAutoRun = true`）：
   ```bash
   node scripts/xhs_pipeline.js hash {uuid}
   ```
   输出包含 `hashes` 数组，每项有 `hash`（question_id）和 `question`。
5. 使用 hash 结果进行**打标**（同 B2 步骤 3-4）。

#### B2: `tag_only` 类型

1. 任务 JSON 中已包含 `metadata` 和 `hashes` 数组，**无需再执行任何命令**。
2. 使用 `hashes[i].hash` 作为 `question_id`，`hashes[i].question` 作为原始题目。
3. **打标签**，对每道题分配：
   - `domain`: `{ "l1": "技术大领域", "l2": "子方向" }`
   - `question_type`: `八股文_Concept` / `原理深度_UnderTheHood` / `场景设计_Scenario` / `算法手撕_Coding` / `项目深挖_Project`
   - `cognitive_depth`: `L1_Principle` / `L2_Mechanism` / `L3_Diagnostic`
   - `tech_entities`: `["HashMap", "红黑树"]`
   - `business_context`: 特定业务场景，通用题 `[]`
   - `is_valid_for_library`: `true` / `false`
4. 使用 `write_to_file` 写入 `note_tagged/{uuid}.json`：
   ```json
   {
     "note_id": "{uuid}", "source": "小红书",
     "company": "...", "position": "...", "round": "...",
     "level": "...", "year": "...", "date": "...",
     "tagged_questions": [
       {
         "question_id": "32位md5",
         "original_question": "原始题目",
         "domain": { "l1": "Java基础", "l2": "JVM" },
         "question_type": "八股文_Concept",
         "cognitive_depth": "L1_Principle",
         "tech_entities": ["GC"],
         "business_context": [],
         "is_valid_for_library": true
       }
     ]
   }
   ```

---

### 步骤 C：提交 + 继续下一批

1. 本批全部任务完成后，执行（`SafeToAutoRun = true`）：
   ```bash
   node scripts/commit_changes.js
   ```
2. **立即**回到步骤 A，执行 `node scripts/xhs_pipeline.js` 获取下一批任务。
3. **重复 A → B → C 循环**，直到步骤 A 的输出中 `summary.extract_and_tag == 0 && summary.tag_only == 0`。
4. 最终输出**全量汇总**：累计处理笔记数、新增题目数、涉及公司。

---

## 示例调用

用户只需说：**"使用 xhs_pipeline 处理笔记"**，AI 将自动循环执行，无需人工干预。
