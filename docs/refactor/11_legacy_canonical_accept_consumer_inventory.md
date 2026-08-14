# 11 Legacy Canonical Accept Consumer Inventory

> 本文解释 `canonical accept` 的最终消费者清单与退役准备度。机器可检查的事实源是同目录下 `11_legacy_canonical_accept_consumer_inventory.json`。

## 1. 当前结论

当前正式 Dedup / Canonical 流程已经完全不依赖 legacy Accept：

```text
canonical suggest
  -> RelationCandidate
  -> dedup decide
  -> RelationDecision
  -> dedup apply
  -> Canonical mutation
```

仓库内检查已经确认：

```text
current Suggest 生成 legacy manifest      = false
GitHub Actions 生成 legacy manifest       = false
npm scripts 调用 canonical accept         = false
当前 in_progress root task 调用 Accept    = false
checked-in legacy candidate               = 0
active manual procedure blocker           = 0
```

进一步通过 GitHub code search 检查项目特异标识后，没有发现可观察的外部消费者。因此当前状态是：

```text
ready_for_runtime_removal_with_unobservable_external_risk
```

含义是：

```text
仓库内退役条件                         已满足
GitHub 可观察项目特异外部消费者         0
本地脚本 / 未提交自动化 / 未索引私有调用 无法证明不存在
```

这不是“绝对证明世界上没有外部调用者”，而是已经把可验证范围内的风险收敛到只剩不可观测残余风险。

## 2. 外部消费者搜索

2026-08-14 使用当前连接可见的 GitHub code search / public code index 检查：

```text
scripts/xhs.js canonical accept
liqiangcc/xhs canonical accept
canonical_candidates.v1
LegacyCanonicalCandidateRepository
legacy-canonical-candidate-repositories
```

项目特异查询没有发现 `liqiangcc/xhs` 之外的消费者。

`canonical_candidates.json` 这个泛化文件名在其它 GitHub 项目中确实存在，但它们属于完全不同的领域和格式，不能仅因为文件名相同就认定为本项目 consumer。

因此机器 inventory 记录：

```text
observable_github_search_completed        = true
observable_github_external_consumer_count = 0
external_consumers_fully_observable        = false
```

最后一个字段必须保持 `false`：GitHub 搜索无法看到用户机器上的 shell、未提交脚本、未授权/未索引仓库等状态。

## 3. Source-level deprecation

为了在真正删除前先固定方向，legacy Accept 的主要入口已经增加源码级 `@deprecated` 标记：

```text
scripts/commands/canonical.js::runAccept
src/application/canonical/accept-canonical.js::createAcceptCanonicalUseCase
src/ports/repositories/legacy-canonical-candidate-repository.js
src/interfaces/cli/canonical-accept-presenter.js
```

替代路径统一为：

```text
canonical suggest
  -> dedup decide
  -> dedup apply
```

弃用标记只存在于源码注释/JSDoc：

```text
不新增 runtime warning
不修改 stdout / stderr
不修改 JSON response
不修改 exit code
不修改 MutationPlan
不修改 preflight / commit 行为
```

这样兼容消费者在真正删除前不会因为“弃用准备”本身发生行为回归。

## 4. Runtime compatibility chain

当前真正执行 legacy Accept 的链路仍然是：

```text
scripts/xhs.js / canonical CLI
        ↓
scripts/commands/canonical.js::runAccept
        ↓
createApplication().canonical.accept
        ↓
Accept Application
        ↓
LegacyCanonicalCandidateRepository
        ↓
legacy-canonical-candidate-repositories.js
        ↓
canonical_candidates.v1
        ↓
canonical_mutation_plan.v1(operation=accept)
        ↓
MutationStore CAS / commit
```

相关生产文件：

```text
scripts/commands/canonical.js
scripts/xhs.js
src/bootstrap/create-application.js
src/application/canonical/accept-canonical.js
src/application/canonical/mutation-plan.js
src/ports/repositories/legacy-canonical-candidate-repository.js
src/infrastructure/filesystem/legacy-canonical-candidate-repositories.js
src/infrastructure/filesystem/canonical-paths.js
src/infrastructure/filesystem/canonical-repositories.js
src/interfaces/cli/canonical-accept-presenter.js
```

其中 `canonical-repositories.js` 还有一个容易漏掉的兼容点：MutationStore preflight 需要重新计算 `canonical-candidate:<id>` revision，所以通用 Canonical revision router 仍保留 legacy candidate 分支。

## 5. Test-support compatibility

`src/infrastructure/in-memory/canonical-adapters.js` 仍包含：

```text
canonicalCandidateRepository
canonical-candidate:<id> revision
candidate fixtures / revision bumps
```

它用于 Accept 的纯 Application/事务 characterization，但 Production Composition Root 不会创建这个 adapter。

因此真正删除 Accept 时，只清理 candidate-specific members，不能删除整个 in-memory Canonical adapter，因为 Merge/Split/Canonicalize 测试仍复用它。

## 6. Shared current code that must survive retirement

有一个特别容易误删的命名陷阱：

```text
src/domain/canonical/accept-policy.js
```

虽然文件名带 `accept`，但它已经不是 legacy-only Domain code。当前：

```text
question-group-projection-policy.js
  -> acceptCanonicalCandidate()
  -> refreshCanonicalFromQuestions()
```

仍把 `acceptCanonicalCandidate()` 当作 Canonical aggregate create/extend 的 SSOT。

因此退役时必须区分：

```text
legacy Accept CLI / Application / candidate input  -> 可删除
accept-policy 的 Canonical 聚合语义                -> 当前仍在使用，必须保留
```

除非先有独立 refactor 把这部分语义迁移到新的、同样单一事实源的命名中，否则不能因为删除 `canonical accept` 顺手删除 `accept-policy.js`。

同理，`src/infrastructure/filesystem/fs-canonical-mutation-store.js` 是 Merge/Split/Canonicalize 共同使用的当前事务边界。退役只应删除 legacy candidate revision evidence，不应删除 MutationStore 本身。

## 7. Compatibility aliases

以下模块只保留 deprecated re-export：

```text
src/ports/repositories/canonical-candidate-repository.js
src/infrastructure/filesystem/canonical-candidate-repositories.js
```

它们不是新代码应继续使用的 Port / adapter；真正删除 Accept 时应与 legacy Port/adapter 一起删除。

## 8. Checked-in legacy data

当前：

```text
data/manifests/canonical/canonical_candidates.json
```

仍是：

```text
schema_version = canonical_candidates.v1
candidate_count = 0
candidates = []
```

所以没有“尚未执行的 legacy candidate”阻止退役。

## 9. Current policy references are not consumers

README、AGENTS、Skill、Actions/架构文档仍可能出现 `canonical accept` 字样，但目的都是明确兼容边界或禁止新流程回退到 Accept。这些属于 anti-regression policy，不是业务消费者。

当前操作 SSOT 仍是：

```text
docs/refactor/10_current_dedup_canonical_operations.md
```

内容建设文档 `08_content_building_goals.md` 也已经改为：

```text
候选召回
  -> canonical suggest
  -> explicit dedup decide
  -> dedup apply (same / alias)
     或 canonical merge / split（维护已有 Canonical）
```

因此 repository-local active blocker 已清零。

## 10. Historical references are not consumers

历史 ADR、旧 Actions TODO、已完成 review plan 可以保留当时术语，因为它们是历史证据而非当前命令 SSOT。删除历史术语不会提高架构安全，反而破坏决策证据链。

## 11. `candidate_id` 不是可靠的 legacy 搜索条件

仓库还有另一套完全不同的模型：

```text
canonical_boundary_candidate.v1
```

用于已有 Canonical 之间的边界审查。它也使用 `candidate_id`，但不会进入 `canonical accept`。

因此真正退役时应追踪强语义标识：

```text
canonical_candidates.v1
canonical_candidates.json
canonical accept --candidate-id
LegacyCanonicalCandidateRepository
canonical-candidate:<id> revision
operation=accept
```

而不是机械删除所有 `candidate_id`。

## 12. Tests

legacy Accept 行为仍由 characterization 保护；在真正 runtime 删除前，这些测试证明 deprecated 标记没有改变兼容行为。

anti-regression / inventory guard 继续负责：

```text
当前 Suggest 不得生成 legacy manifest
当前文档不得把新关系路由到 Accept
inventory 不得出现未分类强 legacy 引用
source-level deprecation 必须存在且不得引入 runtime warning
```

## 13. 进入 runtime 删除 slice 的条件

目前可验证的前置条件已经满足：

```text
repository-local active blocker = 0
observable GitHub external consumer = 0
legacy checked-in candidate = 0
source-level deprecation = marked
```

真正删除时仍必须遵守：

1. 接受“本地/未提交/未索引私有调用者不可证明不存在”的残余风险；
2. 保留 `accept-policy.js` 当前 Canonicalization SSOT 职责；
3. 删除过程中每个逻辑 slice 都跑完整 CI；
4. 不把 shared MutationStore、refresh-policy 或 unrelated boundary candidate 一起误删。

## 14. 推荐删除顺序

```text
1. 移除 canonical accept CLI / presenter
2. 从 Composition Root 移除 canonical.accept
3. 删除 Accept Application
4. 删除 LegacyCanonicalCandidateRepository + FS adapter
5. 删除 canonical-candidate revision bridge
6. 从 MutationPlan supported operations 删除 accept
7. 删除 in-memory candidate test support
8. 删除 deprecated compatibility aliases
9. 删除 legacy-only characterization
10. 删除空 canonical_candidates.json
11. 将 anti-legacy guard 改成“legacy runtime 不得重新出现”
```

不要先删底层 adapter 再留下半可用 CLI；从 Interface 向内收缩，失败面最清楚。

**不要把 `accept-policy.js`、`refresh-policy.js` 或 `CanonicalMutationStore` 本身列入 legacy 删除清单。**
