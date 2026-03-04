---
name: xhs_pipeline
description: 全自动驱动小红书面经笔记的完整处理管线：筛选 → 提取 → Hash → 打标 → 提交。调用本 Skill 时无需额外参数，AI 将自主执行所有步骤。
---

# 小红书面经全流程自动化管线 (XHS Pipeline Orchestrator)

// turbo-all

## 技能描述

你现在是一个**全自动化数据处理管线的执行者**。你只需执行一个脚本，获取任务清单，然后逐个完成 AI 专属任务（提取与打标）。

---

## 执行流程 (3 步完成)

### 第 1 步：获取任务清单

执行命令（`SafeToAutoRun = true`）：
```bash
node scripts/xhs_pipeline.js
```

该脚本会**一次性**完成以下所有机械性工作：
- 筛选高质量面经笔记
- 幂等性检查（跳过已处理的笔记）
- 为已结构化的笔记生成 Hash

输出为 JSON 格式的任务清单，每个任务有两种 `action`：

| action | 含义 | AI 需要做什么 |
|--------|------|------------|
| `extract_and_tag` | 笔记尚未结构化 | ① 读取 `desc_path` 和 `img_path` → 提取问题 → 写入 `note_structured/{uuid}.json`<br>② 执行 `node scripts/xhs_process.js {uuid}` 获取 hash<br>③ 打标签 → 写入 `note_tagged/{uuid}.json` |
| `tag_only` | 已结构化，只需打标 | 直接用任务中提供的 `hashes` 和 `metadata` → 打标签 → 写入 `note_tagged/{uuid}.json` |
| `skip` | 已完成或无效 | 无需操作 |

---

### 第 2 步：逐个执行任务

#### 对于 `extract_and_tag` 类型的任务：

1. 使用 `view_file` 读取任务中的 `desc_path` 和 `img_path`（如非 null）
2. **提取面试题**，遵循 `xhs_extractor` skill 规则：
   - 忠于原味，保留原话
   - 代码题加 `算法：` 前缀，设计题加 `场景：` 前缀
   - 过滤情绪吐槽、项目隐私、答案思路
   - desc 和 img 去重
3. 使用 `write_to_file` 写入 `note_structured/{uuid}.json`：
   ```json
   {
     "note_id": "{uuid}", "source": "小红书",
     "company": "...", "position": "...", "round": "...",
     "level": "...", "year": "...", "date": "...",
     "questions": ["问题1", "算法：手写快排"]
   }
   ```
4. 执行命令获取 hash（`SafeToAutoRun = true`）：
   ```bash
   node scripts/xhs_process.js {uuid}
   ```
5. 从命令输出的表格中提取 `hash` 列作为 `question_id`
6. **打标签**（见下方通用打标规则），写入 `note_tagged/{uuid}.json`

#### 对于 `tag_only` 类型的任务：

1. 任务 JSON 中已包含 `metadata` 和 `hashes` 数组
2. 直接使用 `hashes[i].hash` 作为 `question_id`，`hashes[i].question` 作为原始题目
3. **打标签**，写入 `note_tagged/{uuid}.json`

#### 通用打标规则（来自 `xhs_tagger` skill）：

对每道题分配：
- `domain`: `{ "l1": "技术大领域", "l2": "技术子方向" }`
- `question_type`: `八股文_Concept` / `原理深度_UnderTheHood` / `场景设计_Scenario` / `算法手撕_Coding` / `项目深挖_Project`
- `cognitive_depth`: `L1_Principle` / `L2_Mechanism` / `L3_Diagnostic`
- `tech_entities`: `["HashMap", "红黑树"]`
- `business_context`: 特定业务场景，通用题设为 `[]`
- `is_valid_for_library`: `true` / `false`

输出 JSON 格式：
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

### 第 3 步：提交

所有任务处理完毕后，执行命令（`SafeToAutoRun = true`）：
```bash
node scripts/commit_changes.js
```

然后输出批次汇总报告：处理数量、有效/无效、新增题目数、涉及公司。

---

## 示例调用

用户只需说：**"使用 xhs_pipeline 处理下一批笔记"**，AI 即可自主完成全部流程。
