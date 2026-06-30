# XHS 仓库优化改进计划

> 分析日期：2026-06-30  
> 适用仓库：`liqiangcc/xhs`  
> 目标：在不改变当前业务目标的前提下，把“小红书面经题库”的采集、结构化、打标签、查询与复习分析链路升级为更安全、可维护、可验证、可扩展的数据工程项目。

---

## 1. 当前定位

该仓库已经形成了一条比较完整的面经题库流水线：

```text
搜索/采集 → HTML/JSON/正文/图片 → OCR/题目抽取 → 结构化 JSON → 多维标签 JSON → 查询/统计/复习计划
```

核心价值不是“抓取脚本”本身，而是：

1. 将面经原文转成稳定的题库结构；
2. 给每道题生成稳定 `question_id`；
3. 建立 `domain / question_type / cognitive_depth / tech_entities / is_valid_for_library` 等标签；
4. 支持按公司、岗位、年份、轮次、知识点、高频题进行查询和复习分析。

因此后续优化重点应从“能跑”转向“安全、可复现、可验证、可持续迭代”。

---

## 2. 已观察到的优点

### 2.1 数据产品方向清晰

`README.md` 已经把系统定位为“采集 · 结构化 · 打标签 · 智能查询”的面经题库，并明确了当前数据规模、数据流、目录结构和查询方式。

### 2.2 查询工具已经具备可组合能力

`scripts/query_tagged.js` 支持：

- `domain`、`company`、`type`、`depth`、`entity`、`note`、`question`、`stats`、`hotspot` 等查询；
- `--filter-valid`、`--filter-company`、`--filter-level`、`--filter-year`、`--filter-round`、`--slim` 等组合过滤；
- stdout 输出 JSON、stderr 输出摘要，便于 Agent 或脚本继续处理。

### 2.3 已有基础数据治理脚本

仓库中已经有：

- `scripts/check_consistency.js`：检查 structured/tagged 文件是否一致；
- `scripts/validate_tagged.js`：校验题目数量和 hash 是否一致；
- `scripts/normalize_tags.js`：尝试规范化标签；
- `scripts/find_ocr_needed.js`：定位需要重新 OCR 的笔记；
- `scripts/xhs_pipeline.js`：统一生成待处理任务并生成 hash。

这说明项目已经从“脚本集合”向“数据管线”演进，后续应继续沿着统一入口、统一 schema、统一校验的方向收敛。

---

## 3. 主要问题与风险

| 优先级 | 问题 | 影响 | 建议方向 |
|---|---|---|---|
| P0 | 采集脚本依赖 `raw_curl*.txt` 模板和 `eval` 执行 | 有命令注入、Cookie/请求头泄露、不可审计风险 | 替换为显式参数化客户端；禁止提交敏感请求模板；增加合规采集边界 |
| P0 | 缺少根目录 `.gitignore` | 日志、临时任务、原始请求、下载图片、HTML 等容易误提交 | 增加 `.gitignore` 和 secret scanning 清单 |
| P0 | 标签枚举存在漂移 | `xhs_tagger` 定义的强枚举与 `normalize_tags.js` 的标准化目标不完全一致，查询统计可能前后不统一 | 抽取统一 schema/constants，所有脚本共用 |
| P0 | hash/评分/关键词逻辑重复 | `generate_hashes.js`、`xhs_pipeline.js`、`validate_tagged.js`、`check_consistency.js`、`filter_notes.js`、`find_ocr_needed.js` 有重复逻辑 | 建立 `scripts/lib/` 公共模块 |
| P1 | 采集、解析、OCR、AI、查询混用 Bash/JS/Python | 维护成本高，错误处理风格不一致 | 统一成 Node CLI 或 Python CLI，保留少量兼容入口 |
| P1 | 大体量原始数据进入仓库 | 仓库体积变大，clone 慢，隐私和版权边界不清晰 | 原始数据外置，仓库只保留脱敏后的结构化数据和索引 |
| P1 | 缺少自动化测试和 CI | 每次新增脚本或修改 schema 都可能破坏历史数据 | 增加 package.json、测试、lint、GitHub Actions |
| P1 | AI 输出缺少强校验和重试机制 | 单次 LLM 输出格式错误会污染题库 | JSON Schema 校验 + 自动修复/重试 + 审核队列 |
| P2 | 查询每次全量读取 JSON | 数据量继续增长后性能和可交互性变差 | 生成离线索引、实体倒排索引、统计缓存 |
| P2 | 缺少质量闭环 | 标签质量、无效题比例、重复题比例难量化 | 建立数据质量仪表盘和人工抽样审核流程 |

---

## 4. P0：一周内应优先完成的改进

### 4.1 建立仓库安全边界

新增 `.gitignore`，至少覆盖：

```gitignore
# request templates / credentials
raw_curl*.txt
*.cookie
*.har
.env
.env.*

# logs / temp files
*.log
fetch.log
extract.log
failed_list.txt
unique_tasks.tmp
*.tmp

# large raw artifacts, decide by policy before committing
note_detail/
note_json/
downloaded_images/

# local outputs
hashmap_slim.json
```

同时增加 `docs/DATA_POLICY.md`，明确：

1. 只处理授权、公开、合规来源的数据；
2. 不把绕过平台风控、规避访问限制、批量账号/IP 切换作为项目目标；
3. 触发频控或异常访问提示时，采集流程必须停止并记录原因；
4. 不提交 Cookie、Token、个人账号信息、原始请求头；
5. 原文、图片、HTML 进入仓库前必须评估隐私和版权边界。

### 4.2 移除 `eval` 执行模式

当前 `search.sh` 和 `detail` 通过读取 `raw_curl*.txt`、`sed` 替换、`eval` 执行请求。这种方式的问题是：

- 关键字、token、模板内容都可能影响最终命令；
- 很难在代码审查中判断最终执行了什么；
- 原始 curl 模板往往包含敏感 Cookie 和请求头；
- 对失败原因、重试策略、限速策略缺乏结构化记录。

建议新增：

```text
scripts/collect/search_client.js
scripts/collect/detail_client.js
scripts/lib/http.js
scripts/lib/config.js
```

要求：

- 所有参数显式传入，不拼接 shell 命令；
- 请求头从本地 `.env` 或系统环境变量读取，不入库；
- 对每次请求输出 JSONL 日志：`note_id / page / status / duration / error_code`；
- 遇到频控、登录失效、权限异常时直接停止，不提供规避策略；
- 默认 dry-run，需要显式 `--apply` 才执行网络请求。

### 4.3 统一 schema 与枚举

新增：

```text
scripts/lib/schema.js
scripts/lib/taxonomy.js
scripts/lib/hash.js
```

其中 `taxonomy.js` 作为唯一标签来源：

```js
const DOMAIN_L1 = [
  'Java基础', 'Spring生态', '数据库', '缓存', '中间件', '操作系统',
  '计算机网络', '系统设计', '算法与数据结构', '云原生与工程化', '其他'
];

const QUESTION_TYPES = [
  '八股文_Concept', '原理深度_UnderTheHood', '场景设计_Scenario',
  '算法手撕_Coding', '项目深挖_Project', '行为软技_Behavioral'
];
```

然后让以下文件全部引用同一份定义：

- `skills/xhs_tagger/SKILL.md`；
- `skills/xhs_query/SKILL.md`；
- `scripts/query_tagged.js`；
- `scripts/normalize_tags.js`；
- `scripts/check_consistency.js`；
- `scripts/validate_tagged.js`；
- `README.md`。

这样可以避免“打标时一套枚举、标准化时另一套枚举、查询文档又是一套表达”的问题。

### 4.4 抽取公共 hash 与数据读取模块

当前多个脚本都实现了类似的 hash 逻辑：

```js
question.toLowerCase().replace(/[^\w\u4e00-\u9fa5]/g, '')
```

建议统一为：

```text
scripts/lib/hash.js
scripts/lib/io.js
scripts/lib/note.js
```

迁移顺序：

1. `generate_hashes.js` 改为调用 `lib/hash.js`；
2. `xhs_pipeline.js` 改为调用 `lib/hash.js`；
3. `validate_tagged.js` / `check_consistency.js` 改为调用同一实现；
4. 增加 hash 快照测试，确保历史 question_id 不漂移。

### 4.5 增加最小测试与 CI

新增 `package.json`：

```json
{
  "name": "xhs-interview-library",
  "private": true,
  "type": "commonjs",
  "scripts": {
    "test": "node --test",
    "check": "node scripts/check_consistency.js",
    "validate": "node scripts/validate_tagged.js",
    "query:stats": "node scripts/query_tagged.js stats --filter-valid"
  }
}
```

新增测试：

```text
test/hash.test.js
test/query_args.test.js
test/schema.test.js
test/consistency_sample.test.js
```

新增 GitHub Actions：

```text
.github/workflows/ci.yml
```

CI 先只跑：

1. `node --test`；
2. `node scripts/validate_tagged.js`；
3. `node scripts/check_consistency.js`；
4. 检查是否存在误提交的 `raw_curl*.txt`、`.env`、Cookie、Token 字样。

---

## 5. P1：两到三周内完成的数据工程化改造

### 5.1 收敛为统一 CLI

目标入口：

```bash
node scripts/xhs.js <command> [options]
```

建议命令：

```bash
node scripts/xhs.js collect search --keyword "java社招面试" --pages 5 --dry-run
node scripts/xhs.js collect detail --input notes/java社招面试.txt
node scripts/xhs.js parse html --input note_detail --output note_json
node scripts/xhs.js parse desc
node scripts/xhs.js parse images
node scripts/xhs.js ocr --ids-only
node scripts/xhs.js pipeline --limit 10
node scripts/xhs.js validate
node scripts/xhs.js query entity --value Redis --filter-valid --slim
```

保留旧脚本作为兼容 wrapper，但 README 只推荐新 CLI。

### 5.2 将数据层分区

建议目录：

```text
data/
  raw/              # 本地原始 HTML/图片，不默认提交
  intermediate/     # note_json / note_desc / note_img_txt
  curated/          # note_structured / note_tagged
  indexes/          # 生成的查询索引和统计缓存
  manifests/        # 每次处理批次的 manifest
review/
  ans/
  mysql/
```

迁移策略：

1. 短期先不移动历史目录，避免破坏脚本；
2. 新增路径配置层，允许旧路径和新路径共存；
3. 新增迁移脚本 `scripts/migrate_data_layout.js --dry-run`；
4. 确认查询和校验通过后，再逐步调整 README 和脚本默认路径。

### 5.3 引入 manifest 和可恢复执行

每次流水线执行生成：

```text
data/manifests/2026-06-30Txx-xx-xx.jsonl
```

每条记录包含：

```json
{
  "run_id": "2026-06-30Txx-xx-xx",
  "note_id": "...",
  "stage": "extract|hash|tag|validate|commit",
  "status": "success|failed|skipped",
  "input_sha256": "...",
  "output_path": "...",
  "error": null
}
```

好处：

- 任意阶段失败后可从失败点恢复；
- 可以审计每个文件由哪次运行生成；
- 后续可统计 AI 失败率、OCR 失败率、无效笔记比例。

### 5.4 强化 AI 输出质量控制

建议增加：

```text
scripts/lib/ai_schema.js
scripts/repair_structured.js
scripts/repair_tagged.js
```

流程：

1. LLM 输出后先 JSON parse；
2. 用 schema 校验字段、枚举、数组类型；
3. 对无效输出进行一次自动修复提示；
4. 仍失败则进入 `review/needs_human_review/`；
5. 所有修复动作写入 manifest。

### 5.5 构建查询索引

当前 `query_tagged.js` 每次读取 `note_tagged/*.json` 并展开全部题目。短期可接受，但数据继续增长后应生成索引。

新增：

```bash
node scripts/build_index.js
```

输出：

```text
data/indexes/questions.jsonl
data/indexes/entity_index.json
data/indexes/company_index.json
data/indexes/stats.json
```

`query_tagged.js` 优先读取索引，索引不存在或过期时提示运行 `build_index`。

---

## 6. P2：中长期产品化方向

### 6.1 题库质量仪表盘

新增 `review/quality_report.md`，定期输出：

- 总笔记数、总题数、有效题数；
- 公司分布、年份分布、轮次分布；
- domain/question_type/cognitive_depth 分布；
- 无效题比例；
- 重复题比例；
- schema 警告数量；
- OCR 待处理数量；
- 高频实体 Top N。

### 6.2 建立“题目去重 + 相似题聚类”

`question_id` 当前基于归一化文本 hash，只能识别完全或近似文本一致的题。建议增加语义去重：

1. 保留 `question_id` 作为稳定主键；
2. 新增 `canonical_question_id` 表示归并后的题簇；
3. 使用 embedding 或关键词规则聚类；
4. 高频题统计改用题簇，而不是单个文本 hash。

### 6.3 复习系统升级

基于已存在的 `review/` 目录，可以扩展为：

- `review/plans/`：按岗位/公司/时间生成复习计划；
- `review/ans/`：标准答案和追问；
- `review/sessions/`：模拟面试记录；
- `review/mistakes/`：错题和薄弱点；
- `scripts/generate_review_session.js`：按知识点抽题。

---

## 7. 建议实施顺序

### 第 1 阶段：安全与一致性

1. 增加 `.gitignore`；
2. 增加 `docs/DATA_POLICY.md`；
3. 抽取 `scripts/lib/hash.js`；
4. 抽取 `scripts/lib/taxonomy.js`；
5. 修正 `normalize_tags.js` 与 `xhs_tagger` 的枚举冲突；
6. 增加最小 `package.json` 和 `node --test`；
7. 增加 CI，防止误提交敏感文件。

验收标准：

- `node --test` 通过；
- `node scripts/check_consistency.js` 通过或输出已知可解释问题；
- 所有标签枚举来源一致；
- 仓库中不存在 `raw_curl*.txt`、`.env`、Cookie、Token 等敏感文件。

### 第 2 阶段：统一入口

1. 新增 `scripts/xhs.js`；
2. 将 `query_tagged.js` 接入公共读取模块；
3. 将 `xhs_pipeline.js` 接入公共 hash/schema 模块；
4. 将旧 Bash 脚本逐步包装或废弃；
5. 更新 README，只推荐统一 CLI。

验收标准：

- 新 CLI 覆盖 README 中的主流程；
- 旧命令仍可用或有清晰迁移说明；
- pipeline 失败后可根据 manifest 恢复。

### 第 3 阶段：数据质量与产品化

1. 生成离线索引；
2. 增加质量报告；
3. 加入语义去重；
4. 完善复习计划与模拟面试流程；
5. 评估是否需要把原始大文件迁出 Git。

验收标准：

- 查询响应不依赖全量扫描；
- 高频题统计按语义题簇输出；
- 每次新增数据后自动生成质量报告；
- 原始数据、结构化数据、复习内容边界清晰。

---

## 8. 具体 backlog

### P0 Backlog

- [ ] 新增 `.gitignore`，屏蔽请求模板、日志、临时文件、原始大文件。
- [ ] 新增 `docs/DATA_POLICY.md`，明确合规采集、隐私和敏感信息边界。
- [ ] 新增 `scripts/lib/hash.js`，统一 question_id 生成。
- [ ] 新增 `scripts/lib/taxonomy.js`，统一 domain/question_type/depth 枚举。
- [ ] 改造 `generate_hashes.js`、`xhs_pipeline.js`、`validate_tagged.js`、`check_consistency.js` 使用公共 hash。
- [ ] 改造 `normalize_tags.js`，不再引入与打标 schema 冲突的新枚举。
- [ ] 新增 `package.json` 和基础 `node --test`。
- [ ] 新增 `.github/workflows/ci.yml`。
- [ ] 替换或废弃 `eval` 执行链路。

### P1 Backlog

- [ ] 新增统一 CLI：`scripts/xhs.js`。
- [ ] 新增 manifest 机制。
- [ ] 将数据目录改造为 raw/intermediate/curated/indexes/manifests 分层。
- [ ] 为 AI 结构化和打标输出增加 JSON Schema 校验。
- [ ] 增加索引构建脚本 `scripts/build_index.js`。
- [ ] 优化 `query_tagged.js`，优先读取索引。
- [ ] 更新 README 的命令和目录说明。

### P2 Backlog

- [ ] 生成 `review/quality_report.md`。
- [ ] 增加语义去重和 `canonical_question_id`。
- [ ] 增加公司别名、岗位别名、年份规范化。
- [ ] 增加复习 session 生成器。
- [ ] 评估 Git LFS 或外部对象存储，降低仓库体积。

---

## 9. 推荐的目标架构

```text
xhs/
├── scripts/
│   ├── xhs.js                  # 统一 CLI
│   ├── lib/
│   │   ├── hash.js             # 稳定 question_id
│   │   ├── taxonomy.js         # 统一标签枚举
│   │   ├── schema.js           # JSON Schema 校验
│   │   ├── io.js               # 安全读写 JSON/JSONL
│   │   ├── note.js             # note 领域模型
│   │   └── manifest.js         # 执行记录
│   ├── build_index.js
│   ├── check_consistency.js
│   └── query_tagged.js
├── skills/
│   ├── xhs_extractor/
│   ├── xhs_tagger/
│   ├── xhs_query/
│   └── xhs_pipeline/
├── data/
│   ├── raw/                    # 不默认提交
│   ├── intermediate/           # 可重建中间产物
│   ├── curated/                # 结构化和打标结果
│   ├── indexes/                # 查询索引
│   └── manifests/              # pipeline 执行记录
├── review/
│   ├── ans/
│   ├── plans/
│   └── quality_report.md
├── docs/
│   ├── DATA_POLICY.md
│   └── SCHEMA.md
├── test/
├── package.json
└── README.md
```

---

## 10. 成功指标

| 指标 | 当前问题 | 目标 |
|---|---|---|
| Schema 一致性 | 多处枚举和 hash 逻辑重复 | 所有脚本共用一份 schema/hash/taxonomy |
| 数据质量 | 有校验脚本但未进入 CI | 每次提交自动校验 |
| 安全性 | 请求模板和 `eval` 风险 | 无敏感模板入库，无 shell 拼接执行 |
| 可维护性 | Bash/JS/Python 分散 | 统一 CLI + 公共模块 |
| 可恢复性 | 失败后主要靠人工判断 | manifest 记录每步状态 |
| 查询性能 | 每次全量读取 JSON | 索引化查询 |
| 仓库体积 | 原始数据和图片可能持续膨胀 | 原始大文件外置或受控提交 |

---

## 11. 总结

这个仓库已经具备“面经知识库”的雏形，最值得保留的是：

1. 已沉淀的结构化/打标数据；
2. `query_tagged.js` 的组合查询能力；
3. `xhs_pipeline.js` 的任务编排思路；
4. `check_consistency.js` / `validate_tagged.js` 的数据治理意识；
5. `skills/` 中对 Agent 工作流的明确约束。

下一步不建议继续堆更多临时脚本，而应优先完成：

```text
安全边界 → 统一 schema → 公共模块 → 测试/CI → 统一 CLI → 索引与质量报告
```

完成 P0 后，项目会从“能自动跑的个人脚本仓库”提升为“可以长期维护和迭代的数据工程仓库”。
