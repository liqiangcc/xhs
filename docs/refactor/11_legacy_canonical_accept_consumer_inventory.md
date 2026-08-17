# 11 Legacy Canonical Accept Consumer Inventory

> 本文是 legacy `canonical accept` 退役结果的人类可读摘要。机器可检查事实源是同目录下 `11_legacy_canonical_accept_consumer_inventory.json`。

## 1. 最终结论

仓库内 legacy `canonical accept` 已完全退役。

当前正式流程只有：

```text
canonical suggest
  → RelationCandidate
  → dedup decide
  → RelationDecision
  → dedup apply
  → Canonical mutation
```

机器状态：

```text
fully_retired_repository_local_with_unobservable_external_risk
```

仓库内 blocker = 0；GitHub 可观察的项目特异外部消费者 = 0。仍保留一个事实限制：GitHub 搜索无法证明本地 shell、未提交自动化、不可访问/未索引私有仓库中绝对不存在旧调用。

## 2. 已删除的 legacy 层

按关注点逐层删除完成：

```text
1. Interface
   canonical accept CLI / runAccept / Presenter / help

2. Production Composition Root
   createApplication().canonical.accept
   legacy candidate adapter wiring

3. Application
   src/application/canonical/accept-canonical.js

4. Repository layer
   LegacyCanonicalCandidateRepository
   filesystem candidate Repository
   deprecated Port / adapter aliases

5. Filesystem CAS
   canonical-candidate:<id> revision routing
   legacy candidate revision helper

6. MutationPlan contract
   operation=accept

7. In-memory test support
   candidate seed/state/repository/revision/upsert/snapshot members

8. Final path/data residue
   legacyCandidateManifest / candidateManifest
   data/manifests/canonical/canonical_candidates.json
```

现在不存在任何 repository-local execution/data path 能把 `canonical_candidates.v1` 转成 Canonical mutation。

## 3. 当前防回归边界

CI 会持续验证：

```text
canonical accept CLI 不存在
Production Root 不暴露 canonical.accept
Accept Application 不存在
Legacy Candidate Repository / adapter 不存在
canonical-candidate:* Filesystem CAS 不存在
MutationPlan 不支持 operation=accept
in-memory Canonical adapter 不包含 candidate-specific support
canonical-paths 不暴露 legacy candidate path
canonical_candidates.json 不存在
Suggest / Actions 不生成 legacy manifest
```

历史 ADR / review plan 可以保留旧术语作为历史证据，不作为当前操作说明。

## 4. 当前正式 SSOT

当前 Canonical / Dedup 操作路径：

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

核心约束：

```text
Detect != Decide != Apply
RelationCandidate != mutation authorization
Similarity / AI evidence != RelationDecision
```

## 5. 必须保留的当前代码

不要因为名字里有 `accept` 就删除：

```text
src/domain/canonical/accept-policy.js
```

当前 `question-group-projection-policy.js` 仍复用 `acceptCanonicalCandidate()` 作为 Canonical aggregate create/extend 的 Domain SSOT。

也不要删除整个 `fs-canonical-mutation-store.js`；它仍是 Merge/Split/Canonicalize 的正式事务边界。

## 6. `candidate_id` 不是 legacy 判定条件

其它模型仍可能合法使用 `candidate_id`，例如：

```text
canonical_boundary_candidate.v1
```

它用于已有 Canonical 的边界审查，与已退役的 `canonical_candidates.v1` 不同。

## 7. 外部消费者观测限制

2026-08-14 已搜索以下项目特异标识：

```text
scripts/xhs.js canonical accept
liqiangcc/xhs canonical accept
canonical_candidates.v1
LegacyCanonicalCandidateRepository
legacy-canonical-candidate-repositories
```

未发现 `liqiangcc/xhs` 之外的可观察消费者。

这个结论是“可观察外部消费者为 0”，不是“宇宙中绝对不存在任何旧调用者”。仓库内不再为不可观测风险保留死兼容代码。
