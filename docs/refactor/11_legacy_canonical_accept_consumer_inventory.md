# 11 Legacy Canonical Accept Consumer Inventory

> 本文解释 `canonical accept` 的最终消费者清单。机器可检查的事实源是同目录下 `11_legacy_canonical_accept_consumer_inventory.json`。

## 1. 结论

当前仓库**还不能直接删除** `canonical accept`，但原因已经非常具体。

不是因为当前 Dedup 流程仍依赖它：

```text
canonical suggest
  -> RelationCandidate
  -> dedup decide
  -> RelationDecision
  -> dedup apply
  -> Canonical mutation
```

这条正式链路已经完全不生成或消费 `canonical_candidates.v1`。

真正剩余的是：

1. 一整条显式的 runtime compatibility chain，用于执行历史/手工 `canonical_candidates.v1`；
2. 一套仅服务 legacy Accept characterization 的 in-memory test support；
3. 当前架构/Agent 文档中用于**禁止新流程回退到 Accept**的 policy reference；
4. `docs/refactor/08_content_building_goals.md` 仍有一处当前内容建设步骤写着 `canonical accept / merge / split`，因此仓库内仍存在一个会指导人继续使用 Accept 的活跃文档残留。

所以当前 retirement 状态是：

```text
blocked_by_active_documentation
```

而不是“业务新流程仍未迁移”。

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

因此它属于**测试兼容消费者**，不是线上 runtime dependency；真正删除 Accept 时应随 legacy-only characterization 一起清理。

## 4. Compatibility aliases

为了不突然破坏旧测试或外部调用者，以下模块只保留 deprecated re-export：

```text
src/ports/repositories/canonical-candidate-repository.js
src/infrastructure/filesystem/canonical-candidate-repositories.js
```

它们不是新代码应继续使用的 Port / adapter。

真正删除 Accept 时，这两个 alias 应与 legacy Port/adapter 一起删除，而不是长期保留成为第二个入口。

## 5. Checked-in legacy data

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

## 6. Active documentation blocker

`docs/refactor/08_content_building_goals.md` 是当前内容建设目标与 DoD 文档，但它的一段批次闭环仍写着：

```text
候选召回
  -> 去重与边界确认
  -> canonical accept / merge / split
  -> ...
```

这与当前操作 SSOT 冲突。

当前正确解释应是：

```text
候选召回
  -> canonical suggest
  -> explicit dedup decide
  -> dedup apply (same / alias)
     或 canonical merge / split (维护已有 Canonical)
  -> answer validate / sync
  -> canonical check
```

在这处活跃说明被清理前，不能声称仓库已经没有人工 `canonical accept` 使用路径。

## 7. Current policy references are not active consumers

以下当前文档/Agent 文件会提到 `canonical accept`，但目的都是**明确禁止它成为新流程**或描述兼容边界：

```text
README.md
AGENTS.md
.agents/skills/xhs-answer-curator/SKILL.md
.agents/skills/xhs-answer-curator/references/repo-map.md
docs/refactor/06_github_actions_ai_management.md
docs/refactor/09_legacy_canonical_accept_boundary.md
docs/refactor/10_current_dedup_canonical_operations.md
docs/refactor/10_soc_srp_architecture.md
```

这些引用不能因为字符串扫描命中就被当成 blocker；它们属于 anti-regression policy。

## 8. Historical references are not consumers

以下文件可以保留旧术语，因为它们是历史设计/验收证据，而不是当前命令 SSOT：

```text
docs/adr/003-agent-candidates-script-state.md
docs/refactor/07_actions_review_todo.md
review/plans/c1_asset_calibration.md
review/plans/c6_scale_and_entry_delivery.md
```

删除历史术语不会提高架构安全，反而会破坏“当时为什么这样做”的证据链。

历史文件只需要确保不会被当前 README / AGENTS / Skill 当作操作依据。

## 9. `candidate_id` 不是可靠的 legacy 搜索条件

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

## 10. Tests

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

## 11. Repository-local retirement criteria

下一阶段只有在以下条件满足后，才适合真正删除 runtime compatibility chain：

1. `08_content_building_goals.md` 不再把 `canonical accept` 作为当前批次操作；
2. README / AGENTS / Skill / Actions 继续只推荐 Suggest -> Decide -> Apply；
3. GitHub Actions 不生成 `canonical_candidates.json`；
4. checked-in legacy manifest 继续为空，或者已有明确迁移方案；
5. 没有仓库内脚本/自动化重新生成 legacy manifest；
6. 已确认是否存在仓库外人工调用者；这一点仅靠 GitHub repository search 无法证明；
7. 删除 legacy runtime、test-support、alias、operation/tests/data 后完整 CI 仍能通过。

## 12. 建议的真正删除顺序

当上述 blocker 清零后，建议按依赖方向删除：

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
