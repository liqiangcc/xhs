---
name: xhs_pipeline
description: 全自动驱动小红书面经笔记的完整处理管线：筛选 → 提取 → Hash → 打标 → 提交。调用本 Skill 时无需额外参数，AI 将自主执行所有步骤。
---

# 小红书面经全流程自动化管线 (XHS Pipeline Orchestrator)

## 技能描述

你现在是一个**全自动化数据处理管线的执行者**。你的任务是按照以下固定的 5 个阶段，依次处理一批小红书面经笔记，将其从原始文本转化为结构化、已打标的题库，最后提交到 Git。

**每次执行本管线时，确保严格按阶段顺序处理，不要跳过任何一步。**

---

## 执行阶段 (Execution Phases)

### 阶段 1：发现待处理笔记 (Discovery)

**目标**：获取本批次需要处理的笔记 ID 列表。

**操作**：
1. 执行命令：
   ```bash
   node scripts/filter_notes.js
   ```
2. 该命令会输出若干行 `{uuid}.txt` 格式的文件名。**取前 10 个** `uuid`（去掉 `.txt` 后缀）作为本批次的处理列表。
3. 在继续之前，使用以下命令**逐一确认幂等性**——若 `note_tagged/{uuid}.json` 已存在，则跳过该 uuid：
   ```bash
   # 示例：检查某 uuid 是否已完成
   # 若文件存在则跳过，否则加入处理队列
   Get-Item note_tagged/{uuid}.json 2>$null
   ```

---

### 阶段 2：结构化提取 (Extraction)

**目标**：对本批次每一个 uuid，从文本中萃取面试题，生成 `note_structured/{uuid}.json`。

**操作（对每个 uuid 循环执行）**：

1. 检查 `note_structured/{uuid}.json` 是否已存在。若已存在，跳过本 uuid 的提取，直接进入阶段 3。
2. 读取原始文本：
   - `note_desc/{uuid}.txt`（笔记正文）
   - `note_img_txt/{uuid}.txt`（图片 OCR 文本，如存在）
3. 按照 `xhs_extractor` skill 的**提取规则**进行分析与提取。
4. 使用 `write_to_file` 将结构化 JSON 写入 `note_structured/{uuid}.json`，格式如下：
   ```json
   {
     "note_id": "{uuid}",
     "source": "小红书",
     "company": "推断的公司名，无则填 未知",
     "position": "推断的岗位，无则填 未知",
     "round": "例如 一面，无则填 未注明",
     "level": "例如 校招/社招，无则填 未知",
     "year": "推断年份，无则填 未知",
     "date": "推断日期，无则填 未知",
     "questions": [
       "问题原文 1",
       "算法：手写快排",
       "场景：高并发下如何限流"
     ]
   }
   ```
5. **无效笔记**（吐槽帖、offer 对比、资料分享等）：`questions` 设为空数组 `[]`，文件仍需创建。

---

### 阶段 3：生成题目 Hash ID (Hashing)

**目标**：为每道题生成全局唯一的 `question_id`，同时输出 Hash 清单以备打标阶段使用。

**操作（对每个 uuid 循环执行）**：

1. 执行命令：
   ```bash
   node scripts/xhs_process.js {uuid}
   ```
2. 若输出包含 `[DONE]` 字样，说明该笔记已完成过打标，**跳过**。
3. 若输出包含 `[CONTINUE]`，说明需要继续打标，**保留 Hash 输出结果**（格式为 `index|md5hash|问题原文`），进入阶段 4。
4. 若 `questions` 为空，`xhs_process.js` 会提示 0 hashes，**跳过阶段 4**，直接标记为已处理。

---

### 阶段 4：多维度打标 (Tagging)

**目标**：为每道题打上领域、题型、认知深度、技术实体等多维标签，生成 `note_tagged/{uuid}.json`。

**操作（对每个 uuid 循环执行）**：

1. 读取 `note_structured/{uuid}.json` 中的 `questions` 数组。
2. 读取阶段 3 中 `xhs_process.js` 输出的 Hash 清单，获取每道题的 `question_id`（32 位 MD5）。
3. 按照 `xhs_tagger` skill 定义的**标签约束契约**，对每道题逐一分析并分配以下字段：
   - `domain.l1`：技术大领域（如 `Java基础`、`数据库`、`中间件`）
   - `domain.l2`：技术子方向（如 `JVM`、`MySQL`、`Kafka`）
   - `question_type`：`八股文_Concept` / `原理深度_UnderTheHood` / `场景设计_Scenario` / `算法手撕_Coding` / `项目深挖_Project`
   - `cognitive_depth`：`L1_Principle` / `L2_Mechanism` / `L3_Diagnostic`
   - `tech_entities`：如 `["HashMap", "红黑树"]`
   - `business_context`：特定业务场景标记，通用题设为 `[]`
   - `is_valid_for_library`：是否具有复习价值（`true`/`false`）
4. 使用 `write_to_file` 将打标结果写入 `note_tagged/{uuid}.json`，格式如下：
   ```json
   {
     "note_id": "{uuid}",
     "source": "小红书",
     "company": "...",
     "position": "...",
     "round": "...",
     "level": "...",
     "year": "...",
     "date": "...",
     "tagged_questions": [
       {
         "question_id": "32位md5",
         "original_question": "原始题目文本",
         "domain": { "l1": "Java基础", "l2": "JVM" },
         "question_type": "八股文_Concept",
         "cognitive_depth": "L1_Principle",
         "tech_entities": ["GC", "垃圾回收算法"],
         "business_context": [],
         "is_valid_for_library": true
       }
     ]
   }
   ```

---

### 阶段 5：提交持久化 (Commit)

**目标**：将本批次所有处理结果提交到 Git，确保进度可追溯。

**操作（所有 uuid 处理完毕后执行一次）**：

1. 执行命令：
   ```bash
   node scripts/commit_changes.js
   ```
2. 若输出 `[SUCCESS]` 则本批次完成。
3. 提交完成后，输出**批次汇总报告**，包含：
   - 本批处理的 uuid 数量
   - 有效笔记数 / 无效笔记数
   - 新增面试题总数
   - 涉及的主要公司和技术领域

---

## 幂等性保证 (Idempotency)

| 检查文件 | 若已存在 | 操作 |
|---------|---------|------|
| `note_tagged/{uuid}.json` | 该 uuid 已全部完成 | 直接跳过全部阶段 |
| `note_structured/{uuid}.json` | 提取已完成 | 跳过阶段 2，从阶段 3 开始 |
| `xhs_process.js` 输出 `[DONE]` | 打标已完成 | 跳过阶段 4 |

---

## 示例调用

用户只需说：**"使用 xhs_pipeline 处理下一批笔记"**，AI 即可自主完成全部 5 个阶段，无需人工干预。
