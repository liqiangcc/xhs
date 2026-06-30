# xhs 仓库优化改进计划

> 生成日期：2026-06-30  
> 仓库：`liqiangcc/xhs`  
> 分支：`master`  
> 本文档基于对仓库 README、核心 Node.js 脚本、Shell/Python 采集脚本、Agent Skill 文档与部分数据治理脚本的静态阅读分析。本文档只提出优化计划，不直接改动现有业务代码或数据。

---

## 1. 仓库现状概览

`xhs` 当前是一个围绕“小红书面经题库”的数据工程与智能查询项目，核心目标是从小红书搜索、抓取面试经验笔记，通过 AI 提取面试题、结构化元数据、打标签，最终形成可查询、可复习、可分析的题库。

当前主链路可以概括为：

```text
搜索/抓取笔记 → HTML → JSON → 正文/图片 → AI 提取题目 → note_structured
                                            ↓
                                      AI 打标签 → note_tagged
                                            ↓
                                      query_tagged.js 查询/统计/热点分析
```

已具备的基础能力：

- 有清晰的四段式流水线：采集、结构化、打标签、查询。
- `scripts/query_tagged.js` 已支持领域、公司、题型、认知深度、技术实体、笔记 ID、题目 ID、统计、热点等查询能力。
- `xhs_pipeline` 已经在尝试收敛为统一入口，减少 Agent 直接调用多个零散脚本。
- 已存在 `check_consistency.js` / `fix_consistency.js` / `fix_master_sweep.js` 等数据一致性和清洗脚本。
- Skill 文档已经对提取、打标签、查询、批量分析、自动化管线建立了比较完整的操作契约。

主要问题集中在：工程化基础薄弱、脚本鲁棒性不足、规则分散重复、缺少自动化测试与 CI、数据治理标准还不够强、安全/合规边界需要显式化。

---

## 2. 总体优化目标

### 2.1 短期目标

在不大规模重构的前提下，让仓库“可重复运行、可验证、可安全提交”。

重点是：

- 补齐 `.gitignore`、依赖清单、运行脚本入口和基础文档。
- 给现有脚本加最小化测试和一致性校验。
- 修复 Shell 脚本中的高风险问题，例如 `eval`、输入未转义、错误统计、trap 清理。
- 建立数据 Schema，防止 AI 生成的 JSON 漂移。

### 2.2 中期目标

把项目从“脚本集合”升级为“稳定的数据处理工具链”。

重点是：

- 抽出共享库：hash、taxonomy、schema、文件 IO、过滤规则、日志工具。
- 将采集、OCR、结构化、打标签、查询拆成可组合命令。
- 引入 CI：Node 检查、ShellCheck、JSON Schema 校验、数据一致性检查。
- 建立增量索引，提升查询和批量分析性能。

### 2.3 长期目标

把题库建设成“可持续演进的面试知识库”。

重点是：

- 建立知识点规范化体系和实体词典。
- 做语义去重与相似题聚类，而不仅依赖 MD5 exact hash。
- 增加导出、复习、专题分析、Anki/Markdown/CSV 等产品化能力。
- 建立数据来源、隐私、平台规则、保留策略与敏感信息治理机制。

---

## 3. 优先级总表

| 优先级 | 方向 | 目标 | 推荐周期 |
|---|---|---|---|
| P0 | 安全与仓库卫生 | 避免误提交 Cookie、原始请求、临时文件、大文件；补齐 `.gitignore` | 0.5 天 |
| P0 | 脚本鲁棒性 | 移除 `eval`，修复输入转义、错误处理、计数统计、trap 清理 | 1-2 天 |
| P0 | 数据契约 | 增加 JSON Schema，保证 `note_structured` / `note_tagged` 字段稳定 | 1-2 天 |
| P1 | 测试与 CI | 增加 `npm test`、`npm run check`、GitHub Actions | 2-4 天 |
| P1 | 共享模块化 | 抽出 hash、taxonomy、filters、schema、logger | 3-5 天 |
| P1 | 查询增强 | 增量索引、多维排序、导出、分页、JSON/stderr/stdout 统一 | 3-5 天 |
| P2 | 数据质量 | 语义去重、实体标准化、题目质量评分、人工复核队列 | 1-2 周 |
| P2 | 产品化 | 专题复习包、Anki/CSV/Markdown 导出、可视化统计 | 1-2 周 |

---

## 4. P0：安全与仓库卫生

### 4.1 新增 `.gitignore`

当前采集脚本依赖 `raw_curl.txt` 作为浏览器请求模板，且会产生日志、临时任务文件、HTML、图片、OCR 中间结果等大量易变文件。建议立即新增 `.gitignore`，避免误提交敏感内容和大文件。

建议忽略：

```gitignore
# local request templates / secrets
raw_curl.txt
*.cookie
*.cookies
.env
.env.*
!.env.example

# logs / temp files
*.log
*.tmp
failed_list.txt
fetch.log
extract.log

# generated bulky raw artifacts, unless explicitly curated
downloaded_images/
note_detail/

# local runtime
node_modules/
.DS_Store
```

是否忽略 `note_json/`、`note_desc/`、`note_images/`、`note_img_txt/`、`note_structured/`、`note_tagged/` 需要单独决策：

- 如果仓库本身就是私有数据集仓库，可以继续跟踪结构化和标签数据。
- 如果目标是开源或长期协作，建议将原始采集数据、图片、HTML 移出 Git，改用对象存储或 Git LFS。

### 4.2 增加 `.env.example`

把本地依赖和敏感配置统一放到环境变量，示例：

```bash
GEMINI_MODEL_TEXT=gemini-2.5-flash
GEMINI_MODEL_IMAGE=gemini-2.5-flash
XHS_REQUEST_TEMPLATE=raw_curl.txt
XHS_MAX_PAGE=20
XHS_FETCH_SLEEP_MIN=10
XHS_FETCH_SLEEP_MAX=20
```

注意：不要把真实 Cookie、Token、请求签名、浏览器完整 cURL 提交到仓库。

### 4.3 增加敏感信息扫描

建议在 CI 中加入：

- `gitleaks` 或同类 secret scanner。
- 检查 `raw_curl.txt`、`cookie`、`authorization`、`x-s`、`x-t`、`xsec_token` 等关键词是否被提交。
- PR 或 commit 前阻断高风险文件。

### 4.4 合规边界

采集相关逻辑应显式写入 `docs/COMPLIANCE.md`：

- 仅处理自己有权访问和使用的数据。
- 尊重平台规则、频率限制、版权和隐私要求。
- 不提供绕过风控、规避访问控制、批量盗取数据的功能。
- 对个人信息、头像、昵称、URL、Cookie、Token 做最小化保留。
- 建立数据删除/复核机制。

---

## 5. P0：脚本鲁棒性修复

### 5.1 替换 `search.sh` 中的 `eval`

当前 `search.sh` 通过读取 `raw_curl.txt`，再用 `sed` 替换 keyword/page，最后 `eval` 执行拼接命令。风险包括：

- keyword 中包含特殊字符时可能破坏 sed 表达式。
- 请求模板中如果有 shell 特殊字符，`eval` 会扩大执行风险。
- 错误难以定位，也不利于测试。

建议方案：

1. 短期：对 keyword 做严格转义，至少限制危险字符。
2. 中期：改为 Node.js/Python 请求脚本，读取 JSON 配置而不是执行整段 cURL。
3. 长期：抽象为 `scripts/fetch/search.js`，参数化 headers/body，并输出稳定 JSON。

目标命令：

```bash
node scripts/fetch/search.js --keyword "java社招面试" --page 1 --template raw_curl.json
```

验收标准：

- keyword 包含空格、`/`、`&`、中文、引号时不报错。
- 不再使用 `eval`。
- 失败时返回结构化错误：`{ success:false, error_code, message }`。

### 5.2 修复 `fetch.sh` 参数与文件名处理

当前脚本使用 `$1` 作为关键词和输出文件名，建议：

- 增加参数校验：keyword 不能为空。
- 输出文件名做 slug 化，避免空格、斜杠、特殊字符造成路径问题。
- `MAX_PAGE` 改为参数或环境变量。
- 所有变量引用加双引号。
- 输出结构化统计，包括成功页数、失败页、笔记数、输出路径。

目标命令：

```bash
bash fetch.sh --keyword "java 社招 面试" --max-page 20 --out notes/java-she-zhao.txt
```

### 5.3 修复 `html_to_json.sh` 计数统计

当前脚本使用 `find ... | while read` 管道形式，Bash 中 while 子进程导致 `SUCCESS_COUNT` / `FAILED_COUNT` 在循环外可能无法正确保留。

建议改为：

```bash
while IFS= read -r html_file; do
  ...
done < <(find "$SOURCE_DIR" -name "*.html")
```

并增加：

- 失败原因分类。
- 失败列表 JSONL 输出。
- 支持 `--limit`、`--retry-failed`。

验收标准：

- 最终成功/失败数量与实际处理数量一致。
- 空目录、损坏 HTML、无 JSON HTML 都有明确返回码。

### 5.4 强化 `fetch_detail.sh`

建议改进：

- 使用 `trap 'rm -f "$TASK_LIST"' EXIT` 确保临时文件清理。
- 将 `DETAIL_EXEC` 参数化，避免硬编码 `./detail`。
- 增加重试策略，但不要用于规避平台限制；只处理临时网络错误。
- 日志改成 JSON Lines，方便后续统计。
- 记录 HTTP 状态、失败原因、耗时、note_id。
- 已存在 HTML 时记录为 `skipped_existing`，而不是只写普通日志。

### 5.5 加强图片下载脚本

当前 `url_2_img.sh` 只检查 curl 退出码，不检查 HTTP 状态、Content-Type 和文件真实格式。建议：

- 使用 `curl --fail --location --retry 3 --connect-timeout 5`。
- 下载到临时文件，校验大小和类型后再原子 rename。
- 保存 manifest：URL、文件名、sha256、下载时间、状态码。
- 不强制所有图片保存为 `.webp`，应根据 Content-Type 或 URL 判断扩展名。

### 5.6 统一 AI 调用入口

当前文本提取和图片 OCR 脚本直接调用 `gemini`，模型名、Prompt、输出路径、重试策略都散落在脚本中。

建议新增：

```bash
node scripts/ai/run_model.js \
  --mode extract-text \
  --input note_desc/<id>.txt \
  --output question/<id>_desc_questions.txt
```

并支持：

- 统一模型配置。
- 统一超时与重试。
- 统一空输出处理。
- 记录 token/成本/耗时。
- dry-run 模式。
- prompt 模板版本号。

---

## 6. P0：数据契约与 Schema

### 6.1 新增 JSON Schema

建议新增：

```text
schemas/note_structured.schema.json
schemas/note_tagged.schema.json
schemas/query_result.schema.json
```

`note_structured` 必填：

- `note_id`
- `source`
- `company`
- `position`
- `round`
- `level`
- `year`
- `date`
- `questions`

`note_tagged` 必填：

- `note_id`
- `source`
- `company`
- `position`
- `round`
- `level`
- `year`
- `date`
- `tagged_questions`

`tagged_questions[]` 必填：

- `question_id`
- `original_question`
- `domain.l1`
- `domain.l2`
- `question_type`
- `cognitive_depth`
- `tech_entities`
- `business_context`
- `is_valid_for_library`

注意：当前一致性检查里没有把 `business_context` 放入 tagged question 的必填字段，建议补上，以保持和 Skill 契约一致。

### 6.2 增加校验命令

建议新增：

```bash
npm run validate:data
npm run validate:schemas
npm run check:consistency
```

内部调用：

```bash
node scripts/check_consistency.js --json
node scripts/validate_json_schema.js
```

验收标准：

- 所有 `note_structured/*.json` 和 `note_tagged/*.json` 能通过 schema。
- hash 不一致、题目数量不一致、原题漂移都能在 CI 中失败。
- 输出机器可读 JSON 到 stdout，人类报告到 stderr 或文件。

### 6.3 统一年份字段类型

Skill 示例里 `year` 有时是数字，有时是字符串 `"未知"`。建议统一为：

```json
"year": "2025"
```

或：

```json
"year": null
```

推荐使用字符串或 null，避免查询时同时处理 number/string。

---

## 7. P1：工程化基础

### 7.1 增加 `package.json`

当前 Node.js 脚本使用内置模块为主，但仍然应该有统一入口和脚本命令。

建议：

```json
{
  "name": "xhs-interview-library",
  "private": true,
  "type": "commonjs",
  "scripts": {
    "query": "node scripts/query_tagged.js",
    "pipeline": "node scripts/xhs_pipeline.js",
    "check": "node scripts/check_consistency.js",
    "fix:consistency": "node scripts/fix_consistency.js",
    "test": "node --test",
    "lint:shell": "shellcheck *.sh scripts/**/*.sh",
    "validate:data": "node scripts/validate_json_schema.js"
  },
  "devDependencies": {
    "ajv": "^8.0.0"
  }
}
```

### 7.2 增加 Makefile 或 Taskfile

建议提供稳定入口：

```makefile
check:
	npm run validate:data
	npm run check

query-stats:
	node scripts/query_tagged.js stats --filter-valid

pipeline:
	node scripts/xhs_pipeline.js
```

这样 Agent、人工和 CI 都使用同一套命令。

### 7.3 增加 README 的“快速开始”

建议 README 增加：

- 环境依赖安装。
- 最小化查询命令。
- 数据校验命令。
- 新增数据的标准流程。
- 常见错误排查。
- 哪些目录可以提交，哪些目录不能提交。

---

## 8. P1：模块化重构

当前多个脚本重复实现 hash、技术关键词、实体同义词、文件读取、schema 字段判断。建议拆成共享模块：

```text
scripts/lib/
├── hash.js             # computeQuestionHash
├── taxonomy.js         # domain/question_type/cognitive_depth 枚举
├── entity_normalizer.js# tech_entities 标准化
├── filters.js          # company/level/year/round/entity 过滤
├── io.js               # safeReadJson/listJsonIds/writeJson
├── logger.js           # human/jsonl logger
└── schemas.js          # schema loading and validation
```

### 8.1 Hash 统一

目前 hash 规则出现在：

- `generate_hashes.js`
- `xhs_pipeline.js`
- `check_consistency.js`
- `fix_consistency.js`
- Skill 文档中的 Python 命令

建议以 `scripts/lib/hash.js` 为唯一实现，并在所有 Node 脚本中引用。

验收标准：

- `node --test test/hash.test.js` 覆盖中文、英文、标点、大小写、空格。
- 所有脚本生成的 question_id 完全一致。

### 8.2 Taxonomy 统一

目前 domain/question_type/cognitive_depth 强枚举主要写在 Skill 文档里，代码端只是被动接收。

建议新增：

```text
data/taxonomy/domain.json
data/taxonomy/question_type.json
data/taxonomy/entity_synonyms.json
```

并让：

- `xhs_tagger` Skill 引用该文件。
- `check_consistency.js` 校验枚举合法性。
- `fix_master_sweep.js` 使用同一份 `entity_synonyms.json`。
- `query_tagged.js stats` 可以按标准 taxonomy 输出。

### 8.3 合并清洗脚本

当前 `fix_synonyms.js` 和 `fix_master_sweep.js` 存在明显职责重叠。建议合并为：

```bash
node scripts/normalize_entities.js --dry-run
node scripts/normalize_entities.js --apply
node scripts/normalize_entities.js --rebuild-index
```

验收标准：

- 所有实体标准化逻辑来源于 `data/taxonomy/entity_synonyms.json`。
- 支持 dry-run 展示变更 diff。
- 支持只处理指定 note_id。

---

## 9. P1：查询能力增强

### 9.1 增量索引

`query_tagged.js` 每次运行都会同步读取 `note_tagged/*.json` 并 flatten 全量题目。当前数据量不大时可接受，但随着题库增长，建议生成索引：

```text
data/index/questions.json
数据字段：question_id、original_question、company、level、year、round、domain、question_type、cognitive_depth、tech_entities、note_id
```

新增命令：

```bash
node scripts/build_index.js
node scripts/query_index.js entity --value Redis --filter-valid --limit 20
```

验收标准：

- build_index 可重复执行。
- index 中记录来源文件和 mtime/hash，支持增量更新。
- 查询结果与原 `query_tagged.js` 在同条件下数量一致。

### 9.2 输出协议统一

建议所有查询类脚本遵循：

- stdout：机器可读 JSON。
- stderr：人类摘要、日志、进度。
- `--format json|table|markdown`：控制展示格式。
- `--limit` / `--offset`：分页。
- `--sort`：支持按公司、年份、题型、热度排序。

当前 `check_consistency.js` 把人类报告写 stdout、JSON 写 stderr，不利于程序化集成，建议调整或增加 `--json` 模式。

### 9.3 README 与代码命令保持一致

`query_tagged.js` 已支持 `question --id <id>`，但 README 的命令表主要列出 domain/company/type/depth/entity/note/stats/hotspot。建议补齐 README 和 `xhs_query` Skill，让用户可以直接查单题。

### 9.4 高级查询

建议新增：

- `similar --id <question_id>`：查相似题。
- `cluster --entity Redis`：按技术实体聚类。
- `company-profile --name 字节 --filter-valid`：输出公司考点画像。
- `study-plan --company 美团 --level 社招`：生成复习优先级。
- `export --format csv|anki|markdown`：导出复习资料。

---

## 10. P1：测试与 CI

### 10.1 单元测试

建议使用 Node 内置 test runner：

```text
test/
├── hash.test.js
├── query_args.test.js
├── query_filters.test.js
├── pipeline_score.test.js
├── entity_normalizer.test.js
└── schema_validation.test.js
```

关键测试点：

- hash 稳定性。
- `--slim` 输出只包含必要字段。
- company/entity 模糊匹配。
- `--filter-valid`、`--filter-year`、`--filter-round` 组合过滤。
- 空目录、坏 JSON、缺字段时的行为。
- pipeline scoring 对 JD、offer、纯分享、技术面经的分类。

### 10.2 Fixture 数据

新增小规模测试数据：

```text
test/fixtures/
├── note_structured/demo_valid.json
├── note_structured/demo_empty.json
├── note_tagged/demo_valid.json
├── note_tagged/demo_hash_mismatch.json
└── note_tagged/demo_schema_missing.json
```

测试不要依赖真实私有数据，避免 CI 泄露。

### 10.3 GitHub Actions

建议新增：

```yaml
name: check
on:
  pull_request:
  push:
    branches: [master]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npm test
      - run: npm run validate:data
      - run: npm run check
      - run: shellcheck *.sh || true
```

初期可以把 ShellCheck 设为 warning，待脚本修复后改为强制失败。

---

## 11. P2：数据质量提升

### 11.1 从 exact hash 到语义去重

当前 `question_id` 基于问题文本归一化后的 MD5，适合 exact dedupe，但无法处理：

- “Redis 持久化有哪些？” vs “Redis 的 RDB 和 AOF 区别？”
- “讲讲 HashMap 底层” vs “HashMap 原理是什么？”
- “手写快排” vs “算法：快速排序”

建议新增：

- `canonical_question`：标准题干。
- `semantic_group_id`：语义聚类 ID。
- `duplicate_of`：可选，指向主问题 ID。
- `similarity_score`：相似度。

### 11.2 题目质量评分

新增字段或派生索引：

```json
{
  "quality_score": 0.92,
  "quality_reasons": ["技术实体明确", "题型明确", "非项目私有追问"]
}
```

用途：

- 过滤无效题。
- 优先生成复习材料。
- 发现需要人工复核的题。

### 11.3 人工复核队列

新增：

```text
review/queue/
├── needs_tag_review.json
├── needs_dedupe_review.json
└── needs_metadata_review.json
```

触发条件：

- company/year/round 无法推断。
- domain.l1/l2 不合法。
- tech_entities 为空但题目有效。
- 同一 note 中题目数量异常。
- OCR 文本太短或图片数量较多但没有题目。

### 11.4 数据版本化

建议给每批数据处理增加批次号：

```json
{
  "pipeline_version": "2026.06.30",
  "prompt_version": "xhs_extractor_v2",
  "taxonomy_version": "domain_v1",
  "processed_at": "2026-06-30T00:00:00Z"
}
```

这样后续可以追踪：某次 prompt 或 taxonomy 变化导致的数据漂移。

---

## 12. P2：采集与处理链路改造

### 12.1 把采集与数据处理解耦

建议分层：

```text
collect/       # 搜索、详情抓取、图片下载，仅负责原始数据
extract/       # HTML/JSON/正文/图片 OCR 解析
structure/     # AI 结构化
label/         # AI 打标签
data/          # 索引、taxonomy、schema
review/        # 复习答案、人工复核
```

### 12.2 增加任务状态机

当前依靠目录是否存在判断进度。建议建立 `data/tasks.jsonl` 或 SQLite：

```json
{
  "note_id": "...",
  "status": "tagged",
  "has_desc": true,
  "has_images": true,
  "has_ocr": true,
  "structured": true,
  "tagged": true,
  "last_error": null,
  "updated_at": "2026-06-30T00:00:00Z"
}
```

状态：

```text
discovered → fetched → parsed → ocr_done → structured → tagged → indexed → reviewed
```

好处：

- 更容易断点续跑。
- 更容易查询失败任务。
- 不需要在每个脚本中重复扫描多个目录。

### 12.3 明确重试与限流策略

建议只对临时网络错误做有限重试，且遵守平台规则与本地配置。

配置示例：

```json
{
  "retry": {
    "max_attempts": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000
  },
  "rate_limit": {
    "min_interval_ms": 10000,
    "batch_pause_ms": 300000,
    "batch_size": 20
  }
}
```

---

## 13. P2：产品化能力

### 13.1 复习包导出

新增命令：

```bash
node scripts/export_study_pack.js --company 美团 --level 社招 --format markdown
node scripts/export_study_pack.js --entity Redis --format anki
node scripts/export_study_pack.js --domain JVM --format csv
```

输出：

```text
exports/
├── 美团_社招_复习包.md
├── Redis_Anki.csv
└── JVM_questions.csv
```

### 13.2 公司画像

新增：

```bash
node scripts/company_profile.js --name 字节 --filter-valid
```

输出：

- 高频技术实体 Top 20。
- domain 分布。
- question_type 分布。
- 年份/轮次/层级分布。
- 高频重复题。
- 推荐复习路径。

### 13.3 专题分析

结合 `xhs_batch_analyzer`：

- 对某个实体自动生成答案。
- 跳过已存在分析文件。
- 输出统一模板。
- 记录引用题目来源。

建议增加：

```bash
node scripts/analyze_topic.js --entity Redis --limit 10 --skip-existing
```

---

## 14. 建议实施路线图

### 阶段 0：半天内完成

目标：降低误提交和脚本风险。

任务：

- 新增 `.gitignore`。
- 新增 `.env.example`。
- README 增加“敏感文件不要提交”说明。
- `search.sh` 标注弃用或增加安全警告。
- 新增 `docs/COMPLIANCE.md`。

验收：

- `git status` 不再显示日志、临时文件、raw_curl、下载图片等易变文件。
- 新用户能通过 README 知道哪些文件不能提交。

### 阶段 1：1-2 天

目标：让现有脚本更稳。

任务：

- 修复 `html_to_json.sh` 的计数问题。
- `fetch.sh` 参数化与文件名安全化。
- `fetch_detail.sh` 增加 trap、结构化日志、错误分类。
- `url_2_img.sh` 增加 HTTP/Content-Type 校验。
- AI 调用脚本统一模型配置和重试。

验收：

- 空目录、错误文件、重复运行均不会异常污染状态。
- 所有脚本都有明确返回码。
- 失败任务可复查、可重跑。

### 阶段 2：3-5 天

目标：建立工程化底座。

任务：

- 新增 `package.json`。
- 抽出 `scripts/lib/hash.js`、`io.js`、`filters.js`。
- 新增 JSON Schema。
- 新增基础单元测试。
- 改造 `check_consistency.js --json`。
- GitHub Actions 初版。

验收：

- `npm test` 通过。
- `npm run validate:data` 通过。
- PR 自动检查基础数据一致性。

### 阶段 3：1-2 周

目标：提升数据质量与查询能力。

任务：

- 建立 entity/taxonomy 配置文件。
- 合并实体清洗脚本。
- 新增 `build_index.js`。
- `query_tagged.js` 支持 `--limit`、`--offset`、`--format`。
- 新增公司画像和复习包导出。

验收：

- 查询命令对大数据量仍稳定。
- 查询结果可导出为 Markdown/CSV/Anki。
- 实体规范化有可追踪配置。

### 阶段 4：1 个月+

目标：从题库升级为知识库。

任务：

- 语义去重与相似题聚类。
- 自动生成专题答案并建立引用关系。
- 人工复核队列。
- 数据版本化与 prompt/taxonomy 版本追踪。
- 可视化报表或轻量 Web UI。

验收：

- 能按公司/技术实体自动生成复习计划。
- 相似题聚类可解释。
- 数据质量问题可追踪、可修复、可回滚。

---

## 15. 具体待办清单

### P0 待办

- [ ] 添加 `.gitignore`，至少忽略 `raw_curl.txt`、`.env`、日志、临时文件、下载图片。
- [ ] 添加 `.env.example`。
- [ ] 添加 `docs/COMPLIANCE.md`。
- [ ] 移除或替换 `search.sh` 的 `eval`。
- [ ] 修复 `html_to_json.sh` 的计数统计。
- [ ] 为 `fetch.sh` 增加 keyword 参数校验和输出文件名安全化。
- [ ] 为 `fetch_detail.sh` 增加 `trap` 清理和 JSONL 日志。
- [ ] 为 `url_2_img.sh` 增加 HTTP 状态和文件类型校验。
- [ ] 新增 `schemas/note_structured.schema.json` 和 `schemas/note_tagged.schema.json`。

### P1 待办

- [ ] 添加 `package.json` 和标准 npm scripts。
- [ ] 添加 `test/hash.test.js`。
- [ ] 添加 `test/query_filters.test.js`。
- [ ] 添加 `test/pipeline_score.test.js`。
- [ ] 抽出 `scripts/lib/hash.js`。
- [ ] 抽出 `scripts/lib/io.js`。
- [ ] 抽出 `scripts/lib/taxonomy.js`。
- [ ] 改造 `check_consistency.js` 支持 `--json`。
- [ ] 合并 `fix_synonyms.js` 与 `fix_master_sweep.js`。
- [ ] 建立 GitHub Actions 检查。

### P2 待办

- [ ] 建立 `data/taxonomy/entity_synonyms.json`。
- [ ] 建立 `data/index/questions.json`。
- [ ] 新增 `scripts/build_index.js`。
- [ ] 新增 `scripts/export_study_pack.js`。
- [ ] 新增 `scripts/company_profile.js`。
- [ ] 新增语义去重字段：`canonical_question`、`semantic_group_id`。
- [ ] 新增人工复核队列。
- [ ] 新增数据版本字段：`pipeline_version`、`prompt_version`、`taxonomy_version`、`processed_at`。

---

## 16. 建议的第一个 PR 范围

第一个 PR 不建议做大重构，只做低风险基础建设：

标题：`chore: add repo hygiene, schemas and basic checks`

包含：

1. `.gitignore`
2. `.env.example`
3. `docs/COMPLIANCE.md`
4. `schemas/note_structured.schema.json`
5. `schemas/note_tagged.schema.json`
6. `package.json`
7. `scripts/lib/hash.js`
8. `test/hash.test.js`
9. `README.md` 增加“运行检查”和“敏感文件”章节

不包含：

- 不改现有 `note_*` 数据。
- 不改采集策略。
- 不新增复杂业务功能。

验收命令：

```bash
npm test
npm run validate:data
node scripts/check_consistency.js
```

---

## 17. 风险与注意事项

1. **采集合规风险**  
   优化方向应聚焦稳定性、可维护性、错误处理和数据最小化，不应增加绕过平台访问控制或规避风控的能力。

2. **数据隐私风险**  
   原始 HTML、图片、链接、请求模板可能包含个人信息或敏感访问凭证。建议最小化保存，必要时脱敏。

3. **AI 输出漂移风险**  
   prompt、模型版本、taxonomy 改动会导致标签不一致。必须记录版本，并用 schema/consistency check 把漂移显性化。

4. **脚本重构风险**  
   现有脚本虽然分散，但已能完成任务。建议先加测试和校验，再逐步抽模块，避免一次性大改破坏流程。

5. **大文件风险**  
   如果继续把图片、HTML 和中间数据放在 Git 中，仓库体积会持续增加。建议尽早决策哪些数据进入 Git，哪些进入外部存储。

---

## 18. 结论

`xhs` 已经具备一个有价值的面经题库闭环：采集、结构化、打标签、查询、分析都已经有雏形。下一步最值得做的不是马上堆功能，而是补齐工程化底座：安全边界、依赖入口、schema、测试、CI、共享模块和结构化日志。

建议按以下顺序推进：

```text
仓库卫生与安全 → 脚本鲁棒性 → Schema/测试/CI → 模块化 → 索引与高级查询 → 知识库产品化
```

这样可以在不破坏现有数据资产的前提下，让后续每一次采集、提取、打标、查询和分析都更加稳定、可复现、可维护。
