# 📚 小红书面经题库 — 采集 · 结构化 · 打标签 · 智能查询

从小红书搜索、抓取面试经验笔记，通过 AI 自动提取面试题目并打上多维度标签，最终构建可智能查询的结构化面试题库。

> **当前规模**：2000+ 道面试题 · 135 篇面经笔记 · 覆盖腾讯/美团/字节/百度等 30+ 家公司

---

## 🏗 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   1. 采集    │ ──→ │  2. 结构化   │ ──→ │  3. 打标签   │ ──→ │  4. 查询    │
│  (Shell)    │     │ (AI + JS)   │     │ (AI + JS)   │     │ (Node.js)   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
 search.sh           xhs_extractor       xhs_tagger          query_tagged.js
 fetch.sh            SKILL.md            SKILL.md            xhs_query SKILL
 fetch_detail.sh     xhs_process.js      generate_hashes.js
                     └─ xhs_pipeline (Orchestrator)
```

### 数据流

```
小红书搜索 → 笔记HTML → JSON → 正文/图片 → AI提取面试题
                                              ↓
                                        note_structured/  (结构化JSON)
                                              ↓
                                        note_tagged/      (多维度标签JSON)
                                              ↓
                                        query_tagged.js   (智能查询)
```

---

## 🚀 智能查询

### 基本命令

```bash
node scripts/query_tagged.js <command> [options] [filters]
```

| 命令 | 说明 | 示例 |
|------|------|------|
| `domain --l1 <名称>` | 按技术领域筛题 | `domain --l1 Java基础` |
| `domain --l2 <名称>` | 按子方向筛题 | `domain --l2 JVM` |
| `company --name <名称>` | 按公司筛题（模糊匹配） | `company --name 字节` |
| `type --value <类型>` | 按题型筛题 | `type --value 算法手撕_Coding` |
| `depth --value <深度>` | 按认知深度筛题 | `depth --value L3_Diagnostic` |
| `entity --value <关键词>` | 按技术实体筛题（模糊匹配） | `entity --value Redis` |
| `note --id <note_id>` | 查指定笔记的全部题 | `note --id 67ed5649...` |
| `stats` | 各维度统计分布 | `stats --filter-valid` |
| `hotspot` | 跨笔记高频题 | `hotspot --slim` |

### 全局过滤（可自由组合）

| 选项 | 说明 |
|------|------|
| `--slim` | 只输出 question_id + original_question（减少 token） |
| `--filter-valid` | 只保留有效题（is_valid_for_library=true） |
| `--filter-company <值>` | 按公司过滤（模糊匹配） |
| `--filter-level <值>` | 按 level 过滤（如 `校招`、`社招`） |
| `--filter-year <值>` | 按 year 过滤（如 `2024`） |
| `--filter-round <值>` | 按 round 过滤（如 `一面`） |

### 使用示例

```bash
# 美团社招面试偏好分析
node scripts/query_tagged.js stats --filter-company 美团 --filter-level 社招 --filter-valid

# 字节跳动校招2024年一面的JVM有效题
node scripts/query_tagged.js domain --l2 JVM --filter-company 字节 --filter-level 校招 --filter-year 2024 --filter-round 一面 --filter-valid --slim

# 索引相关面试题
node scripts/query_tagged.js entity --value 索引 --filter-valid --slim

# 跨笔记高频题精简列表
node scripts/query_tagged.js hotspot --filter-valid --slim

# 全量题库统计（含 tech_entities Top 30）
node scripts/query_tagged.js stats --filter-valid
```

---

## 📁 目录结构

```
xhs/
├── scripts/                    # 核心脚本
│   ├── query_tagged.js         # 查询引擎（支持 9 种命令 + 6 个全局过滤）
│   ├── xhs_process.js          # 笔记处理流水线控制器
│   ├── generate_hashes.js      # 题目 ID 生成（基于内容 Hash）
│   ├── filter_notes.js         # 笔记筛选
│   └── commit_changes.js       # 批量提交
│
├── skills/                     # Agent Skill 定义（唯一维护入口）
│   ├── xhs_extractor/SKILL.md  # 结构化提取技能
│   ├── xhs_tagger/SKILL.md     # 多维度打标签技能
│   ├── xhs_query/SKILL.md      # 智能查询技能
│   ├── xhs_batch_analyzer/SKILL.md # 按技术实体批量查询+分析+落盘
│   └── xhs_pipeline/SKILL.md   # 全流程自动化管线 (Orchestrator)
├── .github/skills -> ../skills # GitHub Copilot Skills 入口（软链接到 skills/）
│
├── note_structured/            # 结构化 JSON（135 篇）
├── note_tagged/                # 打标签后的 JSON（135 篇）
│
├── note_detail/                # 原始笔记 HTML
├── note_json/                  # 提取的 JSON
├── note_desc/                  # 笔记正文文本
├── note_images/                # 图片 URL 列表
├── downloaded_images/          # 已下载图片
├── question/                   # AI 提取的原始面试题
│
├── *.sh                        # 采集阶段 Shell 脚本
└── README.md
```

---

## 🔧 数据采集流水线

### 1. 搜索 & 抓取

```bash
# 搜索关键字（自动翻页，最多 20 页）
bash fetch.sh "java社招面试"

# 批量抓取笔记 HTML（自动限速 + 熔断）
bash fetch_detail.sh

# HTML → JSON → 正文 + 图片
bash html_to_json.sh
bash json_2_desc_txt.sh
bash json_2_img_urls.sh && bash url_2_img.sh
```

### 2. AI 提取面试题

```bash
# 从正文提取（需要 gemini CLI）
bash desc_2_questions.sh

# 从图片 OCR 提取
bash img_2_txt.sh
```

### 3. 结构化 & 打标签

通过 Agent Skill（`xhs_extractor` + `xhs_tagger`）驱动 AI 完成：
- **结构化**：提取公司、岗位、轮次、层级、年份及面试题列表
- **打标签**：为每道题标注 domain (l1/l2)、question_type、cognitive_depth、tech_entities 等
- **全流程管线**：通过 `xhs_pipeline` 技能串联上述步骤，实现批量自动化处理。

```bash
# 单笔记处理流水线
node scripts/xhs_process.js <note_id>

# 批量全流程自动化 (推荐用法)
# 使用 xhs_pipeline 技能引导：Discovery -> Extraction -> Hashing -> Tagging -> Commit
```

---

## 📊 标签体系

每道题包含以下维度：

| 维度 | 说明 | 示例值 |
|------|------|--------|
| `domain.l1` | 技术大领域 | Java基础、数据库、缓存 |
| `domain.l2` | 技术子方向 | JVM、并发编程(JUC)、MySQL、Redis |
| `question_type` | 题型 | 八股文_Concept、原理深度_UnderTheHood、场景设计_Scenario、算法手撕_Coding |
| `cognitive_depth` | 认知深度 | L1_Principle、L2_Mechanism、L3_Diagnostic |
| `tech_entities` | 技术实体 | HashMap、synchronized、B+树、Kafka |
| `is_valid_for_library` | 是否有复习价值 | true / false |

---

## 🛡 设计特点

- **断点续传** — 所有脚本检测已处理文件，自动跳过
- **反爬保护** — 随机延迟 + 批次休息 + 错误熔断
- **幂等执行** — 重复运行不会产生重复数据
- **Agent 友好** — `--slim` 模式减少 token，stdout/stderr 分离便于程序化处理
- **可组合过滤** — 6 个全局 filter 可自由组合，适用于所有查询命令

## 🤖 Copilot Skills 加载方式

- `skills/` 是 Skill 定义的唯一维护目录。
- GitHub Copilot 从 `.github/skills` 加载 Skill；该目录已通过软链接指向 `skills/`。
- 新增或修改 Skill 时，只需要维护 `skills/<skill_name>/SKILL.md`，无需再复制到其他目录。

### 批量分析工作流示例

- `使用 xhs_batch_analyzer 分析 MySQL 相关题目`
- `使用 xhs_batch_analyzer 分析 Redis 的 3 道题`
- `使用 xhs_batch_analyzer 分析 ThreadLocal 相关题，限定美团社招，取 4 道`

该工作流会自动执行三步：
- 通过 `node scripts/query_tagged.js entity --value <技术实体> --filter-valid --slim` 查询题目
- 通过 `node scripts/check_existing_analyses.js --ids <id1,id2,...>` 跳过 `review/ans/` 中已存在的分析文件
- 按题型复用 `xhs_analyzer` 的分析框架逐题生成答案
- 将每题结果写入 `review/ans/analysis_{question_id}.md`

如果匹配题目已经分析过，工作流会直接跳过，避免重复生成。

## 依赖

- `bash`, `curl`, `jq`, `python3` — 采集阶段
- `node` (Node.js) — 查询 & 处理阶段
- `gemini` CLI — AI 提取与打标签
