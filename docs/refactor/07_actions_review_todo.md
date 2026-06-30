# 07 Actions Review TODO

> 目标：在继续扩大 AI 触发 GitHub Actions 的范围之前，先修复当前 Action 管理层和质量报告体系中的边界问题，保证后续自动化不会误写仓库、不会隐藏失败报告，也不会把空模板答案标记为 ready。

---

## 1. 当前状态

当前 `xhs` 已经完成了 GitHub Actions 管理层第一版：

```text
.github/workflows/ci.yml
.github/workflows/xhs-manage.yml
.github/workflows/xhs-weekly-report.yml
```

同时已经补齐了：

```text
npm run ci:check
node scripts/xhs.js report quality
node scripts/xhs.js answer missing
node scripts/xhs.js answer init-batch
node scripts/xhs.js review next
scripts/lib/review_scheduler.js
config/review_strategy.json
```

当前质量报告显示：

```text
questions: 9620 rows
valid questions: 9362 rows
canonical records: 18
assigned question rows: 83
P0 canonical: 12
ready answers: 12
P0 missing answers: 0
reviewed count: 0
issue links: 0
taxonomy legacy aliases: 6862
```

这说明 Action 管理层已经可用，但还需要补齐几个安全边界。

---

## 2. TODO 总览

| ID | 优先级 | 任务 | 目标 |
|---|---:|---|---|
| T1 | P0 | `report quality` 支持失败也产出报告 | weekly report 不因 `report.ok=false` 中断上传 |
| T2 | P0 | `answer validate --strict` | 防止 `ready` 答案仍是 TODO 空模板 |
| T3 | P0 | `review prepare --noWrite` 不写 plan | 统一只读任务语义 |
| T4 | P1 | 明确 `--noManifest` 语义 | 避免误解 candidate manifest 和 run manifest |
| T5 | P1 | 把 TODO 加入 docs/refactor 索引 | 后续 Codex 能按顺序执行 |
| T6 | P1 | 增加 Action 运行状态检查方式 | 能确认 CI / manage workflow 是否真实运行 |

---

## 3. T1：`report quality` 支持失败也产出报告

### 问题

`report quality` 当前会根据 `report.ok` 返回退出码：

```text
report.ok=true  -> exit 0
report.ok=false -> exit 1
```

这对 CI 守门是合理的，但对 weekly report 不合理。

如果仓库出现质量问题，`xhs-weekly-report.yml` 可能在生成报告步骤直接失败，导致后续 artifact 上传不执行。结果是：

```text
越是需要看报告时，越可能拿不到报告。
```

### 建议方案

给 `report quality` 增加参数：

```bash
node scripts/xhs.js report quality --noManifest --noFail
```

语义：

```text
--noFail 只影响退出码，不影响 report.ok 字段。
report.ok=false 时仍然输出 JSON 和 Markdown 报告。
命令最终 exit 0，方便 weekly report 上传 artifact。
```

### 需要修改的文件

```text
scripts/commands/report.js
.github/workflows/xhs-weekly-report.yml
.github/workflows/xhs-manage.yml
test/report.test.js
```

### 实施步骤

```text
1. 在 report.js parseArgs 中识别 --noFail。
2. main() 中保持 result.ok 原样。
3. 如果 options.noFail=true，则始终 return 0。
4. weekly report workflow 改为使用 --noFail。
5. xhs-manage 的 quality-report 只读任务也可以使用 --noFail。
6. 增加测试覆盖 report.ok=false + --noFail 时 exit 0。
```

### 验收标准

```text
[ ] node scripts/xhs.js report quality 在 report.ok=false 时仍 exit 1
[ ] node scripts/xhs.js report quality --noFail 在 report.ok=false 时 exit 0
[ ] report.ok=false 仍保留在 JSON 输出中
[ ] weekly report 始终能上传 quality-report artifact
[ ] npm test 通过
```

---

## 4. T2：增加 `answer validate --strict`

### 问题

当前 `answer validate` 主要校验 metadata：

```text
schema_version
canonical_id
filename_metadata_mismatch
unknown_canonical_id
status
```

但它不检查正文质量。

风险是：

```text
某个 answer 文件 status=ready，但正文仍然是 TODO 空模板，也可能通过普通 validate。
```

### 建议方案

增加严格模式：

```bash
node scripts/xhs.js answer validate --strict
```

strict 模式检查：

```text
1. status=ready 的答案不能包含独立 TODO 占位。
2. status=ready 的答案必须包含必要章节。
3. 必要章节不能是空内容。
4. canonical answer_status=ready 时，必须存在对应 ready answer 文件。
```

必要章节建议先固定为：

```text
## 核心结论
## 1 分钟版
## 3 分钟版
## 关键细节
## 原理机制
## 项目经验版
## 常见追问
## 易错点
```

### 需要修改的文件

```text
scripts/commands/answer.js
scripts/lib/answer_store.js
test/answer.test.js
package.json
.github/workflows/ci.yml
```

### 实施步骤

```text
1. answer parseArgs 支持 --strict。
2. answer_store 增加 validateAnswerContent(answer, options)。
3. runValidate 在 strict=true 时检查 ready 文件正文。
4. 增加错误类型：todo_placeholder、missing_section、empty_section、ready_status_without_ready_file。
5. package.json 增加 ci:answer:validate:strict。
6. CI 可先不强制 strict，先在 xhs-manage 中提供 task：answer-validate-strict。
```

### 验收标准

```text
[ ] ready 文件包含 TODO 时 strict validate 失败
[ ] draft 文件包含 TODO 时 strict validate 不失败
[ ] ready 文件缺少必要章节时 strict validate 失败
[ ] ready 文件章节为空时 strict validate 失败
[ ] 当前 12 个 ready 答案能通过 strict validate
[ ] npm test 通过
```

---

## 5. T3：修复 `review prepare --noWrite` 仍写 plan

### 问题

`review today` 和 `review weak` 已经支持 `--noWrite`，不会初始化 progress，也不会写 run manifest。

但 `review prepare` 当前仍然会写：

```text
review/plans/{target}.md
```

这会导致后续如果把 `review prepare` 加入 xhs-manage 的只读任务，违反“只读任务不写仓库”的规则。

### 建议方案

调整 `runPrepare(options)`：

```text
options.noWrite=true 时：
1. 不写 review/plans/*.md
2. 返回 dry_run=true
3. plan_path=null
4. rows 正常输出
```

普通模式保持不变。

### 需要修改的文件

```text
scripts/commands/review.js
test/review.test.js
test/no_write.test.js
.github/workflows/xhs-manage.yml
```

### 实施步骤

```text
1. runPrepare 中判断 options.noWrite。
2. noWrite 时跳过 writePlan。
3. result 增加 dry_run 字段。
4. noWrite 时 plan_path=null。
5. no_write.test 增加 review prepare --noWrite 不写 plan 的用例。
6. 后续 xhs-manage 可以安全开放 review-prepare dry-run。
```

### 验收标准

```text
[ ] review prepare 正常模式仍写 review/plans/{target}.md
[ ] review prepare --noWrite 不写 review/plans/{target}.md
[ ] review prepare --noWrite 返回 dry_run=true
[ ] review prepare --noWrite 不写 latest_review_prepare.json
[ ] npm test 通过
```

---

## 6. T4：明确 `--noManifest` 语义

### 问题

`canonical suggest --noManifest` 当前仍会写：

```text
data/manifests/canonical/canonical_candidates.json
```

这在业务上是合理的，因为 canonical candidates 是任务输出；但从命名看容易误解为“不写任何 manifest”。

实际语义是：

```text
--noManifest 只是不写 data/manifests/runs/latest_*.json
```

### 建议方案

短期文档修正即可。

在 README 和 `06_github_actions_ai_management.md` 中明确：

```text
--noManifest / --noWrite 控制 run manifest 和报告写入。
canonical_candidates.json 属于 canonical suggest 的业务输出，不受 --noManifest 控制。
```

中期可以考虑改名为：

```text
--noRunManifest
```

但不建议马上改名，避免破坏已有 Action。

### 需要修改的文件

```text
README.md
docs/refactor/06_github_actions_ai_management.md
docs/refactor/07_actions_review_todo.md
```

### 验收标准

```text
[ ] README 明确 --noManifest 语义
[ ] 06 文档明确 candidate manifest 是业务输出
[ ] xhs-manage 中 canonical suggest 的 artifact 行为与文档一致
```

---

## 7. T5：把 TODO 加入文档索引

### 问题

`docs/refactor/` 当前已经有 01-06 文档。新增本 TODO 后，如果不加入索引，后续 Codex 可能不会优先读取。

### 建议方案

更新：

```text
docs/README.md
docs/refactor/README.md
```

增加：

```text
refactor/07_actions_review_todo.md     Actions 管理层 review 后的修复 TODO
```

### 验收标准

```text
[ ] docs/README.md 能看到 07 文档
[ ] docs/refactor/README.md 能看到 07 文档
[ ] 07 文档被定义为当前 Action 管理层下一步执行依据
```

---

## 8. T6：增加 Action 运行状态检查方式

### 问题

当前已经新增 workflow 文件，但本地 review 时不容易确认：

```text
1. workflow 是否已经触发过
2. 最近一次是否成功
3. 哪个 commit 对应哪个 workflow run
```

### 建议方案

新增文档和命令说明：

```bash
gh run list --workflow CI --limit 5
gh run list --workflow "XHS Manage" --limit 5
gh run view <run-id> --log-failed
```

可以在 README 的 Verification 或 `06_github_actions_ai_management.md` 增加一节。

后续可增加 `xhs-manage` task：

```text
action-status
```

但第一阶段只需文档说明。

### 验收标准

```text
[ ] README 或 06 文档记录 gh run list / gh run view 用法
[ ] review 人员可以快速检查 CI 是否真实运行
```

---

## 9. 建议执行顺序

推荐按这个顺序给 Codex 执行：

```text
1. T1：report quality --noFail
2. T3：review prepare --noWrite
3. T2：answer validate --strict
4. T4：文档说明 --noManifest 语义
5. T5：更新 docs 索引
6. T6：补充 Action 运行状态检查说明
```

原因：

```text
T1 直接影响 weekly report 可见性。
T3 直接影响只读语义一致性。
T2 直接影响 ready 答案质量。
T4-T6 主要是文档和维护体验。
```

---

## 10. Codex 执行提示词

```text
请基于当前 liqiangcc/xhs 仓库继续修复 GitHub Actions 管理层 review 后的 TODO。

请按 docs/refactor/07_actions_review_todo.md 执行，优先完成：

1. T1：给 `node scripts/xhs.js report quality` 增加 `--noFail` 参数。
   - report.ok=false 时普通模式仍 exit 1。
   - report.ok=false 且 --noFail 时 exit 0。
   - xhs-weekly-report.yml 使用 --noFail，保证 artifact 能上传。
   - 增加 test/report.test.js 覆盖。

2. T3：修复 `review prepare --noWrite` 仍写 plan 的问题。
   - noWrite 时不写 review/plans/*.md。
   - 返回 dry_run=true、plan_path=null、rows 正常输出。
   - 增加 test/no_write.test.js 覆盖。

3. T2：增加 `answer validate --strict`。
   - ready 答案不能包含 TODO。
   - ready 答案必须包含必要章节。
   - 必要章节不能为空。
   - 当前 12 个 ready 答案应通过 strict validate。
   - 增加 test/answer.test.js 覆盖。

4. T4-T6：补充 README / docs 说明。
   - 说明 --noManifest 只控制 run manifest，不控制 canonical_candidates 等业务输出。
   - 把 07 文档加入 docs/README.md 和 docs/refactor/README.md。
   - 补充 gh run list / gh run view 的 Action 状态检查命令。

约束：
- 不修改 note_tagged。
- 不引入外部存储。
- 不直接同步 GitHub issue。
- 不把语义变更直接隐藏在 workflow 中。
- 提交前运行 npm test 和 npm run ci:check。
```

---

## 11. 完成后的目标状态

完成本 TODO 后，仓库应该达到：

```text
1. Weekly report 即使质量失败也能产出 artifact。
2. 所有只读 Action 都不会写仓库文件。
3. ready answer 具备最低内容质量保证。
4. --noManifest / --noWrite 语义清楚。
5. 文档索引能引导 Codex 读取最新 TODO。
6. 人可以快速检查 GitHub Actions 是否真实运行。
```

这时再继续扩大 AI 触发范围会更安全。
