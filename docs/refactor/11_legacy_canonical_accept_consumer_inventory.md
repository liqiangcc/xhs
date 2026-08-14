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

四层 runtime removal 已完成：

```text
Interface layer
  canonical accept CLI / runAccept / Presenter / help   removed

Production Composition Root
  canonical.accept capability                           removed
  Legacy Candidate adapter construction/injection       removed

Application layer
  src/application/canonical/accept-canonical.js         removed
  Application characterization                          removed

Repository layer
  LegacyCanonicalCandidateRepository                    removed
  Legacy filesystem Repository adapter                  removed
  deprecated Port / adapter aliases                     removed
```

当前状态：

```text
runtime_removal_in_progress_repository_layer_removed
```

因此当前代码中已经没有可读取 legacy candidate 的 Repository 能力。剩余内容只属于 `canonical-candidate:*` CAS revision、legacy path、`operation=accept` 和 test-support/data 的残余兼容。

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

`canonical_candidates.json` 在其它项目中存在同名文件，但属于无关格式/领域，不能作为本项目 consumer 证据。

因此：

```text
observable_github_external_consumer_count = 0
external_consumers_fully_observable        = false
```

## 3. 已删除的 Interface / Production / Application

已经不存在：

```text
canonical accept CLI / runAccept / Presenter
createApplication().canonical.accept
src/application/canonical/accept-canonical.js
```

CLI 反向 characterization 仍验证旧命令会以 `Unknown canonical command: accept` 失败且不产生写入。

## 4. Repository layer removal 已完成

已经删除：

```text
src/ports/repositories/legacy-canonical-candidate-repository.js
src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js
src/ports/repositories/canonical-candidate-repository.js
src/infrastructure/filesystem/canonical-candidate-repositories.js
```

`canonical_mutation_contracts.test.js` 也不再把 Canonical Candidate Repository 当作当前 Application read port。

原 `canonical_accept_filesystem_integration.test.js` 已删除，因为它保护的是已退役 Repository 能力。

## 5. CAS bridge 被单独保留

为了不把 Repository removal 和 CAS removal 混成一刀，新增了最小 helper：

```text
src/infrastructure/filesystem/legacy-canonical-candidate-revision.js
```

它唯一职责是：

```text
canonical-candidate:<id>
  -> 读取 legacy manifest 中对应历史 candidate
  -> 计算 semantic opaque revision
```

它**不提供**：

```text
Repository Port
get(candidateId)
candidate DTO snapshot
Application dependency
```

`canonical-repositories.js` 的通用 revision router 只通过这个 helper 保留旧 `canonical-candidate:*` CAS evidence。

对应测试现在是：

```text
test/canonical_legacy_candidate_cas.test.js
```

它证明 metadata-only manifest 变化不改变 candidate revision，而 candidate 语义变化会改变 revision。

## 6. Remaining compatibility

仍待删除：

```text
src/infrastructure/filesystem/legacy-canonical-candidate-revision.js
src/infrastructure/filesystem/canonical-repositories.js
  -> canonical-candidate:<id> revision routing
src/infrastructure/filesystem/canonical-paths.js
  -> legacyCandidateManifest / candidateManifest path
src/application/canonical/mutation-plan.js
  -> operation=accept
src/infrastructure/in-memory/canonical-adapters.js
  -> candidate-specific test support
data/manifests/canonical/canonical_candidates.json
  -> empty historical snapshot
```

这些都不再构成可调用业务能力。

## 7. Shared current code that must survive

不要删除：

```text
src/domain/canonical/accept-policy.js
```

当前 `question-group-projection-policy.js` 仍复用 `acceptCanonicalCandidate()` 作为 Canonical aggregate create/extend 的 SSOT。

也不要删除整个：

```text
src/infrastructure/filesystem/fs-canonical-mutation-store.js
```

它仍是 Merge/Split/Canonicalize 的正式事务边界。后续只移除 legacy candidate revision evidence。

## 8. Checked-in legacy data

`data/manifests/canonical/canonical_candidates.json` 当前仍为空：

```text
candidate_count = 0
candidates = []
```

没有待执行 legacy candidate 阻止继续退役。

## 9. Policy / historical references

README、AGENTS、Skill、Actions/架构文档中出现 legacy 术语时，只能用于说明已退役边界、禁止回退或记录删除计划。

历史 ADR / review plan 可以保留当时术语，不作为当前操作 SSOT。

当前操作 SSOT：

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

## 10. `candidate_id` 不是删除条件

`canonical_boundary_candidate.v1` 等其它模型也使用 `candidate_id`，与 legacy Accept 无关。

真正退役继续追踪：

```text
canonical_candidates.v1
canonical_candidates.json
canonical-candidate:<id> revision
operation=accept
```

`LegacyCanonicalCandidateRepository` 已经不是“待删除项”，而是“已删除项”。

## 11. 下一步

下一刀只删除 CAS bridge：

```text
canonical-repositories.js 中 canonical-candidate:* revision branch
legacy-canonical-candidate-revision.js
canonical_legacy_candidate_cas.test.js
```

先不删除 `operation=accept`、legacy path alias、in-memory candidate support 或空 manifest。

依赖继续按层收缩：

```text
canonical-candidate CAS bridge
→ operation=accept
→ in-memory candidate test support
→ legacy path alias / empty data
```

每一刀都必须独立跑完整 CI。
