# 11 Legacy Canonical Accept Consumer Inventory

> 本文解释 `canonical accept` 的消费者清单与分阶段退役状态。机器可检查事实源是同目录下 `11_legacy_canonical_accept_consumer_inventory.json`。

## 1. 当前结论

当前正式流程只有：

```text
canonical suggest
  -> RelationCandidate
  -> dedup decide
  -> RelationDecision
  -> dedup apply
  -> Canonical mutation
```

Repository-local blocker 已清零，GitHub 可观察的项目特异外部消费者为 0；仍保留“本地脚本、未提交自动化、不可见/未索引私有调用无法证明不存在”的残余风险。

已经完成五层 runtime removal：

```text
Interface layer                         removed
Production Composition Root             removed
Accept Application                      removed
Legacy Candidate Repository layer       removed
canonical-candidate:* Filesystem CAS     removed
```

当前状态：

```text
runtime_removal_in_progress_cas_bridge_removed
```

因此当前 `src/` JavaScript 中已经没有读取 `canonical_candidates.v1` 的执行路径，也没有 `canonical-candidate:*` Filesystem revision route。

## 2. 外部消费者搜索证据

2026-08-14 检查过项目特异标识：

```text
scripts/xhs.js canonical accept
liqiangcc/xhs canonical accept
canonical_candidates.v1
LegacyCanonicalCandidateRepository
legacy-canonical-candidate-repositories
```

未发现 `liqiangcc/xhs` 之外的可观察消费者。

`canonical_candidates.json` 在其它项目中有同名文件，但属于无关格式/领域，不能作为本项目 consumer 证据。

```text
observable_github_external_consumer_count = 0
external_consumers_fully_observable        = false
```

## 3. 已删除的执行层

### Interface

```text
canonical accept CLI / runAccept / Presenter / help
```

旧命令现在以 `Unknown canonical command: accept` 失败并且不写任何正式状态。

### Production Root

```text
createApplication().canonical.accept
Legacy Candidate adapter construction/injection
```

### Application

```text
src/application/canonical/accept-canonical.js
test/canonical_accept_application.test.js
```

### Repository layer

```text
src/ports/repositories/legacy-canonical-candidate-repository.js
src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js
src/ports/repositories/canonical-candidate-repository.js
src/infrastructure/filesystem/canonical-candidate-repositories.js
```

### Filesystem candidate CAS bridge

```text
canonical-repositories.js 中 canonical-candidate:* revision branch
src/infrastructure/filesystem/legacy-canonical-candidate-revision.js
test/canonical_legacy_candidate_cas.test.js
```

现在 `revisionForResource(..., 'canonical-candidate:...')` 会作为 unsupported resource fail-closed。

## 4. Remaining non-executable compatibility

仍待删除：

```text
src/application/canonical/mutation-plan.js
  -> operation=accept

src/infrastructure/filesystem/canonical-paths.js
  -> legacyCandidateManifest / candidateManifest path

src/infrastructure/in-memory/canonical-adapters.js
  -> candidate-specific test support

data/manifests/canonical/canonical_candidates.json
  -> empty historical snapshot
```

这些都不再构成可调用业务能力，也没有 filesystem reader/CAS bridge 能把历史 manifest 变成正式 mutation。

## 5. Shared current code that must survive

不要删除：

```text
src/domain/canonical/accept-policy.js
```

当前 `question-group-projection-policy.js` 仍复用 `acceptCanonicalCandidate()` 作为 Canonical aggregate create/extend 的 SSOT。

也不要删除整个：

```text
src/infrastructure/filesystem/fs-canonical-mutation-store.js
```

它仍是 Merge/Split/Canonicalize 的正式事务边界。Legacy candidate CAS evidence 已经从它依赖的 revision routing 中移除。

## 6. Checked-in legacy data

`data/manifests/canonical/canonical_candidates.json` 当前仍为空：

```text
candidate_count = 0
candidates = []
```

没有待执行 legacy candidate。

## 7. Policy / historical references

README、AGENTS、Skill、Actions/架构文档中出现 legacy 术语时，只能用于说明已退役边界、禁止回退或记录删除计划。

历史 ADR / review plan 可以保留当时术语，不作为当前操作 SSOT。

当前操作 SSOT：

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

## 8. `candidate_id` 不是删除条件

`canonical_boundary_candidate.v1` 等其它模型也使用 `candidate_id`，与 legacy Accept 无关。

真正退役继续追踪：

```text
canonical_candidates.v1
canonical_candidates.json
operation=accept
candidate-specific in-memory support
legacyCandidateManifest / candidateManifest
```

`LegacyCanonicalCandidateRepository` 与 `canonical-candidate:*` filesystem CAS 都已经是已删除项。

## 9. 下一步

下一刀只删除 MutationPlan 中的：

```text
operation=accept
```

同时删除/修改只保护该 operation 的 contract tests。

先不删除 in-memory candidate support、legacy path alias 或空 manifest，继续保持：

```text
operation=accept
→ in-memory candidate test support
→ legacy path alias / empty data
```

每一刀都必须独立跑完整 CI。
