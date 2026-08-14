# 11 Legacy Canonical Accept Consumer Inventory

> 本文解释 `canonical accept` 的消费者清单与分阶段退役状态。机器可检查事实源是同目录下 `11_legacy_canonical_accept_consumer_inventory.json`。

## 1. 当前结论

当前正式流程是：

```text
canonical suggest
  -> RelationCandidate
  -> dedup decide
  -> RelationDecision
  -> dedup apply
  -> Canonical mutation
```

Repository-local blocker 已清零，GitHub 可观察的项目特异外部消费者为 0；同时仍保留“本地脚本、未提交自动化、不可见/未索引私有调用无法证明不存在”的残余风险。

前三层 runtime removal 已完成：

```text
Interface layer
  canonical accept CLI / runAccept / Presenter / help   removed

Production Composition Root
  canonical.accept capability                           removed
  Legacy Candidate adapter construction/injection       removed

Application layer
  src/application/canonical/accept-canonical.js         removed
  canonical_accept_application characterization         removed
```

当前状态：

```text
runtime_removal_in_progress_application_removed
```

因此当前代码中已经没有 Accept Application orchestration。剩余 legacy 内容只存在于 Port / filesystem adapter / revision CAS / MutationPlan operation 等更低层兼容契约。

## 2. 外部消费者搜索证据

2026-08-14 检查过：

```text
scripts/xhs.js canonical accept
liqiangcc/xhs canonical accept
canonical_candidates.v1
LegacyCanonicalCandidateRepository
legacy-canonical-candidate-repositories
```

项目特异 GitHub 查询未发现 `liqiangcc/xhs` 之外的消费者。

`canonical_candidates.json` 在其它项目中存在同名文件，但属于无关格式/领域，不能作为本项目 consumer 证据。

因此：

```text
observable_github_external_consumer_count = 0
external_consumers_fully_observable        = false
```

## 3. Interface removal 已完成

已经删除：

```text
scripts/commands/canonical.js::runAccept
canonical.js accept dispatch
canonical.js accept help
scripts/xhs.js canonical accept help
src/interfaces/cli/canonical-accept-presenter.js
test/canonical_accept_presenter.test.js
```

CLI characterization 现在验证反向边界：

```text
node scripts/xhs.js canonical accept ...
  -> exit 1
  -> Unknown canonical command: accept
  -> no Canonical mutation
  -> no Question mutation
```

Interface 不再知道 `canonical_candidates.v1` schema。

## 4. Production Composition Root removal 已完成

`src/bootstrap/create-application.js` 已删除：

```text
createAcceptCanonicalUseCase import
createFsLegacyCanonicalCandidateRepository import
Legacy Candidate adapter construction
Accept use case construction
canonical.accept capability exposure
```

Production Root 当前 Canonical capability 只包含：

```text
merge
split
planQuestionGroup
planQuestionGroupMutation
canonicalizeQuestionGroup
```

架构测试要求：

```text
'accept' in app.canonical === false
```

## 5. Accept Application removal 已完成

已经删除：

```text
src/application/canonical/accept-canonical.js
test/canonical_accept_application.test.js
```

原 Application characterization 中关于 create / extend / conflict / race / commit failure 的测试随已删除 orchestration 一起退役，不下沉复制到 Port/Infrastructure。

`canonical_accept_filesystem_integration.test.js` 现在只验证更低层的 Legacy Candidate repository 与 Canonical ownership opaque revision 语义，不再显式组装一个替代 Accept Application。

## 6. Remaining lower-level compatibility

仍待删除：

```text
src/ports/repositories/legacy-canonical-candidate-repository.js
  -> deprecated legacy read Port

src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js
  -> legacy filesystem adapter

src/infrastructure/filesystem/canonical-paths.js
  -> legacyCandidateManifest path

src/infrastructure/filesystem/canonical-repositories.js
  -> canonical-candidate:<id> revision CAS bridge

src/application/canonical/mutation-plan.js
  -> operation=accept support
```

这些已经不构成可调用的业务 use case，只是分阶段删除尚未完成的低层兼容代码。

## 7. Test-support compatibility

`src/infrastructure/in-memory/canonical-adapters.js` 仍包含 candidate-specific state/revision support。Accept Application 删除后它已不再由该 Application characterization 使用，但本刀不顺带删除，留给后续 test-support cleanup slice。

不能删除整个 in-memory Canonical adapter，因为 Merge/Split/Canonicalize 测试仍复用其中其它能力。

## 8. Shared current code that must survive

不要把：

```text
src/domain/canonical/accept-policy.js
```

当作 legacy-only 文件。

当前 `question-group-projection-policy.js` 仍复用 `acceptCanonicalCandidate()` 作为 Canonical aggregate create/extend 的 SSOT。

同样不能删除整个：

```text
src/infrastructure/filesystem/fs-canonical-mutation-store.js
```

它仍是 Merge/Split/Canonicalize 的正式事务边界。只应逐步删除 legacy candidate revision evidence。

## 9. Checked-in legacy data

`data/manifests/canonical/canonical_candidates.json` 当前仍为空：

```text
candidate_count = 0
candidates = []
```

没有待执行 legacy candidate 阻止继续退役。

## 10. Policy / historical references

README、AGENTS、Skill、Actions/架构文档中出现 legacy 术语时，只能用于：

- 说明已退役边界；
- 禁止新流程回退；
- 记录删除计划。

历史 ADR / review plan 可以保留当时术语，不作为当前操作 SSOT。

当前操作 SSOT：

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

## 11. `candidate_id` 不是删除条件

`canonical_boundary_candidate.v1` 等其它模型也使用 `candidate_id`，与 legacy Accept 无关。

真正退役应追踪：

```text
canonical_candidates.v1
canonical_candidates.json
LegacyCanonicalCandidateRepository
canonical-candidate:<id> revision
operation=accept
```

## 12. 下一步

下一刀建议只删除：

```text
src/ports/repositories/legacy-canonical-candidate-repository.js
src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js
```

并删除/改写当前直接验证 legacy filesystem repository 的 characterization。

先不删除 `canonical-candidate:<id>` CAS bridge、`operation=accept`、in-memory candidate support、deprecated aliases 或空 manifest，继续按层向内收缩：

```text
Legacy Port / filesystem adapter
→ canonical-candidate CAS bridge
→ operation=accept
→ in-memory candidate test support
→ deprecated aliases
→ legacy-only tests
→ empty canonical_candidates.json
```

每一刀都必须独立跑完整 CI。
