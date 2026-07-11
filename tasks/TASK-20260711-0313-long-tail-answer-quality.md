# 长尾答案全量升级到精选质量

- Root ID: `TASK-20260711-0313-long-tail-answer-quality`
- Status: `in_progress`
- Created: `2026-07-11 03:13 Asia/Shanghai`
- Source request: 制定长尾答案重做的每个阶段目标，最终所有长尾答案都要和精选答案质量保持一致。
- Task file: `tasks/TASK-20260711-0313-long-tail-answer-quality.md`

## Objective

把当前 9,160 份 `long_tail_baseline` 从“结构完整的复习底稿”升级为与 100 份精选答案相同质量等级的答案资产。最终每一道有效原题都必须通过唯一 Canonical 到达一份事实可信、直接回答、题型完整、可口述、可追问、可验证的答案；重复 Canonical 应先合并，不要求保留 9,160 份彼此重复的答案文件。任何答案只有通过确定性校验、独立语义审查和证据审查后才能标记为 `ready` / `curated`。

## Context

- 当前权威数据为 `data/questions/questions.jsonl`、`data/questions/canonical_questions.jsonl` 和 `review/answers/*.md`。
- 当前共有 9,260 个 Canonical、9,260 份 `ready` 答案，其中 100 份精选答案、9,160 份 `long_tail_baseline`。
- 当前 9,043 个 Canonical 的 `frequency=1`；重答前和每个批次内必须复核题簇边界，避免为同义题重复编写答案。
- 长尾已知缺陷基线：1,818 份兜底核心结论、580 份无专属技术判断的通用场景答案、735 份 Coding 答案仅 31 种代码块，其中 417 份 `ProblemSpec`、36 份通用 SQL、27 份未实现 DP 骨架。
- `node scripts/xhs.js answer validate --strict --noWrite` 只验证章节和 TODO，不证明事实正确、内容相关或代码可运行。
- 现有语义标准在 `docs/refactor/09_answer_content_standard.md`；100 份精选答案是风格与深度基准，但仍需重新事实审计，不能未经校准直接视为绝对真值。
- 每批固定最多 10 个 Canonical。批次必须完整经过“题簇复核 → 题型确认 → 研究 → 编写候选 → 独立审查 → 硬性校验 → 晋级 → 复习反馈”，不得先批量覆盖答案再补审查。
- 版本敏感结论优先使用官方文档、标准、源码或论文等第一手材料；每份答案的核验依据写入 `review/evidence/{canonical_id}.json`，正文保持适合口述。
- Skill 放在 `.agents/skills/xhs-answer-curator/`，负责可重复执行流程；质量规则、状态模型、CLI 校验和 CI 闸门必须落在仓库代码中，不能只依赖提示词。

## Quality Contract

每份答案按 100 分审查：事实与证据 25、直接性与相关性 20、题型专项完整性 20、原理与因果链 15、边界与取舍 10、追问质量 5、口述质量 5。

晋级 `ready` / `curated` 必须同时满足：

- 总分不低于 90；事实与证据不低于 23/25；直接性与相关性不低于 18/20；其他单项不低于该项满分的 80%。
- 零硬失败：题型错误、答非所问、跨主题污染、事实无依据、版本结论无边界、虚构经历、模板追问、占位代码、不可运行实现、未覆盖原题变体中的任一项均直接阻断晋级。
- 至少 3 个题目专属追问且有短答，其中至少 1 个检查边界/失败路径；不得用全库通用追问凑数。
- Coding/SQL 必须提供本题实现、复杂度和边界用例，并通过编译/解析及测试；Project/Behavior 必须保持真实材料边界，缺少个人事实时只能给表达框架。
- 编写者与审查者必须是相互隔离的两个审查轮次；审查者只接收原题、Canonical、候选答案和证据，不接收编写者的自我解释。无法取得独立审查时保持 `needs_update`。
- 首个 60 题试点进行 100% 人工抽查；稳定后每批随机人工抽查至少 20%。任一硬失败使整批回退并扩大为 100% 复核。

## Final Proof

只有以下证据全部成立，根任务才能标记 `done`：

- 所有有效 Question 均绑定唯一 Canonical；所有重复/包含/边界冲突均已解决或有人工确认记录。
- 所有最终 Canonical 均有且仅有一份 `status=ready`、`quality_tier=curated` 的答案；`long_tail_baseline`、`draft`、`needs_update`、missing 和 orphan 全部为 0。
- 每份答案均存在通过 schema 的 evidence sidecar、独立审查记录、评分和版本/来源核验时间。
- 全库结构、语义、重复度、代码、引用、可达性和状态同步校验全部通过。
- 六类答案均完成真实复述抽样；连续四周没有出现硬失败或质量覆盖率回退。

## Execution Rules

- Execute subtasks in listed order unless dependencies say otherwise.
- Update this file after each subtask with status, notes, validation, changed files, and commit hash.
- Commit only files related to the completed subtask.
- Do not mark a subtask `done` without validation or a documented reason validation was skipped.
- 不得以“结构校验通过”“文件数覆盖 100%”代替语义质量完成证明。
- 不得直接覆盖 100 份精选答案；先审计，只有发现明确缺陷时才单独升级版本。
- 候选答案在晋级前写入候选区或临时文件；失败候选不得污染 `review/answers/`。
- 每次晋级最多 10 份答案并单独提交；任何失败先修复本批，不能带债进入下一批。
- 队列中的 Canonical 合并后保留 Question 可达性与迁移记录，删除重复答案前先验证引用和 ReviewProgress 迁移。

## Stage Map

| 阶段 | 目标 | 退出条件 |
|---|---|---|
| S0 | 纠正质量状态与指标口径 | 只有语义合格答案计为 curated-ready；9,160 份长尾进入待升级队列 |
| S1 | 校准精选基准与评分器 | 100 份精选全部重新审计通过；正负样本能被质量闸门稳定区分 |
| S2 | 建立 Skill、候选区、证据与语义校验 | 单题可完整执行且失败不写入正式答案 |
| S3 | 复核 Canonical 与题型 | 全量稳定队列生成；每题都有唯一批次、明确题型和去重状态 |
| S4 | 60 题六类型试点 | 每类型 10 题均达到门槛，人工抽查无硬失败 |
| S5 | Coding/SQL 全量升级 | 所有最终 Coding/SQL 可运行、可测试且有本题实现 |
| S6 | Concept 全量升级 | 所有 Concept 具备统一比较维度、选择条件、反例和专属追问 |
| S7 | Mechanism 全量升级 | 所有 Mechanism 具备数据结构、主流程、状态变化、开销和版本边界 |
| S8 | Scenario 全量升级 | 所有 Scenario 具备容量、数据流、一致性、故障、观测和替代方案 |
| S9 | Project/Behavior 全量升级 | 所有个人题保持真实性边界并提供可填充表达框架 |
| S10 | 余量清零和全库证明 | 所有有效 Question 到 curated-ready Answer 可达，质量债为 0 |
| S11 | 四周复习稳定性验证 | 连续四周无硬失败、无覆盖回退，反馈已闭环到答案版本 |

## 阶段执行目标与产物

每个阶段只在其退出条件有直接证据时结束；结构校验通过、文件存在或候选已生成，都不能单独证明阶段完成。

### S4：60 题六类型试点

- 目标：验证“题簇复核 → 一手研究 → 候选 → evidence → 隔离审查 → 机器审计 → 人工签核 → 原子晋级”的端到端流程，覆盖六类题各 10 题。
- 输入：冻结的 `answer_pilot_set.json`、Canonical/来源问法、真实项目材料（Project/Behavior）。
- 产物：候选答案、evidence sidecar、独立审查记录、候选审计、人工签核记录和试点台账。
- 退出：60 题均有明确处置；可晋级题经过人工签核，失败题有可追溯 blocker，且试点不存在硬失败。

### S5：Coding / SQL 全量升级

- 目标：让每道 Coding/SQL 都有题目专属、可运行的 Java 或 SQL，而非通用骨架。
- 产物：输入输出约束、不变量、复杂度、变体、至少三个边界用例和可执行测试。
- 退出：所有 Coding/SQL 通过编译或解析与边界测试，且没有占位实现或跨题代码复用。

### S6：Concept 全量升级

- 目标：让概念与对比题能按统一维度讲清定义、选择条件、代价与反例。
- 产物：直接结论、统一比较矩阵/维度、适用与不适用边界、题目专属追问和版本证据。
- 退出：每题可在口述中完成“定义—比较—选型—反例”，不以分类方法论代替答案。

### S7：Mechanism 全量升级

- 目标：让机制题提供从入口到结果的可核验因果链。
- 产物：参与组件或核心结构、状态变化、并发/一致性保证、资源成本、故障路径、版本边界与第一手证据。
- 退出：每题的关键事实均可映射到规范、官方文档、源码或可复现实验；没有无依据的性能或版本外推。

### S8：Scenario 全量升级

- 目标：让系统设计题形成可落地、可压测、可回滚的方案，而不是组件清单。
- 产物：需求/SLO/容量假设、数据流、数据模型与幂等、超时重试降级补偿灾备、观测压测灰度、替代方案与代价。
- 退出：每题覆盖成功与失败路径，容量和一致性结论均有明确前提或证据。

### S9：Project / Behavior 全量升级

- 目标：在不虚构个人经历的前提下，把真实项目和行为材料组织为可口述答案。
- 输入：用户提供的背景、职责、约束、个人动作、原始证据、结果和复盘；缺失时仅保留待填框架。
- 产物：真实 STAR/项目时间线、个人责任边界、证据链接或占位清单、反思与改进。
- 退出：所有第一人称、规模和结果都能由用户材料核对；没有材料的题明确保持 `needs_update`。

### S10：余量清零与全库完成证明

- 目标：将所有有效 Question 收敛到唯一 Canonical 与唯一 curated-ready 正式答案。
- 产物：全库 evidence、独立审查与评分、可达性/覆盖/重复度/状态同步审计、质量债清单为零的证明。
- 退出：`long_tail_baseline`、`draft`、`needs_update`、missing、orphan 均为 0，所有全库校验通过。

### S11：四周复习稳定性验证

- 目标：验证答案不仅能通过一次审查，也能在真实复述和持续反馈中稳定。
- 产物：每周抽样、答不出/含糊/事实疑问/过长/追问断裂记录、修订版本和趋势报告。
- 退出：连续四周无硬失败、无覆盖回退，所有反馈均已闭环到答案或明确处置。

## Tasks

### `TASK-20260711-0313-long-tail-answer-quality-T01` S0：建立真实质量基线

- Status: `in_progress`
- Depends on: `none`
- Goal: 让状态、报告和文档真实区分“可访问底稿”与“语义合格答案”，停止把 9,160 份长尾底稿计为精选质量 ready。
- Files likely touched: `scripts/lib/answer_store.js`, `scripts/content/check_answer_coverage.js`, `data/manifests/quality/answer_coverage_report.json`, `docs/refactor/08_content_building_goals.md`
- Validation: `npm test && node scripts/xhs.js answer validate --strict --noWrite && node scripts/content/check_answer_coverage.js --check`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T01-S01` 固化质量基线报告

- Status: `done`
- Goal: 生成可重复的长尾缺陷基线，覆盖兜底结论、通用场景、重复追问、代码占位、题型分布和正文重复度。
- Steps:
  - 新增只读质量盘点命令，按 `quality_tier` 输出机器可读 JSON。
  - 将本任务 Context 中的已知数字写成回归断言，后续升级时只允许缺陷数下降。
  - 报告记录生成时间、输入文件 hash 和统计口径。
- Expected files: `scripts/content/analyze_answer_semantics.js`, `data/manifests/quality/answer_semantic_baseline.json`, `test/answer_semantics.test.js`
- Validation: `node scripts/content/analyze_answer_semantics.js --check && node --test test/answer_semantics.test.js` -> passed
- Commit: `9e4c090c`
- Changed files: `scripts/content/analyze_answer_semantics.js`, `data/manifests/quality/answer_semantic_baseline.json`, `test/answer_semantics.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 冻结 2026-07-11 全量语义缺陷基线与输入 hash；`--check` 只阻断缺陷回升，允许后续重写持续降低缺陷数。

##### `TASK-20260711-0313-long-tail-answer-quality-T01-S02` 修正 ready 与 quality_tier 语义

- Status: `done`
- Goal: 在代码和测试中明确 `ready` 只代表已经达到精选语义质量，并提供可检查的迁移命令。
- Steps:
  - 为 100 份精选答案定义显式 `quality_tier=curated` 元数据规则。
  - 实现幂等迁移命令：精选补齐 tier，`long_tail_baseline` 迁移为 `needs_update`，保留文件和来源定位。
  - 更新 coverage/report/review 口径，分别报告 baseline、needs_update 和 curated-ready。
  - 增加 `--check` / `--noWrite`，先证明迁移范围恰好是 100 + 9,160，不能误改后续新增答案。
- Expected files: `scripts/commands/answer.js`, `scripts/lib/answer_store.js`, `scripts/content/check_answer_coverage.js`, `test/answer_quality_migration.test.js`
- Validation: `node --test test/answer_quality_migration.test.js test/long_tail_answers.test.js && node scripts/xhs.js answer quality-migrate --check --noWrite && npm test` -> passed (54 tests)
- Commit: `e1e7f62a`
- Changed files: `scripts/commands/answer.js`, `scripts/lib/answer_store.js`, `scripts/content/check_answer_coverage.js`, `scripts/content/generate_long_tail_answers.js`, `test/answer_quality_migration.test.js`, `test/long_tail_answers.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 新增 fail-closed、幂等的 `answer quality-migrate` dry-run/执行接口；精确识别 100 份 curated 与 9,160 份 baseline。Coverage 现在独立报告 curated-ready、baseline、needs_update 和 semantic_complete，长尾生成器不再产出 ready。

##### `TASK-20260711-0313-long-tail-answer-quality-T01-S03` 执行质量状态迁移

- Status: `done`
- Goal: 原子执行经过 dry-run 验证的状态迁移，并同步 Canonical 与质量报告。
- Steps:
  - 执行 `answer quality-migrate`，为 100 份精选补齐 curated tier，将 9,160 份长尾迁移为 needs_update。
  - 执行 `answer sync` 同步 Canonical 状态并记录迁移 manifest。
  - 重建 coverage/quality report，确认答案文件没有丢失且 curated-ready 恰好为 100。
- Expected files: `review/answers/*.md`, `data/questions/canonical_questions.jsonl`, `data/manifests/runs/latest_answer_sync.json`, `data/manifests/quality/answer_coverage_report.json`
- Validation: `node scripts/xhs.js answer validate --strict --noWrite && node scripts/content/check_answer_coverage.js --check && node scripts/xhs.js canonical check --noWrite && node scripts/content/generate_long_tail_answers.js --check` -> passed
- Commit: `f2b29a8c`
- Changed files: `review/answers/*.md` (9,260 metadata-only changes), `data/questions/canonical_questions.jsonl`, `data/manifests/quality/answer_coverage_report.json`, `data/manifests/runs/latest_answer_quality-migrate.json`, `data/manifests/runs/latest_answer_sync.json`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 100 份精选答案现为 ready/curated；9,160 份长尾现为 needs_update/long_tail_baseline。正文未改，Canonical 状态已同步；coverage 显式报告 curated_ready=100、baseline=9160、semantic_complete=false。

##### `TASK-20260711-0313-long-tail-answer-quality-T01-S04` 重开内容阶段状态

- Status: `done`
- Goal: 让项目文档不再把结构覆盖当作全量答案质量完成。
- Steps:
  - 将原 C8 的“全量答案覆盖完成”改为 baseline coverage 已完成、semantic curated coverage 待完成。
  - 在质量报告中新增 `curated_ready_rate`、`baseline_count`、`needs_update_count` 和 `semantic_hard_fail_count`。
  - 保留历史交付记录，但显式注明旧口径不能证明语义完成。
- Expected files: `docs/refactor/08_content_building_goals.md`, `review/plans/c8_full_answer_coverage.md`, `scripts/commands/report.js`
- Validation: `node --test test/report.test.js test/report_no_fail.test.js && node scripts/xhs.js report quality --noWrite --noFail` -> passed; report correctly returns `ok=false`, `semantic_complete=false`
- Commit: `abd859f3`
- Changed files: `scripts/commands/report.js`, `test/report.test.js`, `docs/refactor/08_content_building_goals.md`, `review/plans/c8_full_answer_coverage.md`, `review/plans/content_inventory.md`, `data/manifests/reports/quality_report.json`, `review/plans/quality_report.md`, `data/manifests/runs/latest_report_quality.json`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: C8 已按真实语义重新打开，C9 等待 curated-ready 100% 后再执行。总质量报告现在显示 curated-ready=100、baseline/needs_update/semantic_hard_fail=9160，并把整体状态标为 NEEDS ATTENTION。

### `TASK-20260711-0313-long-tail-answer-quality-T02` S1：校准精选答案与统一质量合同

- Status: `in_progress`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T01`
- Goal: 把“和精选答案一致”转换为可评分、可拒绝、可复现的质量合同，并先证明 100 份精选答案自身达到该合同。
- Files likely touched: `config/answer_quality.json`, `docs/refactor/09_answer_content_standard.md`, `review/evidence/*.json`, `test/fixtures/answer_quality/*`
- Validation: `node scripts/xhs.js answer validate --strict --noWrite && node --test test/answer_quality_config.test.js`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T02-S01` 落盘评分规则和硬失败

- Status: `done`
- Goal: 将本任务 Quality Contract 写成机器可读规则和人工审查表。
- Steps:
  - 定义六类题型的必答项、评分权重、最低分和硬失败。
  - 定义证据来源等级、版本敏感规则、引用日期和不确定结论处理方式。
  - 定义重复内容、通用追问、跨主题污染和虚构经历的判定标准。
- Expected files: `config/answer_quality.json`, `docs/refactor/09_answer_content_standard.md`
- Validation: `node scripts/xhs.js validate all --noWrite && node --test test/answer_quality_config.test.js` -> passed
- Commit: `d31198a9`
- Changed files: `config/answer_quality.json`, `docs/refactor/09_answer_content_standard.md`, `test/answer_quality_config.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 固化 100 分七维评分、90 分晋级线、13 项硬失败、第一手证据优先级、隔离审查输入、六题型专项要求与 10 题批次规则；无法核验统一保持 needs_update。

##### `TASK-20260711-0313-long-tail-answer-quality-T02-S02` 全量复核 100 份精选答案

- Status: `in_progress`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T03-S04`
- Goal: 让精选集合成为经过当前标准校准的正样本，而不是历史上自称精选的样本。
- Steps:
  - 按六类题型重新分类并审查全部 100 份答案。
  - 对事实、版本、直接性或追问存在缺陷的答案单独升级版本。
  - 为每份答案生成 evidence sidecar 和评分记录。
  - 只有 100/100 通过合同后才进入后续试点。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/curated_answer_audit.json`
- Validation: `manual check: 100/100 curated rows have completed rubric, evidence, reviewer decision, and zero hard failures`
- Commit: `pending`
- Notes: 100 篇历史精选已全部完成审计状态校准。AOF、AQS、Bean、binlog 由独立审查发现可追溯的事实/版本/证据硬失败；其余 96 篇没有 evidence sidecar，均以确定性 `missing_evidence` 门禁在不改正文的前提下分批原子降级。当前 `curated_answer_audit.json` 为 0/100 通过、100/100 `needs_update/curated_audit_failed`；严格 Answer 与 Canonical 结构校验仍通过。历史精选不再被错误用作正样本，后续必须从候选、来源、独立审查和人工签核重新建立合格集合。

##### `TASK-20260711-0313-long-tail-answer-quality-T02-S03` 建立正负评测集

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T02-S02`, `TASK-20260711-0313-long-tail-answer-quality-T03-S04`
- Goal: 用精选正样本和已知长尾缺陷负样本校准质量闸门，防止“所有答案都高分”的失效评审。
- Steps:
  - 正样本使用经复核的 100 份精选答案。
  - 每类选择至少 20 个负样本，覆盖答非所问、模板化、跨主题污染、代码占位、版本错误和虚构风险。
  - 评审器必须接受全部正样本，并拒绝至少 95% 负样本；所有硬失败负样本必须 100% 拒绝。
- Expected files: `test/fixtures/answer_quality/positive.jsonl`, `test/fixtures/answer_quality/negative.jsonl`, `test/answer_semantic_audit.test.js`
- Validation: `node --test test/answer_quality_config.test.js`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T03` S2：建立仓库级 Skill 与质量流水线

- Status: `done`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T02-S01`
- Goal: 提供可重复的单题/批次编写流程，候选答案只有通过所有闸门后才原子晋级正式答案。
- Files likely touched: `.agents/skills/xhs-answer-curator/`, `AGENTS.md`, `scripts/commands/answer.js`, `scripts/lib/answer_quality.js`, `test/answer_quality.test.js`
- Validation: `python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/xhs-answer-curator && npm test`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T03-S01` 创建 xhs-answer-curator Skill

- Status: `done`
- Goal: 用仓库 Skill 固化“准备上下文、研究、编写、独立审查、修订、晋级”的低自由度流程。
- Steps:
  - 使用 skill-creator 初始化 `.agents/skills/xhs-answer-curator/`，名称固定为 `xhs-answer-curator`。
  - `SKILL.md` 只保留执行顺序、失败处理和资源路由；详细规则引用仓库标准，不复制大段知识。
  - Skill 明确禁止复用长尾正文作为事实来源，允许读取精选答案作为风格基准。
  - Skill 要求独立审查轮次；审查失败最多修订两次，仍失败则保持 `needs_update`。
  - 生成并校验 `agents/openai.yaml`，默认提示显式包含 `$xhs-answer-curator`。
- Expected files: `.agents/skills/xhs-answer-curator/SKILL.md`, `.agents/skills/xhs-answer-curator/agents/openai.yaml`
- Validation: `python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/xhs-answer-curator` -> passed (`Skill is valid!`)
- Commit: `8060a81e`
- Changed files: `.agents/skills/xhs-answer-curator/SKILL.md`, `.agents/skills/xhs-answer-curator/references/repo-map.md`, `.agents/skills/xhs-answer-curator/agents/openai.yaml`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: Skill 明确旧长尾不可作为事实来源、候选区隔离、第一手证据、独立 reviewer/subagent、最多两轮修订、90 分和零硬失败晋级；命令缺失时要求先实现而非手工模拟写状态。

##### `TASK-20260711-0313-long-tail-answer-quality-T03-S02` 增加仓库持久规则

- Status: `done`
- Goal: 确保任何会修改 `review/answers/` 的 Agent 都执行同一质量流程。
- Steps:
  - 在根 `AGENTS.md` 中要求答案变更使用 `xhs-answer-curator`、禁止直接标 ready、必须运行语义校验。
  - 记录每批 10 题限制、候选区路径和提交规则。
  - 保持 AGENTS 简短，详细内容由 Skill 和质量标准承载。
- Expected files: `AGENTS.md`
- Validation: `manual check: repository root contains AGENTS.md; .agents/skills/xhs-answer-curator passes quick_validate and is in the documented repo discovery path` -> passed
- Commit: `9c678a00`
- Changed files: `AGENTS.md`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 根规则要求所有答案改动使用 curator Skill、候选与正式答案隔离、最多 10 题、禁止手工 ready/curated、失败保持 needs_update，并强制结构/Canonical/测试验证。

##### `TASK-20260711-0313-long-tail-answer-quality-T03-S03` 实现上下文、候选、审查和晋级接口

- Status: `done`
- Goal: 让 Skill 通过确定性命令完成数据准备和状态变更，不手工拼接仓库数据。
- Steps:
  - 新增 `answer context --canonical-id <id>`，输出 Canonical、全部原题变体、实体、领域、公司、相邻 Canonical 和精选风格样本。
  - 新增 `answer candidate render --spec <json>`，只写 `review/candidates/answers/`。
  - 新增 `answer audit --candidate <path>`，输出评分、硬失败、证据和修改建议；支持 `--tier`、单个/多个 `--type`、`--set`、`--require-evidence`、`--require-code` 和 `--noWrite` 过滤。
  - 新增 `answer promote --canonical-id <id> --candidate <path> --evidence <path>`，仅在全部校验通过时原子替换正式答案并升级 metadata/version。
  - 晋级失败不改正式答案、不改 Canonical 状态。
- Expected files: `scripts/commands/answer.js`, `scripts/lib/answer_quality.js`, `scripts/content/render_answer_specs.js`, `review/candidates/answers/.gitkeep`
- Validation: `node --test test/answer_candidate.test.js test/answer_promote.test.js` -> passed (3/3); `npm test` -> passed (60/60)
- Commit: `80cfbdfc`
- Changed files: `scripts/commands/answer.js`, `scripts/lib/answer_quality.js`, `scripts/content/render_answer_specs.js`, `review/candidates/answers/.gitkeep`, `test/answer_candidate.test.js`, `test/answer_promote.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 新增完整上下文、隔离候选渲染、可过滤审查和带候选哈希/独立审查/分数门禁的原子晋级；失败测试验证正式答案与 Canonical 均逐字节不变。同步修正精选 spec 渲染器保留 `quality_tier=curated`，避免质量迁移后的生成漂移。

##### `TASK-20260711-0313-long-tail-answer-quality-T03-S04` 建立证据与专项校验器

- Status: `done`
- Goal: 自动阻断可确定发现的低质量答案。
- Steps:
  - 定义 `review/evidence/{canonical_id}.json` schema，记录来源、claim 映射、核对日期、编写/审查版本和评分。
  - 增加模板重复、通用追问、跨题实体污染和原题覆盖校验。
  - Coding/SQL 增加编译/解析、边界用例和禁止占位符校验。
  - Project/Behavior 增加第一人称虚构与未填占位检查。
- Expected files: `scripts/lib/answer_quality.js`, `scripts/content/check_answer_evidence.js`, `test/answer_evidence.test.js`, `test/answer_code_validation.test.js`
- Validation: `npm test` -> passed (66/66); `node scripts/xhs.js answer audit --fixtures --noWrite` -> passed (5/5 expected outcomes)
- Commit: `322581ab`
- Changed files: `config/answer_evidence.schema.json`, `scripts/commands/answer.js`, `scripts/lib/answer_quality.js`, `scripts/content/check_answer_evidence.js`, `test/answer_candidate.test.js`, `test/answer_promote.test.js`, `test/answer_evidence.test.js`, `test/answer_code_validation.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 证据 schema 要求来源、claim 映射、核对日期、编写/审查版本、原题覆盖和两轮内独立审查；专项门禁覆盖旧模板/通用追问/跨题核心、Java `javac` 编译、SQL 结构与占位符、至少三个边界用例，以及 Project/Behavior 的虚构经历和未填占位。

##### `TASK-20260711-0313-long-tail-answer-quality-T03-S05` 接入 CI

- Status: `done`
- Goal: 任何 PR 都不能降低精选覆盖率或引入新的语义硬失败。
- Steps:
  - 新增 `ci:answer:semantic`、`ci:answer:evidence` 和 `ci:answer:code`。
  - CI 对变更答案做全量专项校验，对全库做覆盖率和状态回归校验。
  - curated-ready 数只能增加或在显式修复迁移中保持不变，不能静默下降。
- Expected files: `package.json`, `.github/workflows/ci.yml`, `scripts/content/check_answer_coverage.js`
- Validation: `npm run ci:check && npm run ci:answer:semantic && npm run ci:answer:evidence && npm run ci:answer:code` -> passed; `npm test` -> passed (74/74)
- Commit: `b4bae26c`
- Changed files: `package.json`, `.github/workflows/ci.yml`, `scripts/content/check_answer_evidence.js`, `scripts/content/check_answer_code.js`, `scripts/content/check_curated_ready_regression.js`, `data/manifests/quality/curated_ready_floor.json`, `scripts/lib/answer_quality.js`
- Notes: 新增长尾语义回归、精选 ready 证据校验、curated Coding 专项检查和 curated-ready 单调回归 floor；CI 对无 active curated 的当前过渡态通过，但任何后续 ready/curated 答案都会进入证据和代码门禁。历史 spec 渲染器现在保留现有审计状态，不能静默恢复 ready/curated。

### `TASK-20260711-0313-long-tail-answer-quality-T04` S3：全量复核 Canonical 边界与答案题型

- Status: `done`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T03`
- Goal: 在重答前建立无重复、无错类、可稳定恢复的全量升级队列。
- Files likely touched: `data/questions/canonical_questions.jsonl`, `data/questions/questions.jsonl`, `data/manifests/quality/answer_rewrite_queue.jsonl`, `data/manifests/canonical/*`
- Validation: `node scripts/xhs.js canonical check --noWrite && node scripts/xhs.js answer queue check --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T04-S01` 生成全量相似题簇候选

- Status: `done`
- Goal: 对 9,043 个 singleton 和已有多题簇做全库相似度检查，找出重复、包含和边界冲突。
- Steps:
  - 组合标准化标题、实体、领域、原题向量/语义判断生成候选对。
  - 优先检查与 100 个精选 Canonical 重合的长尾题，复用而不是复制答案。
  - 每个候选保留算法分数、理由和人工决策字段。
- Expected files: `data/manifests/canonical/long_tail_duplicate_candidates.jsonl`, `scripts/content/audit_canonical_boundaries.js`
- Validation: `node scripts/content/audit_canonical_boundaries.js --check` -> passed (307 deterministic candidates)
- Commit: `pending`
- Changed files: `scripts/content/audit_canonical_boundaries.js`, `data/manifests/canonical/long_tail_duplicate_candidates.jsonl`, `test/canonical_boundary_audit.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 候选由规范化标题、中文/英文 token、实体和领域组合生成；每条保留分数、证据、建议动作和人工决策字段。该结果仅进入 merge/boundary review，绝不自动合并。

##### `TASK-20260711-0313-long-tail-answer-quality-T04-S02` 审核并执行 merge/split

- Status: `done`
- Goal: 所有高置信重复和题簇边界冲突均有明确决策，Question、Answer、ReviewProgress 可追溯迁移。
- Steps:
  - 按 10 组候选一批进行人工/Agent 语义审查。
  - 同义题 merge；独立大追问保留独立 Canonical；混合题按可回答边界 split。
  - 删除重复答案前先验证 Question 和复习进度迁移。
  - 新增只读 `review integrity`，检查 ReviewProgress 引用、重复进度和失效 canonical_id。
- Expected files: `data/questions/canonical_questions.jsonl`, `data/questions/questions.jsonl`, `review/progress.jsonl`, `data/manifests/runs/latest_canonical_merge.json`
- Validation: `node scripts/xhs.js canonical check --noWrite && node scripts/xhs.js review integrity --noWrite`
- Commit: `3c64f8ac`, `70f81127`, `85e4134d`
- Notes: Batch 0001–0023 已审查全部 234 组：220 组同义题簇已合并，14 组因算法状态、语言契约或专项深度不同而明确保留独立。后续试点边界复核又归并了 HTTP/HTTPS 一组和进程/线程两组同义题，均迁移 Question、归档源答案并重建队列；当前保留 9,036 个 Canonical，所有 Canonical、ReviewProgress 与答案结构校验通过。

##### `TASK-20260711-0313-long-tail-answer-quality-T04-S03` 全量重新判定 answer_type

- Status: `done`
- Goal: 不再直接信任来源 `question_type`，为每个最终 Canonical 选择唯一正确答案类型。
- Steps:
  - 依据面试官实际期待的回答产物判定 Concept、Mechanism、Scenario、Coding、Project、Behavior。
  - 对混合题选择主类型并在 Canonical 中记录次要覆盖要求；不可兼容的混合题执行 split。
  - 对技术题误标 Behavior、算法题误标 Concept 等硬错误全部清零。
- Expected files: `data/questions/canonical_questions.jsonl`, `data/manifests/quality/answer_type_audit.jsonl`
- Validation: `node scripts/xhs.js answer type-audit --check --noWrite` -> passed (9,260 Canonical)
- Commit: `pending`
- Changed files: `scripts/content/audit_answer_types.js`, `scripts/commands/answer.js`, `data/manifests/quality/answer_type_audit.jsonl`, `test/answer_type_audit.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 基于面试输出预期判定主类型，并独立记录来源类型信号、次要覆盖要求和风险标记；结果为 Concept 2122、Mechanism 2354、Scenario 2369、Coding 1724、Project 383、Behavior 308，2,752 条带混合/覆盖风险供后续 split review。

##### `TASK-20260711-0313-long-tail-answer-quality-T04-S04` 生成稳定重写队列和批次 ID

- Status: `done`
- Goal: 每个非 curated Canonical 恰好出现在一个最多 10 题的批次中，支持按 ID 恢复。
- Steps:
  - 排序优先级依次为硬失败、明确占位、公司/主题价值、领域覆盖缺口、稳定 canonical_id。
  - 队列字段包含 batch_id、canonical_id、answer_type、domain、risk_flags、dependencies、status。
  - 合并后的旧 Canonical 标记 migrated，不进入重写队列。
  - 为每个最多 10 题的批次生成 `tasks/answer-batches/` 子任务文件；根 ID 固定为 `TASK-20260711-0313-answer-batch-NNNN`，每份文件包含题簇复核、研究编写、独立审查、晋级和批次验证子任务。
  - 队列记录 `task_file`，后续使用 `task-md-workflow:execute-task-md` 按批次任务 ID 执行和恢复；每个批次独立提交，阶段任务只在全部对应批次任务 done 后完成。
- Expected files: `data/manifests/quality/answer_rewrite_queue.jsonl`, `data/manifests/quality/answer_rewrite_batches.json`, `tasks/answer-batches/*.md`
- Validation: `node scripts/xhs.js answer queue check --noWrite` -> passed (9,036 rows, 904 batches, each ≤10); all retained boundary candidates have explicit keep_separate decisions
- Commit: `pending`
- Changed files: `scripts/content/build_answer_rewrite_queue.js`, `scripts/commands/answer.js`, `data/manifests/quality/answer_rewrite_queue.jsonl`, `data/manifests/quality/answer_rewrite_batches.json`, `tasks/answer-batches/TASK-20260711-0313-answer-batch-*.md`, `test/answer_rewrite_queue.test.js`, `tasks/TASK-20260711-0313-long-tail-answer-quality.md`
- Notes: 已在边界清单清零（0 pending）后重建最终稳定队列；HTTP 与进程/线程同义题后续归并后再次重建：全部 9,036 个非 curated Canonical 被稳定排序并分配唯一可恢复任务，共 904 批，每批最多 10 题。首 60 题试点 Canonical ID 保持冻结，不以队列重新排序覆盖。队列只冻结执行顺序，不等价于答案晋级。

### `TASK-20260711-0313-long-tail-answer-quality-T05` S4：完成六类型 60 题试点

- Status: `in_progress`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T04`
- Goal: 在规模化之前证明 Skill、评分器和晋级流程能对六类题分别产出不弱于精选答案的结果。
- Files likely touched: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/pilot_answer_audit.json`
- Validation: `node scripts/xhs.js answer audit --set data/manifests/quality/answer_pilot_set.json --require-evidence --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T05-S01` 选择分层试点样本

- Status: `done`
- Goal: 每类 10 题同时覆盖高频实体、冷门题、版本敏感题、已知模板缺陷和题干不完整风险。
- Steps:
  - 从稳定队列确定 60 个 canonical_id 并冻结样本清单。
  - 每类至少包含 3 个已知硬失败样本和 2 个与精选主题相近的对照样本。
- Expected files: `data/manifests/quality/answer_pilot_set.json`
- Validation: `node scripts/content/select_answer_pilot.js --check && node scripts/xhs.js answer queue check --set data/manifests/quality/answer_pilot_set.json --noWrite` -> passed (60 items, 10 per type)
- Commit: `a8e54c0f`
- Notes: 新增确定性 selector；每类选择 10 题，均至少包含 3 条历史精选审计失败样本，Coding 同时优先占位实现风险，Project/Behavior 同时优先真实材料/混合题风险。样本清单将作为首 60 题的 100% 人工审查范围。

##### `TASK-20260711-0313-long-tail-answer-quality-T05-S02` 执行 60 题完整闭环

- Status: `in_progress`
- Goal: 60 题全部经研究、候选、独立审查、专项验证和晋级。
- Steps:
  - 使用 `$xhs-answer-curator` 按 10 题批次执行。
  - 每题最多两轮修订；失败则保持 needs_update 并记录原因，不能降低标准晋级。
  - 对 60 题进行 100% 人工审查和盲对比。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/pilot_answer_audit.json`
- Validation: `node scripts/xhs.js answer audit --set data/manifests/quality/answer_pilot_set.json --require-evidence --noWrite`
- Commit: `5f91877c`, `d9f29df2`, `4f945bc6`, `d68f69b9`, `9c92c429`, `0203e816`, `d172ca10`, `99fc664e`, `a5a927d4`, `971c1a4c`, `886360ee`, `d7b3efbb`, `60102414`, `28ea0ec6`, `4d65fbbd`, `b26bc5f7`, `da6fb8e1`, `62f8c402`, `d32761c1`, `9dcadfa2`, `31704726`, `6e073179`, `b5a6b4eb`, `6269a46b`, `14353944`, `02486c33`, `29f041bc`, `b1566e14`, `0f7ccafc`, `a203083d`, `6d9b3e30`, `0404b3f7`, `01ecb044`, `e9d667fa`, `4fde4ab6`, `6194af76`, `0a902ecb`, `7322a477`, `3b5b90bb`, `7bd76f82`, `ff9a5050`, `f9977626`, `8332876a`, `2859b32b`, `220c0e07`, `6198bb4d`, `5e1a181a`
- Notes: `cq_arraylist_9d3444a1`、`cq_binlog_86a375fd`、`cq_cache_consistency_a83eeb36`、`cq_clustered_index_8c8cbedb`、`cq_daemon_thread_a38b0a9b`、`cq_stringbuffer_8b8caf0d`、`cq_http_c439559c`、`cq_thread_states_2db7d11`、`cq_topic_c569b06e`、`cq_spring_injection_5060c47f`、`cq_bean_319a398d` 与 `cq_lbs_00924ec8` 已完成候选、可追溯取证、独立审查和机器审计，均无硬失败。Spring 注入候选依据 Spring Framework 7.0.8 官方文档明确区分 `@Resource` 显式 `name` 与无 `name` 的默认名称/限定回退路径，第二轮隔离审查得分 95；Bean 生命周期候选用同一版本官方文档核验扩展点、组合回调顺序与 prototype 销毁边界，第一轮隔离审查得分 96。LBS 场景候选明确容量假设、索引可回放、版本幂等、隐私过滤、热点/跨格、故障降级、压测与灰度闭环，并以 Redis 官方 GEO 文档限定 `GEOSEARCH` 的 Redis ≥ 6.2.0 边界，第二轮隔离审查得分 97。因首 60 题尚未人工签核，均不得晋级。`cq_hashmap_4d9f15d2` 两轮独立审查后仍将树桶最坏复杂度外推到不满足源码可区分/可排序 key 限定的碰撞情形，以 `unsupported_factual_claim` 保持 `needs_update`，不再修订。`cq_redis_ff848e90` 完成一轮独立审查并按证据/版本边界修订，但第二轮隔离审查服务连续无响应；按 fail-closed 规则保持 `needs_update`，不等待、不晋级。`cq_topic_f575096b` 先归并两组同义进程/线程题；两轮审查后仍有未经逐项取证的选型/机制断言，以 `unsupported_factual_claim`、`missing_evidence` 保持 `needs_update`，不再修订。`cq_gc_algorithms_3f884748` 因 JDK 版本证据不足保持 `needs_update`；`cq_incident_diagnosis_4e5a6405` 因缺少可验证的真实个人事故事实，以 `template_only_answer`、`uncovered_source_variant` 保持 `needs_update`。台账当前为 12/60 `awaiting_human_review`、5/60 保持 `needs_update`、43/60 待处理；任何未签核候选不得替换正式答案。

补充记录（2026-07-11）：`cq_redis_ff848e90` 的第二轮隔离审查随后返回，仍缺少 Lua、pipeline 队列和性能处方的一手证据映射，以 `unsupported_factual_claim` 保持 `needs_update`，不再修订。`cq_kafka_isr_3e780e46` 第二轮隔离审查发现完整复制链路、状态模型及“恢复等待”未被现有一手证据逐项覆盖；以 `unsupported_factual_claim`、`missing_evidence` 保持 `needs_update`，不启动第三轮修订。

台账校正（2026-07-11）：重新生成试点台账后为 12/60 `awaiting_human_review`、7/60 `needs_update`、41/60 待处理（SPI 候选正处于第二轮隔离审查）。`cq_kafka_isr_3e780e46` 的 pilot 队列题型为 mechanism，但 `answer context` 基于原题返回 concept；按 Skill 的“以面试期待回应决定题型”原则，此冲突已记录，当前失败候选不再改写或晋级。

SPI 进展（2026-07-11）：`cq_spi_3342eb14` 按 Java SE 21 `ServiceLoader` 一手文档完成两轮隔离审查；第二轮得分 98、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 13/60 `awaiting_human_review`、6/60 `needs_update`、41/60 待处理。

零拷贝进展（2026-07-11）：`cq_zero_copy_e7b6486b` 依据 Linux `sendfile(2)` 与 Java SE 21 `FileChannel.transferTo` 完成两轮隔离审查；第二轮得分 100、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 14/60 `awaiting_human_review`、8/60 `needs_update`、38/60 待处理（RAG 和 Redis 持久化候选正在隔离审查/取证）。

RAG 进展（2026-07-11）：`cq_rag_2ff8f969` 依据 Lewis 等人的 RAG 原始论文完成两轮隔离审查；第二轮得分 100、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 15/60 `awaiting_human_review`、7/60 `needs_update`、38/60 待处理。该题 pilot 队列标 mechanism，而 `answer context` 取原题分类显示 scenario；按题干要求的原理解释与试点队列，候选采用 mechanism，冲突已记录。

Redis 持久化进展（2026-07-11）：`cq_topic_2494ec69` 依据 Redis 官方 persistence 文档在首轮隔离审查即获 100 分、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 16/60 `awaiting_human_review`、6/60 `needs_update`、38/60 待处理。该题试点队列标 mechanism，但原题及 `answer context` 均指向 RDB/AOF 的 concept 对比，候选采用 concept，冲突已记录。

TCP/UDP 进展（2026-07-11）：`cq_tcp_e9932fa7` 依据 RFC 9293 与 RFC 768 完成两轮隔离审查；第二轮得分 100、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 17/60 `awaiting_human_review`、7/60 `needs_update`、36/60 待处理（InnoDB/MyISAM 候选正在隔离审查）。

InnoDB/MyISAM 进展（2026-07-11）：`cq_innodb_myisam_754c10e6` 依据 MySQL 8.4 官方引擎与索引文档在首轮隔离审查获 98 分、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 18/60 `awaiting_human_review`、7/60 `needs_update`、35/60 待处理（线程池拒绝策略候选已起草并待取证/独立审查）。

线程池拒绝策略记录（2026-07-11）：`cq_topic_36aeccc5` 两轮隔离审查后仍将特定构造器的默认 handler 误概括为“默认构造器”，并给出未被 Java SE 21 API 取证的递归提交适用性结论；以 `unsupported_factual_claim` 保持 `needs_update`，不进行第三轮修订。台账维持 18/60 `awaiting_human_review`、7/60 `needs_update`、35/60 待处理。

MySQL 索引类型记录（2026-07-11）：`cq_mysql_index_types_8ee09a1a` 两轮隔离审查后，现有 MySQL 8.4 侧车仍未逐项映射 FULLTEXT/SPATIAL 用途、PRIMARY/UNIQUE 写入约束语义、列组合选型条件及覆盖索引避免回表；以 `unsupported_factual_claim` 保持 `needs_update`，不进行第三轮修订。候选机器审计为 85 分且事实维度低于门槛，正式答案未修改。台账为 18/60 `awaiting_human_review`、8/60 `needs_update`、34/60 待处理。

MySQL 隔离级别进展（2026-07-11）：`cq_mysql_isolation_c43c6784` 依据 MySQL 8.4 InnoDB 隔离级别与一致性读文档完成两轮隔离审查；第二轮得分 97、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 19/60 `awaiting_human_review`、8/60 `needs_update`、33/60 待处理。试点队列遗留标注为 coding，但原题实际要求解释隔离级别和解决的问题，`answer context` 判定 concept，候选采用 concept，冲突已记录。

MySQL 备份与 PITR 记录（2026-07-11）：`cq_mysql_backup_0daa23c7` 两轮隔离审查后已纠正“以备份完成时刻作为 binlog 起点”的错误，并以 MySQL 8.4 position 恢复文档限定一致性坐标、连续日志链和误操作前 stop position；但一致性坐标与备份基线的建立、并发写入/DDL/非事务对象边界没有一手证据，机制题专项仅 15 分（最低 16）。候选保持 `needs_update`，不进行第三轮修订；正式答案未修改。台账为 19/60 `awaiting_human_review`、9/60 `needs_update`、32/60 待处理。试点队列遗留标注为 coding，但原题要求恢复流程解释，`answer context` 判定 mechanism，候选采用 mechanism，冲突已记录。

Undo Log 进展（2026-07-11）：`cq_undo_log_ed9636b1` 依据 MySQL 8.4 InnoDB Undo 与恢复文档完成两轮隔离审查；第二轮得分 99、无硬失败，候选审计通过。首轮发现的 XA 条件已修正为“未提交或处于 XA PREPARE 状态”，并明确已提交事务不属于恢复回滚对象。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 20/60 `awaiting_human_review`、9/60 `needs_update`、31/60 待处理。试点队列遗留标注为 coding，但原题实际要求恢复机制解释，`answer context` 判定 mechanism，候选采用 mechanism，冲突已记录。

CAS 记录（2026-07-11）：`cq_cas_64fa0b00` 两轮隔离审查后，CAS 条件更新、ABA 的 reference+stamp 边界以及 Java SE 21 API 证据均通过；但第二轮指出机制题没有经证据支撑的高竞争重试资源成本与性能边界，题型专项仅 15 分（最低 16）。候选保持 `needs_update`，不进行第三轮修订，正式答案未修改。台账为 20/60 `awaiting_human_review`、10/60 `needs_update`、30/60 待处理。试点队列遗留标注为 scenario，但原题实际要求原理解释，候选采用 mechanism，冲突已记录。

协程进展（2026-07-11）：`cq_coroutine_878b831f` 依据 Kotlin 官方协程基础、`runBlocking` 与 `supervisorScope` API 完成两轮隔离审查；第二轮得分 100、无硬失败，候选审计通过。候选明确限定 Kotlin/JVM、区分普通 Job 与监督作用域的失败边界、阻塞与 suspend、并发组织与实际并行度。晋级预检仅以 `missing_human_review` 失败，正式答案未修改；当前台账为 21/60 `awaiting_human_review`、10/60 `needs_update`、29/60 待处理。试点队列遗留标注为 scenario，但原题实际为概念/对比选型题，候选采用 concept，冲突已记录。

IPC 记录（2026-07-11）：`cq_ipc_84b09f40` 两轮隔离审查后，Linux/POSIX 本机 IPC 的管道、消息队列、共享内存/信号量、信号和 AF_UNIX 核心 API 已取证；但 FIFO 事实没有一手映射，AF_UNIX 的类型级消息边界/连接契约未逐项映射，五类机制的统一比较矩阵也未达到题型完整性要求。以 `unsupported_factual_claim`、`missing_evidence` 保持 `needs_update`，不进行第三轮修订，正式答案未修改。台账为 21/60 `awaiting_human_review`、11/60 `needs_update`、28/60 待处理。

JVM 安全点记录（2026-07-11）：`cq_jvm_safepoint_f7c9b757` 两轮隔离审查后已以 OpenJDK 21u 源码区分普通 native 安全状态、state transition 与 JNI critical/GC Locker；但将“源码创建/提交 JFR safepoint 事件”外推为运行时必然可见，且没有为 JVM-operation 日志归因与完整处置链提供一手映射。以 `unsupported_factual_claim` 保持 `needs_update`，不进行第三轮修订，正式答案未修改。台账为 21/60 `awaiting_human_review`、12/60 `needs_update`、27/60 待处理。

Redis 锁等待记录（2026-07-11）：`cq_redis_lock_wait_a9bfb6eb` 两轮隔离审查后已固定 Redisson commit `e40b1773d12c5123746aaa594411affbae26b969`，并取证总 waitTime 预算、订阅耗时、最终释放发布、latch 后重新竞争和 TTL 时间等待；但正文未精确说明非 owner unlock 不改变锁状态/不发布，也未保留 TTL 非正值时按剩余预算等待的源码分支。第二轮决策仍为 revise，候选保持 `needs_update`，不进行第三轮修订；正式答案未修改。台账为 21/60 `awaiting_human_review`、13/60 `needs_update`、26/60 待处理。

MySQL 索引失效进展（2026-07-11）：`cq_topic_99ffa229` 依据 MySQL 8.4 的索引使用、范围优化、生成列索引、类型转换与索引使用核验文档完成两轮隔离审查；第二轮得分 100、无硬失败，候选审计通过。首轮删去未映射的 Skip Scan、FULLTEXT/外部检索与 EXPLAIN 字段外推，改为逐项一手证据。晋级预检仅以 `missing_human_review` 失败，正式答案未修改。试点队列遗留标注为 coding、`answer context` 标为 scenario，但全部来源问法实际要求索引可用性条件解释，候选采用 concept，冲突已记录。台账生成后为 22/60 `awaiting_human_review`、13/60 `needs_update`、24/60 未起草，另 `cq_arch_layering_02c49d25` 候选已渲染并待隔离审查。

复杂系统分层进展（2026-07-11）：`cq_arch_layering_02c49d25` 依据 Microsoft 关于 Web 分层架构与架构风格的官方文档完成首轮隔离审查，得分 96、无硬失败，候选审计通过。候选明确分层是职责/依赖约束而非固定层数，区分传统上到下依赖与依赖反转，并说明映射、调用和抽象成本。晋级预检仅以 `missing_human_review` 失败，正式答案未修改。试点队列遗留标注为 scenario，但来源问法实际为分层设计原理解释，候选采用 concept，冲突已记录；当前台账为 23/60 `awaiting_human_review`、13/60 `needs_update`、24/60 未起草。

Spring 同名 Bean 进展（2026-07-11）：`cq_spring_bean_conflict_fb864867` 依据 Spring Framework 当前 BeanDefinition/覆盖文档、Framework 7.0.8 异常 API 与 Spring Boot 4.0 属性附录完成两轮隔离审查；第二轮得分 98、无硬失败，候选审计通过。首轮补齐运行中并发注册 Bean 的官方事实映射；候选明确同名 definition 注册与同类型多候选解析不同，区分 Framework 当前文档与 Boot 默认禁止覆盖的边界。晋级预检仅以 `missing_human_review` 失败，正式答案未修改。试点队列遗留标注为 behavior、`answer context` 同样误判为 behavior，但原题实际要求注册机制解释，候选采用 mechanism；当前台账为 24/60 `awaiting_human_review`、13/60 `needs_update`、23/60 未起草。

短 URL 记录（2026-07-11）：`cq_short_url_c0218e46` 以 RFC 3986 的 URI 未保留字符、Base62 容量与号段/幂等状态机可复现测试完成两轮隔离审查。第二轮总分 91，但场景题专项仅 15（最低 16）：创建/解析 SLO 未明确、号段源或映射存储不可用时缺少创建降级与超时补偿、缓存状态版本未定义权威比较或失效通知。按最多两轮规则保持 `needs_update`，不再修订，正式答案未修改；候选测试通过。试点队列遗留标注为 behavior、`answer context` 同样误判为 behavior，但原题实际为 scenario，候选采用 scenario；当前台账为 24/60 `awaiting_human_review`、14/60 `needs_update`、22/60 未起草。

哈希表碰撞记录（2026-07-11）：`cq_hash_table_286e0112` 以分离链接、开放寻址 tombstone、重散列和碰撞比较模型测试完成两轮隔离审查。第二轮总分 89，事实与证据仅 18（最低 23）：开放寻址探测方法、装载因子/性能外推、链接法选型细节以及抽象哈希表的并发适用边界没有可接受的一手或可复现逐项证据。按最多两轮规则保持 `needs_update`，不再修订，正式答案未修改；候选测试通过。试点队列遗留标注为 behavior、`answer context` 同样误判为 behavior，但原题实际为 mechanism，候选采用 mechanism；当前台账为 24/60 `awaiting_human_review`、15/60 `needs_update`、21/60 未起草。

消息 exactly-once 记录（2026-07-11）：`cq_message_exactly_once_4aede2ce` 以 Kafka 4.3 producer 幂等/事务、`read_committed` 与 destination cooperation 文档，以及 processed-event/outbox/retry 状态机测试完成两轮隔离审查。第二轮总分 93，但场景题专项 15（最低 16）、口述 3（最低 4）：缺少端到端 SLO/业务规模或待澄清验收目标，且 3 分钟版超过可口述密度。按最多两轮规则保持 `needs_update`，不再修订，正式答案未修改；候选测试通过。`answer context` 正确给出 scenario，候选采用 scenario；当前台账为 24/60 `awaiting_human_review`、16/60 `needs_update`、20/60 未起草。

RocketMQ 顺序消费进展（2026-07-11）：`cq_rocketmq_b7347b07` 依据 RocketMQ 5.0 顺序消息、消费者类型与消费者负载均衡官方文档完成两轮隔离审查；第二轮得分 100、无硬失败，候选审计通过。首轮补齐了可执行的超时/暂停/重试/DLQ/补偿恢复路径、`order_event` 幂等状态模型、容量与 SLO 假设，并压缩 3 分钟版。晋级预检仅以 `missing_human_review` 失败，正式答案 SHA-256 仍为 `2b3e1fe2e57efb471143565ba4b4f2b0cfc2eba32fa3bb9f7548fc1f580fcfe1`，未修改；当前台账为 25/60 `awaiting_human_review`、16/60 `needs_update`、19/60 未起草。

搜索引擎设计记录（2026-07-11）：`cq_topic_0c5b15b3` 依据 Lucene 10.3 postings/term dictionary 与 Elasticsearch 当前 analyzer、text field、alias、乐观并发控制、snapshot 官方文档完成两轮隔离审查。第二轮总分 91，但口述维度仅 3（最低 4）：1 分钟版四点仍承载过多设计信息，且 3 分钟版重复较多。按最多两轮规则保持 `needs_update`，不再修订；正式答案 SHA-256 仍为 `6aca1238f2c5ef6f67f2aacb4c30361b9a322c60670a35a961a4890ce97a1d32`，未修改。当前台账为 25/60 `awaiting_human_review`、17/60 `needs_update`、18/60 未起草。

待补充真实素材记录（2026-07-11）：只读盘点剩余未起草试点后，`cq_ai_055f19f9`（本人 AI 实践/思考）、`cq_q_031790903ddb176821f248e58083b1a8`（短链项目 Redis 锁的实际 key/value/业务语义）、`cq_q_18848d921d4665b4a96a8e455d2c83ed`（离职与成长）、`cq_q_1c6a767f1cb3bd48baae269f3d5dcd12`（实际冲突）、`cq_q_29c89bfc2929e423edec84f13ebab049`（个人职业规划/业务见解）、`cq_q_5530db7c04d9a3ae56de6acc6d23b39b`（本人 RabbitMQ 选型与可靠性实践）、`cq_q_5b4e008e58ab3a24f638a6160292f6de`（本人选型经历）、`cq_design_patterns_0b3fb4b2`、`cq_q_00ff669021e14b95562bb9db64da3207`、`cq_q_082198e292b873e11771a9984a2fd7ad`（实际设计模式落地）、`cq_q_0633d30c8c0b5548ac47dcbc35939e00`（项目发钱逻辑）、`cq_q_063fb18784fc2d9677aba13b1b3f3791`（秒杀项目 QPS）、`cq_q_0e26bffea609c7de57b1404293587fba`（上一家公司蓝绿发布）、`cq_q_1ac5d677a6ec11ee658edf8038e80836`（真实文件上传流程）、`cq_q_4bf1435a7d1a0d3fc7f64f471cfcd1d2`（项目 Feign/Dubbo 选型）、`cq_topic_fcc849e5`（实际微服务拆分）均没有候选人的背景、职责、原始证据和结果。为避免已验证会失败的模板化个人回答，不生成候选、不计入修订轮次；等待真实素材。因此 T05-S02 不能仅靠生成继续推进到 60 题闭环。

Maven 类路径冲突记录（2026-07-11）：`cq_q_74d36d6bdeee0a5c1894daee54b67ce8` 按实际题意从历史 behavior/project 标记改为 scenario，使用 Maven dependency mechanism、dependency:tree 插件与 Java SE 21 ClassLoader/Class/ProtectionDomain/CodeSource API 完成两轮隔离审查。第二轮仍将渲染器自动附加的通用“分区/缓存/异步扩展”文本判为 `cross_topic_contamination`，并指出 JPMS、shading、应用服务器共享库的加载行为未有逐项一手映射；总分 85，按最多两轮规则保持 `needs_update`。正式答案 SHA-256 仍为 `30c0802598f4fe70966795555b1ef68acb942bae5814285671ad8df4bd11d4c7`，未修改；当前台账为 25/60 `awaiting_human_review`、18/60 `needs_update`、17/60 未起草。

候选渲染器修复（2026-07-11）：`renderCandidate` 现显式关闭 `render_answer_specs` 的通用题型 guidance，仅保留候选规格提供的题目专属 `deep`/`mechanism`/易错点；正式 curated spec 保持原有 guidance 和无漂移输出。新增回归测试覆盖 scenario 候选不含“先澄清规模…”和“入口按容量预算…”通用段落。`node --test test/answer_candidate.test.js test/content_specs.test.js`、严格答案校验、Canonical 检查和 `npm test`（92/92）均通过。该修复不回写已达到两轮上限的 Maven 候选。

ZooKeeper 锁 Canonical 边界记录（2026-07-11）：`cq_zookeeper_lock_2808e178` 的 `answer context` 显示相邻 `cq_q_17a452529374881c0a57e963f08a18e2` 标题为“Zookeeper分布式锁实现原理？”，与当前题为同一语义边界。按去重规则撤回未审候选和证据，不增加试点计数、不修改正式答案；该对 Canonical 待合并/迁移审查后再进入重写队列。

ZooKeeper 锁合并与进展（2026-07-11）：将 `cq_q_17a452529374881c0a57e963f08a18e2` 合并到试点 Canonical `cq_zookeeper_lock_2808e178`，迁移 1 个 Question、归档重复正式答案、保留目标复习进度并重建 type-audit/稳定队列（9,035 Canonical、904 批），Canonical 与队列校验通过。合并后的候选按 mechanism 编写，依据 ZooKeeper 官方 lock recipe、3.9.5 `CreateMode` 与客户端 API 完成两轮隔离审查；第二轮 98 分、无硬失败，候选审计通过。晋级预检仅以 `missing_human_review` 失败，正式答案 SHA-256 仍为 `2fc9071534194143525cc67200356e64a4944868a033aeac87d70d12257d3d79`，未修改；当前台账为 26/60 `awaiting_human_review`、18/60 `needs_update`、16/60 未起草。试点清单遗留类型为 scenario，但合并后来源问法与 `answer context` 均为 mechanism，候选采用 mechanism。

##### `TASK-20260711-0313-long-tail-answer-quality-T05-S03` 校准并冻结 v1 流水线

- Status: `pending`
- Goal: 试点零硬失败，候选与精选盲比不劣于精选，才能进入全量阶段。
- Steps:
  - 汇总每一评分维度、返工次数、人工缺陷和误判原因。
  - 任一类型出现硬失败则修订 Skill/规则并重跑该类型全部 10 题。
  - 冻结 `xhs-answer-curator.v1`、`answer_quality.v1` 和 evidence schema v1。
- Expected files: `.agents/skills/xhs-answer-curator/SKILL.md`, `config/answer_quality.json`, `data/manifests/quality/pilot_answer_audit.json`
- Validation: `npm test && node scripts/xhs.js answer audit --set data/manifests/quality/answer_pilot_set.json --require-evidence --noWrite`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T06` S5：全量升级 Coding 与 SQL

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T05`
- Goal: 清零 Coding/SQL 占位与复用错误，每道题都有针对本题的可运行实现和测试证据。
- Files likely touched: `review/answers/*.md`, `review/evidence/*.json`, `test/generated_answers/*`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer audit --type coding --require-code --require-evidence --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T06-S01` 优先清理已知 480 份占位实现

- Status: `pending`
- Goal: `ProblemSpec`、通用 SQL 和未实现 DP 骨架在正式 ready 答案中全部为 0。
- Steps:
  - 先处理 417 + 36 + 27 个已知风险记录，合并重复 Canonical 后按实际数量执行。
  - 为每题补输入输出、约束、不变量、实现、复杂度、边界和变体。
  - 每批 10 题独立晋级并更新队列。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/content/analyze_answer_semantics.js --check --forbid-code-placeholders`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T06-S02` 完成剩余 Coding/SQL 队列

- Status: `pending`
- Goal: 最终所有 Coding/SQL Canonical 达到精选质量。
- Steps:
  - 逐批处理剩余 Coding/SQL，禁止仅因算法名称相似复用代码。
  - Java 代码编译并执行边界测试；SQL 使用固定 schema fixture 做解析/结果断言。
  - 变体必须说明状态或实现如何改变，而不是只列题名。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `test/generated_answers/*`
- Validation: `npm run ci:answer:code && node scripts/xhs.js answer queue status --type coding --expect-empty --noWrite`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T07` S6：全量升级 Concept

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T05`
- Goal: 所有 Concept 直接定义/比较题目对象，使用统一维度给出选择条件、反例、版本边界和专属追问。
- Files likely touched: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer audit --type concept --require-evidence --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T07-S01` 处理兜底结论与高重复 Concept

- Status: `pending`
- Goal: Concept 中不再出现“复习本题时应先……”式方法论代替答案，也不再跨主题拼接知识包。
- Steps:
  - 先处理 `fallback_core`、高重复结论和相邻实体污染标记。
  - 每题核心结论必须在不引用题目标题的情况下仍能独立回答问题。
  - 比较题必须按同一维度比较，单概念题必须包含反例或混淆点。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`
- Validation: `node scripts/content/analyze_answer_semantics.js --check --type concept`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T07-S02` 清空剩余 Concept 队列

- Status: `pending`
- Goal: 所有最终 Concept Canonical 均为 curated-ready。
- Steps:
  - 按领域和实体相邻批次处理，但每份答案保持题目独立性。
  - 每批随机人工抽查至少 20%，任一硬失败回退整批。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer queue status --type concept --expect-empty --noWrite && node scripts/xhs.js answer audit --type concept --noWrite`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T08` S7：全量升级 Mechanism

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T05`
- Goal: 所有 Mechanism 都能沿参与对象、核心结构、入口、状态变化、保证机制、开销、故障和版本边界完整复述。
- Files likely touched: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer audit --type mechanism --require-evidence --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T08-S01` 处理版本敏感和源码类 Mechanism

- Status: `pending`
- Goal: JDK、JVM、Spring、MySQL、Redis、MQ、协议等版本敏感结论均有第一手依据与适用边界。
- Steps:
  - 先处理带版本号、源码、默认参数、阈值和废弃机制的题。
  - evidence 将关键 claim 映射到官方文档/源码/标准及核对日期。
  - 不确定或无法取得第一手证据的答案保持 needs_update。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`
- Validation: `node scripts/xhs.js answer audit --type mechanism --require-evidence --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T08-S02` 清空剩余 Mechanism 队列

- Status: `pending`
- Goal: 所有最终 Mechanism Canonical 均为 curated-ready，原理章节不再使用全库通用因果模板。
- Steps:
  - 按 10 题批次完成研究、独立审查和晋级。
  - 追问覆盖底层、性能/资源和版本/故障边界。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer queue status --type mechanism --expect-empty --noWrite && node scripts/xhs.js answer audit --type mechanism --noWrite`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T09` S8：全量升级 Scenario

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T05`
- Goal: 所有 Scenario 从“设计清单”升级为结合题目约束的数据流、容量、一致性、故障和取舍方案。
- Files likely touched: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer audit --type scenario --require-evidence --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T09-S01` 处理 580 份纯通用场景答案和类型错误

- Status: `pending`
- Goal: 场景题核心结论必须包含本题方案判断，CSS、测试、工具使用等非系统设计题不得套 QPS/分片模板。
- Steps:
  - 先处理无 `核心技术判断` 的通用场景记录和 answer_type 审计异常。
  - 对信息不足的题明确提出最小假设，但仍需在假设下给出可执行主链路。
  - 至少提供一个替代方案和拒绝它的具体代价。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`
- Validation: `node scripts/content/analyze_answer_semantics.js --check --type scenario`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T09-S02` 清空剩余 Scenario 队列

- Status: `pending`
- Goal: 所有最终 Scenario Canonical 均为 curated-ready。
- Steps:
  - 按 10 题批次处理，容量数字注明是假设、计算结果或真实证据。
  - 追问至少覆盖故障、容量/热点和一致性/取舍三类中的两类。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer queue status --type scenario --expect-empty --noWrite && node scripts/xhs.js answer audit --type scenario --noWrite`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T10` S9：全量升级 Project 与 Behavior

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T05`
- Goal: 所有个人经历类问题提供高质量表达框架，同时绝不替用户生成虚构故事、职责或指标。
- Files likely touched: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer audit --type project,behavior --require-evidence --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T10-S01` 修复技术题误标个人题

- Status: `pending`
- Goal: GC、数据库、架构等技术问题不再因来源标签被回答成 STAR 框架。
- Steps:
  - 复核全部 Project/Behavior 的主问题期待产物。
  - 技术主问题重新分类并迁移到对应队列；混合题拆分或以技术答案为主、项目映射为辅。
- Expected files: `data/questions/canonical_questions.jsonl`, `data/manifests/quality/answer_rewrite_queue.jsonl`, `review/answers/*.md`
- Validation: `node scripts/xhs.js answer type-audit --types project,behavior --check --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T10-S02` 清空真实 Project/Behavior 队列

- Status: `pending`
- Goal: 每题有针对性的 STAR/决策框架、真实性校验问题和岗位相关追问，无确定口吻虚构事实。
- Steps:
  - 无用户真实材料时输出字段化提问和组织框架，不写完成态个人故事。
  - 公司选择等题只能引用已经核验的岗位/公司事实，否则使用待填字段。
  - 每批进行第一人称、精确指标和敏感信息专项扫描。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/answer_rewrite_queue.jsonl`
- Validation: `node scripts/xhs.js answer queue status --type project,behavior --expect-empty --noWrite && node scripts/xhs.js answer audit --type project,behavior --noWrite`
- Commit: `pending`
- Notes:

### `TASK-20260711-0313-long-tail-answer-quality-T11` S10：余量清零与全库完成证明

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T06`, `TASK-20260711-0313-long-tail-answer-quality-T07`, `TASK-20260711-0313-long-tail-answer-quality-T08`, `TASK-20260711-0313-long-tail-answer-quality-T09`, `TASK-20260711-0313-long-tail-answer-quality-T10`
- Goal: 对实际全库逐项证明所有有效问题都到达精选质量答案，不以抽样或缺陷未检出代替完成。
- Files likely touched: `data/manifests/quality/answer_semantic_report.json`, `data/manifests/quality/answer_coverage_report.json`, `docs/refactor/08_content_building_goals.md`, `review/plans/*`
- Validation: `npm run ci:check && npm run ci:answer:semantic && npm run ci:answer:evidence && npm run ci:answer:code`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T11-S01` 清理所有残余状态和孤儿资产

- Status: `pending`
- Goal: 队列、答案状态、Canonical 状态和 evidence 一一对应。
- Steps:
  - `long_tail_baseline`、draft、needs_update、missing、orphan candidate、orphan answer、orphan evidence 全部清零。
  - 所有 merge/split 后的旧 ID 均有迁移记录且不再被 ReviewProgress 引用。
  - 删除旧确定性长尾生成器或将其限制为明确的 baseline 草稿工具，禁止产出 ready。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `scripts/content/generate_long_tail_answers.js`, `data/manifests/quality/*`
- Validation: `node scripts/xhs.js answer closure check --noWrite && node scripts/xhs.js review integrity --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T11-S02` 执行全库逐项完成审计

- Status: `pending`
- Goal: 对每一个最终 Canonical 生成可追溯完成行，而不是只输出总数。
- Steps:
  - 输出 canonical_id、Question 数、答案路径、status、quality_tier、评分、evidence、代码/题型校验和最近审查时间。
  - 任一字段缺失或任一闸门失败即整体不完成。
  - 随机重算至少 5% 评分并与已存评分对比，检测评审漂移。
- Expected files: `data/manifests/quality/final_answer_completion_audit.jsonl`, `data/manifests/quality/answer_semantic_report.json`
- Validation: `node scripts/xhs.js answer closure audit --full --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T11-S03` 验证 Question 到答案的全量可达性

- Status: `pending`
- Goal: 任何有效 Question 都唯一到达 curated-ready Answer 和 ReviewProgress。
- Steps:
  - 全量遍历有效 Question，而非抽样。
  - 验证 Canonical 唯一、答案唯一、证据存在、进度存在、查询和复习入口可发现。
  - 验证合并前的所有旧 question_id 仍然可达。
- Expected files: `data/manifests/quality/question_answer_reachability.json`, `data/manifests/quality/answer_coverage_report.json`
- Validation: `node scripts/xhs.js answer reachability --full --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T11-S04` 更新阶段文档为语义完成

- Status: `pending`
- Goal: 只有全库证明通过后，才将全量答案阶段标记为完成。
- Steps:
  - 更新 C8/C9 状态、最终 Canonical 数、curated-ready 数和合并数量。
  - 记录质量门槛、全量审计结果和遗留项为 0 的证据路径。
- Expected files: `docs/refactor/08_content_building_goals.md`, `review/plans/c8_full_answer_coverage.md`
- Validation: `manual check: every completion claim links to a current manifest or command result`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T11-S05` 补齐全库完成证明命令

- Status: `done`
- Goal: 为 S5–S11 的队列清零、正式答案闭环、Question 可达性和四周稳定性提供 fail-closed、可复现的命令，而不是依赖人工汇总。
- Steps:
  - 实现 `answer queue status`、`answer closure check|audit`、`answer reachability` 和 `answer stability`。
  - 逐行检查正式答案、evidence、独立审查、Canonical、Question 和 ReviewProgress 的关联。
  - 修复正式答案复审对“候选哈希”与“晋级后元数据哈希”混淆的问题，并加入回归测试。
- Expected files: `scripts/commands/answer.js`, `scripts/lib/answer_completion.js`, `scripts/lib/answer_quality.js`, `test/answer_completion.test.js`, `test/answer_promote.test.js`
- Validation: `node --test test/answer_completion.test.js test/answer_promote.test.js && npm test && node scripts/xhs.js answer validate --strict --noWrite && node scripts/xhs.js canonical check --noWrite` -> passed (94 tests; 9,035 formal answers and 9,609 Question bindings remain structurally valid)
- Commit: `abc968ff`
- Notes: 实现 queue status、closure check/audit、reachability 和 stability/sample 的 fail-closed 验证；正式 curated 复审改为校验晋级时保存的 `candidate_sha256`，不再误用元数据变更后的正式文件哈希。真实库只读结果正确保持未完成：Coding 余量 1,673，四周计划与快照尚未建立；该子任务不改变任何答案的晋级状态。

### `TASK-20260711-0313-long-tail-answer-quality-T12` S11：连续四周复习稳定性验证

- Status: `pending`
- Depends on: `TASK-20260711-0313-long-tail-answer-quality-T11`
- Goal: 用真实口述和复习反馈证明答案不只是静态评分合格，而且长期保持精选质量。
- Files likely touched: `review/sessions/*`, `review/progress.jsonl`, `review/answers/*.md`, `data/manifests/quality/weekly_answer_quality.json`
- Validation: `node scripts/xhs.js answer stability --weeks 4 --noWrite`

#### Subtasks

##### `TASK-20260711-0313-long-tail-answer-quality-T12-S01` 建立每周分层复述样本

- Status: `pending`
- Goal: 每周覆盖六种题型、主要领域、新晋级答案和历史薄弱答案。
- Steps:
  - 每周至少抽取 60 题，每种类型至少 5 题，其余按领域规模和风险加权。
  - 同一答案至少覆盖 1 分钟版和一个随机追问。
  - 记录答不出、含糊、事实疑问、过长和追问断裂等缺陷类型。
- Expected files: `review/plans/weekly_answer_quality.md`, `review/sessions/*`
- Validation: `node scripts/xhs.js answer stability sample --week <YYYY-Www> --check --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T12-S02` 连续四周闭环反馈

- Status: `pending`
- Goal: 每个复习缺陷都回写答案、重新审查并再次复述，且四周无质量覆盖回退。
- Steps:
  - 硬失败立即将答案降为 needs_update，并阻断全库完成状态。
  - 普通表达缺陷进入下一批修订，修订后重新走 evidence、审查和晋级。
  - 每周输出 curated-ready 覆盖率、硬失败数、返工数和复述通过率。
- Expected files: `review/answers/*.md`, `review/evidence/*.json`, `data/manifests/quality/weekly_answer_quality.json`
- Validation: `node scripts/xhs.js answer stability --weeks 4 --require-zero-hard-fail --require-no-regression --noWrite`
- Commit: `pending`
- Notes:

##### `TASK-20260711-0313-long-tail-answer-quality-T12-S04` 记录可审计的复述反馈

- Status: `done`
- Goal: 让每次复习能记录 1 分钟复述、随机追问、缺陷类型、硬失败和反馈闭环日期，供稳定性审计逐项核验。
- Steps:
  - 扩展 `review mark` 的 session event，保存口述与追问完成情况、质量缺陷、硬失败和闭环字段。
  - 验证 `--noWrite` 不修改 progress 或 session。
- Expected files: `scripts/commands/review.js`, `test/review.test.js`
- Validation: `node --test test/review.test.js test/answer_completion.test.js && npm test` -> passed (95 tests)
- Commit: `pending`
- Notes: `review mark` 保存 `oral_version`、`followup_answered`、`quality_defects`、`hard_failures` 和 `feedback_closed_at`；只读调用返回事件预览而不写 progress/session。

##### `TASK-20260711-0313-long-tail-answer-quality-T12-S03` 完成根任务审计

- Status: `pending`
- Goal: 逐条核对 Objective、Quality Contract 和 Final Proof，确认没有未完成、弱证据或缺失证据项。
- Steps:
  - 复跑所有结构、语义、证据、代码、可达性和稳定性命令。
  - 将每项要求映射到当前文件或命令输出；抽样证据不能支持全量要求。
  - 仅当所有要求都有直接证据时，将根任务和所有阶段标记为 done。
- Expected files: `tasks/TASK-20260711-0313-long-tail-answer-quality.md`, `data/manifests/quality/*`
- Validation: `npm run ci:check && node scripts/xhs.js answer closure audit --full --noWrite && node scripts/xhs.js answer stability --weeks 4 --noWrite`
- Commit: `pending`
- Notes:

## Assumptions

- “所有长尾答案完成”按所有有效 Question 的语义覆盖定义；同义题合并后共享一份精选答案，不为满足旧文件数量保留重复答案。
- 100 份现有精选答案是起始基准，不豁免重新事实审查；若精选答案本身不达标，应先修复基准。
- 真正的事实正确性不能只靠 Skill 提示保证；必须同时具备第一手证据、独立审查、确定性校验和人工抽查。
- 全量阶段按现有 10 题批次执行；如 Canonical 合并导致总量变化，以完成审计中的最终 Canonical 数为准。
- 任何无法核验的答案允许长期保持 `needs_update`，但只要仍有一份未晋级，根任务就不能完成。
