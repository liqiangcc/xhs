# 11 Legacy Canonical Accept Consumer Inventory

> 本文解释 `canonical accept` 的最终消费者清单。机器可检查的事实源是同目录下 `11_legacy_canonical_accept_consumer_inventory.json`。

## 1. 结论

当前仓库已经达到 **repository-local retirement ready**：仓库内没有仍要求新工作使用 `canonical accept` 的活跃流程，正式 Dedup 链路也不生成或消费 `canonical_candidates.v1`。

当前正式链路是：

```text
canonical suggest
  -> RelationCandidate
  -> dedup decide
  -> RelationDecision
  -> dedup apply
  -> Canonical mutation
```

仓库内仍保留三类 legacy 内容，但它们现在都是明确的退役对象或保护性说明：

1. 一整条显式的 runtime compatibility chain，用于执行历史/手工 `canonical_candidates.v1`；
2. 一套仅服务 legacy Accept characterization 的 in-memory test support；
3. 当前架构/Agent 文档中用于**禁止新流程回退到 Accept**的 policy reference。

仓库内没有发现其它活跃执行依赖：

```text
package.json npm scripts          -> no canonical accept
.github/workflows/*.yml           -> no canonical accept / legacy manifest
当前 in_progress root task        -> no canonical accept / canonical_candidates
08 内容建设批次流程               -> suggest / decide / apply
checked-in legacy candidate data  -> 0 candidates
```

所以当前 retirement 状态是：

```text
repository_local_ready_external_confirmation_required
```

这里的限制只剩一个仓库搜索无法证明的事实：**是否存在仓库外人工脚本、旧 checkout 或其它外部调用者仍在调用 `canonical accept`。** 在没有外部确认前，不应把“repository-local ready”表述成“全局无消费者”。

## 2. Runtime compatibility chain

当前真正执行 legacy Accept 的链路是：

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

其中 `canonical-repositories.js` 还有一个容易漏掉的兼容点：MutationStore preflight 需要重新计算 `canonical-candidate:<id>` revision，所以通用 Canonical revision router 仍保留 legacy candidate 分支。该 import 已改为显式 `legacy-canonical-candidate-repositories`，不再通过旧 generic alias 隐藏依赖。

## 3. Test-support compatibility

`src/infrastructure/in-memory/canonical-adapters.js` 仍包含：

```text
canonicalCandidateRepository
canonical-candidate:<id> revision
candidate fixtures / revision bumps
```

它用于 Accept 的纯 Application/事务 characterization，但 Production Composition Root 不会创建这个 adapter。

因此它属于**测试兼容消费者**，不是线上 runtime dependency；真正删除 Accept 时应只清理 candidate-specific members，不能删除整个 in-memory Canonical adapter，因为 Merge/Split/Canonicalize 测试仍复用它。

## 4. Shared current code that must survive retirement

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

同理：

```text
src/infrastructure/filesystem/fs-canonical-mutation-store.js
```

是 Merge/Split/Canonicalize 共同使用的当前事务边界。退役只应删除 `canonical-candidate:*` revision evidence 的兼容分支，不应删除 MutationStore 本身。

## 5. Compatibility aliases

为了不突然破坏旧测试或外部调用者，以下模块只保留 deprecated re-export：

```text
src/ports/repositories/canonical-candidate-repository.js
src/infrastructure/filesystem/canonical-candidate-repositories.js
```

它们不是新代码应继续使用的 Port / adapter。

真正删除 Accept 时，这两个 alias 应与 legacy Port/adapter 一起删除，而不是长期保留成为第二个入口。

## 6. Checked-in legacy data

当前仓库中的：

```text
data/manifests/canonical/canonical_candidates.json
```

仍是：

```text
schema_version = canonical_candidates.v1
candidate_count = 0
candidates = []
```

因此当前 checked-in 文件没有任何尚待执行的 legacy candidate。

这很重要：从仓库数据本身看，没有“删掉 Accept 会丢失尚未处理候选”的证据。

但它只能证明仓库内状态，不能证明仓库外没有人工脚本或旧调用者。

## 7. Active documentation blocker 已清零

`docs/refactor/08_content_building_goals.md` 过去的一段批次闭环写成：

```text
候选召回
  -> 去重与边界确认
  -> canonical accept / merge / split
  -> ...
```

这处活跃残留现在已经迁移为：

```text
候选召回
  -> canonical suggest
  -> explicit dedup decide
  -> dedup apply (same / alias)
     或 canonical merge / split (维护已有 Canonical)
  -> answer validate / sync
  -> canonical check
```

并显式引用 `docs/refactor/10_current_dedup_canonical_operations.md` 作为命令级 SSOT。

因此 repository-local inventory 中：

```text
active_manual_procedure_blocker_count = 0
active_blockers = []
```

仓库内已经没有仍指导新候选走 legacy Accept 的活跃人工流程。

## 8. Current policy references are not active consumers

以下当前文档/Agent 文件会提到 `canonical accept`，但目的都是**明确禁止它成为新流程**或描述兼容边界：

```text
README.md
AGENTS.md
.agents/skills/xhs-answer-curator/SKILL.md
.agents/skills/xhs-answer-curator/references/repo-map.md
docs/refactor/06_github_actions_ai_management.md
docs/refactor/08_content_building_goals.md
docs/refactor/09_legacy_canonical_accept_boundary.md
docs/refactor/10_current_dedup_canonical_operations.md
docs/refactor/10_soc_srp_architecture.md
```

其中 `08_content_building_goals.md` 现在只引用当前 Dedup 操作 SSOT，不再把 `canonical accept` 作为批次动作。

这些 policy reference 不能因为字符串扫描命中就被当成 blocker；它们属于 current routing / anti-regression policy。

## 9. Historical references are not consumers

以下文件可以保留旧术语，因为它们是历史设计/验收证据，而不是当前命令 SSOT：

```text
docs/adr/003-agent-candidates-script-state.md
docs/refactor/07_actions_review_todo.md
review/plans/c1_asset_calibration.md
review/plans/c6_scale_and_entry_delivery.md
```

删除历史术语不会提高架构安全，反而会破坏“当时为什么这样做”的证据链。

历史文件只需要确保不会被当前 README / AGENTS / Skill 当作操作依据。

## 10. `candidate_id` 不是可靠的 legacy 搜索条件

仓库还有另一套完全不同的 candidate：

```text
scripts/content/audit_canonical_boundaries.js
  -> canonical_boundary_candidate.v1
  -> candidate_id = boundary_<canonicalA>_<canonicalB>
```

以及：

```text
data/manifests/canonical/boundary_review_decisions.json
data/manifests/canonical/long_tail_duplicate_candidates.jsonl
```

这些 `candidate_id` 用于**已有 Canonical 之间的边界审查**，不是 `canonical_candidates.v1`，也不会进入 `canonical accept`。

因此未来退役扫描不能简单做：

```text
grep candidate_id -> 全部删除
```

应追踪强语义标识：

```text
canonical_candidates.v1
canonical_candidates.json
--candidate-id on canonical accept
LegacyCanonicalCandidateRepository
canonical-candidate:<id> revision
operation=accept
```

## 11. Tests

legacy Accept 行为仍由 characterization 保护，主要包括：

```text
test/canonical_accept_application.test.js
test/canonical_accept_filesystem_integration.test.js
test/canonical_accept_presenter.test.js
test/canonical_characterization.test.js
test/canonical.test.js
test/canonical_mutation_contracts.test.js
```

anti-regression / inventory guards 包括：

```text
test/legacy_canonical_accept_boundary.test.js
test/current_dedup_operational_docs.test.js
test/legacy_canonical_accept_consumer_inventory.test.js
```

前一类在真正删除 Accept 时应删除或改写；后一类应改成“legacy 已不存在”的永久 guard，而不是一起丢掉。

## 12. Repository-local retirement criteria

以下 repository-local 条件现在已经满足：

1. `08_content_building_goals.md` 不再把 `canonical accept` 作为当前批次操作；
2. README / AGENTS / Skill / Actions 只推荐 Suggest -> Decide -> Apply；
3. GitHub Actions 不生成 `canonical_candidates.json`；
4. `package.json` 不存在调用 legacy Accept 的 npm script；
5. 当前 `in_progress` root task 不依赖 `canonical accept` / `canonical_candidates.v1`；
6. checked-in legacy manifest 为空；
7. 没有仓库内脚本/自动化重新生成 legacy manifest。

真正删除 runtime compatibility chain 前还需要保留两个约束：

8. 确认是否存在仓库外人工调用者；这一点仅靠 GitHub repository search 无法证明；
9. 删除 legacy runtime、test-support、alias、operation/tests/data 后完整 CI 仍能通过。

同时必须继续保护当前共享代码：

10. `accept-policy.js` 的 Canonicalization SSOT 职责必须保留，或先有等价迁移。

因此当前准确状态不是“完全可删”，而是：

```text
repository-local ready
+ external usage confirmation required
+ deletion slice still needs its own CI proof
```

## 13. 建议的真正删除顺序

完成外部使用确认后，建议按依赖方向删除：

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
10. 删除空 canonical_candidates.json（若确认无需恢复入口）
11. 将 anti-legacy guard 改成“legacy runtime 不得重新出现”
```

不要先删底层 adapter 再留下半可用 CLI；从 Interface 向内收缩，能让每一步的失败面最清楚。

**不要把 `accept-policy.js`、`refresh-policy.js` 或 `CanonicalMutationStore` 本身列入上述删除清单。** 它们仍有当前非 legacy 职责。
