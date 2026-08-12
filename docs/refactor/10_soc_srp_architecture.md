# 10 SoC / SRP 架构重构设计

> 目标：把关注点分离（Separation of Concerns, SoC）与单一职责原则（Single Responsibility Principle, SRP）固化为 `xhs` 后续开发的架构硬约束。
>
> 本文只定义模块边界、依赖方向、迁移策略和验收标准，不在本次提交中修改业务代码。

---

## 1. 背景

`xhs` 已从早期“小红书面经抓取 + AI 提取 + 查询脚本”演进为知识资产系统，主链路为：

```text
Question -> CanonicalQuestion -> Answer -> ReviewProgress
```

当前统一入口已经收敛为：

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

这是正确方向，但当前 `scripts/commands/*.js` 中仍存在多种职责混合：

- CLI 参数解析；
- 应用用例编排；
- Canonical 业务规则；
- 相似度与去重逻辑；
- JSONL / 文件读写；
- ReviewProgress 迁移；
- Answer 归档；
- Index 重建；
- 报告与 stdout/stderr 输出。

随着 Canonical、Answer、Evidence、Review 和质量门禁不断增长，这种结构会造成：

1. 一个规则变化触发多个无关模块修改；
2. CLI、GitHub Actions、未来 MCP 之间复制业务逻辑；
3. JSONL 切换 SQLite 时影响上层业务；
4. AI suggestion 与实际状态修改耦合；
5. 测试难以隔离领域逻辑；
6. 大文件承担过多职责，代码审查和回归风险持续上升。

因此下一阶段重构的目标不是“大改目录”，而是建立稳定的责任边界。

---

## 2. 核心原则

### 2.1 关注点分离

不同类型的变化必须落在不同模块：

```text
交互方式变化       -> Interface
用例执行顺序变化   -> Application
业务规则变化       -> Domain
存储实现变化       -> Infrastructure
外部系统变化       -> Adapter
```

任何模块都不得因为多个完全不同的变化原因而频繁修改。

### 2.2 单一职责

判断一个模块是否违反 SRP，统一使用下面的问题：

> 这个模块有几个彼此独立的“修改原因”？

例如，一个文件同时因为以下变化而需要修改：

- CLI 参数格式变化；
- Canonical merge 规则变化；
- JSONL 格式变化；
- ReviewProgress 规则变化；
- GitHub Issue 格式变化；

则该模块必须拆分。

SRP 不等于“每个函数只能做一件小事”，而是：

> 一个模块只服务于一个稳定的责任边界。

### 2.3 依赖方向单向

目标依赖方向固定为：

```text
Interfaces
    ↓
Application
    ↓
Domain
    ↑
Ports
    ↑
Infrastructure / Adapters
```

Domain 是最稳定的核心，不允许反向依赖 CLI、GitHub、文件系统或数据库。

---

## 3. 目标架构

```text
┌────────────────────────────────────────────┐
│ Interfaces                                 │
│ CLI / GitHub Actions / future MCP          │
├────────────────────────────────────────────┤
│ Application                                │
│ use cases / orchestration / transactions   │
├────────────────────────────────────────────┤
│ Domain                                     │
│ Question / Canonical / Dedup / Answer /    │
│ AnswerQuality / Review                     │
├────────────────────────────────────────────┤
│ Ports                                      │
│ Repository / Evidence / External services  │
├────────────────────────────────────────────┤
│ Infrastructure / Adapters                  │
│ JSONL / FS / GitHub / AI / future SQLite   │
└────────────────────────────────────────────┘
```

推荐逐步迁移到：

```text
src/
├── domain/
│   ├── question/
│   ├── canonical/
│   ├── dedup/
│   ├── answer/
│   ├── answer-quality/
│   └── review/
│
├── application/
│   ├── question/
│   ├── canonical/
│   ├── dedup/
│   ├── answer/
│   └── review/
│
├── ports/
│   ├── repositories/
│   └── services/
│
├── infrastructure/
│   ├── jsonl/
│   ├── filesystem/
│   ├── github/
│   └── ai/
│
└── interfaces/
    ├── cli/
    ├── github-actions/
    └── mcp/
```

迁移期间允许旧 `scripts/` 与 `src/` 并存，但新业务规则不得继续沉积到大型 `scripts/commands/*.js`。

---

## 4. Interface Layer

### 4.1 职责

Interface 只负责：

```text
输入解析
输入校验（语法级）
构造 application DTO
调用 use case
输出格式化
exit code / transport response
```

### 4.2 禁止事项

Interface 不允许：

- 决定 Canonical 是否可以 merge；
- 计算 priority；
- 直接读写 JSONL；
- 修改 ReviewProgress；
- 决定答案是否 curated；
- 实现 Jaccard / embedding 等相似度规则；
- 直接组合多个 Repository 完成业务流程。

### 4.3 CLI 示例

理想的 CLI command 应保持很薄：

```js
async function runMergeCommand(argv, app) {
    const input = parseMergeArgs(argv);
    const result = await app.mergeCanonical(input);
    printResult(result);
    return 0;
}
```

CLI 参数变化不应影响 Domain。

---

## 5. Application Layer

### 5.1 职责

Application 负责“完成一个用例所需的执行顺序”。

例如 `MergeCanonical`：

```text
load source canonical
load target canonical
load affected questions/review/answers
        ↓
call domain policy
        ↓
apply domain result
        ↓
persist records
        ↓
archive/migrate references
        ↓
rebuild required indexes
        ↓
return use-case result
```

Application 负责流程，不负责定义业务正确性。

### 5.2 示例目录

```text
src/application/canonical/
├── accept-candidate.js
├── merge-canonical.js
├── split-canonical.js
└── suggest-canonical.js
```

### 5.3 禁止事项

Application 不允许：

- 直接解析 JSONL；
- 直接操作 `fs`；
- 把业务规则写成大量 if/else；
- 依赖 CLI argv；
- 依赖 GitHub API payload 格式。

---

## 6. Domain Layer

Domain 是系统核心，只描述业务概念和业务规则。

### 6.1 Canonical Domain

建议拆分：

```text
src/domain/canonical/
├── canonical.js
├── canonical-policy.js
├── canonical-priority.js
└── canonical-relation.js
```

典型接口：

```text
canMergeCanonical(source, target)
calculateCanonicalPriority(stats)
classifyCanonicalRelation(a, b)
buildCanonicalAliases(questions)
```

### 6.2 Domain 禁止依赖

Domain 不允许依赖：

```text
fs
path
process.argv
console
GitHub API
JSONL 路径
SQLite
AI SDK
GitHub Actions
MCP transport
```

Domain 单元测试必须可以使用纯内存对象执行。

---

## 7. Canonical Dedup 必须独立

当前 Canonical 数量已经很大，去重不能继续作为 Canonical CRUD 的附属逻辑。

建议独立：

```text
src/domain/dedup/
├── similarity.js
├── relation.js
└── merge-policy.js

src/application/dedup/
├── build-review-queue.js
├── review-candidate.js
└── apply-merge-decision.js
```

流程必须固定为：

```text
Detect
  ↓
Review / Decide
  ↓
Apply
```

即：

```text
相似度检测 != 关系判断 != 状态修改
```

相似度算法只能产生候选，禁止直接 merge Canonical。

推荐关系模型：

```text
same
alias
parent_child
followup
related
unrelated
```

只有经过明确 decision 的结果才能进入 Canonical merge use case。

---

## 8. Answer Quality 必须拆分关注点

答案质量已经包含多个独立维度，不应继续无限扩展单一 `answer_quality.js`。

建议：

```text
src/domain/answer-quality/
├── quality-contract.js
├── quality-score.js
├── hard-failure-policy.js
├── evidence-policy.js
├── oral-quality-policy.js
└── followup-policy.js
```

题型专项规则独立：

```text
src/domain/answer-type/
├── concept-policy.js
├── mechanism-policy.js
├── scenario-policy.js
├── coding-policy.js
├── project-policy.js
└── behavior-policy.js
```

### 8.1 检测与修改必须分离

以下约束为硬规则：

```text
answer audit != answer promote
```

`audit` 只能输出：

```text
PASS / FAIL
score
hard failures
findings
evidence status
```

不能顺便修改正式 Answer 状态。

`promote` 是独立 Application use case，必须重新验证所有 promotion 前置条件后才能修改：

```text
status
quality_tier
version
promotion metadata
```

---

## 9. AI 也是 Adapter，不是业务核心

AI 可以执行：

- 候选召回；
- 相似关系建议；
- Answer candidate 生成；
- Evidence discovery；
- 独立 reviewer；
- 内容缺陷建议。

AI 不可以成为系统唯一业务规则来源。

必须遵守：

```text
AI Suggestion
    ↓
Deterministic validation / explicit review
    ↓
Application apply
```

禁止：

```text
AI output -> 直接修改 canonical/answer/review 正式状态
```

Prompt/Skill 可以定义执行方法，但决定系统正确性的规则必须落在代码、配置 Schema 和确定性 gate 中。

---

## 10. Ports 与 Repository

Application 只能通过 Ports 访问存储和外部系统。

推荐：

```text
src/ports/repositories/
├── question-repository.js
├── canonical-repository.js
├── answer-repository.js
├── review-repository.js
└── evidence-repository.js
```

典型接口：

```text
findById(id)
findMany(filter)
save(record)
saveMany(records)
remove(id)
```

Repository 只负责持久化，不做业务判断。

例如：

```text
JSONL Repository
SQLite Repository
InMemory Repository
```

应实现相同 Port。

这样未来从 JSONL 切换 SQLite 时，不需要修改 Domain 与 Application。

---

## 11. Infrastructure Layer

Infrastructure 只实现技术细节：

```text
JSONL read/write
filesystem archive
GitHub issue API
AI client
SQLite
clock / filesystem lock
```

例如：

```text
src/infrastructure/jsonl/jsonl-canonical-repository.js
src/infrastructure/github/github-issue-adapter.js
src/infrastructure/ai/answer-writer-adapter.js
```

Infrastructure 不定义：

- 什么题应该合并；
- 什么答案算 curated；
- 什么 review 应该进入下一轮；
- 什么 priority 是 P0/P1/P2。

---

## 12. GitHub Actions 与未来 MCP

GitHub Actions、CLI、MCP 都属于 Interface / Adapter。

目标结构：

```text
CLI --------┐
Actions ----┼----> Application ----> Domain
MCP --------┘
```

因此未来开发 MCP 时：

- MCP 不复制 `canonical merge` 逻辑；
- MCP 不复制 `answer audit` 逻辑；
- MCP 不直接操作 JSONL；
- MCP 只负责 transport schema -> application DTO 的转换。

这样同一用例可以由 CLI、Actions、MCP 共享。

---

## 13. 架构硬规则

后续代码审查统一执行以下规则：

1. Command / Interface 不包含领域规则。
2. Domain 不允许依赖 `fs`、GitHub、CLI、数据库或 AI SDK。
3. Application 不直接解析 JSONL 或文件格式。
4. Repository 不做业务判断。
5. Detection 与 Mutation 必须分离。
6. AI Suggestion 与 Apply 必须分离。
7. Canonical Dedup 的检测、审核、执行必须分离。
8. Answer Audit 与 Promotion 必须分离。
9. 外部系统变化不得驱动 Domain 修改。
10. 新增功能优先复用 Application use case，不允许为 CLI/Actions/MCP 各写一份业务逻辑。
11. 单文件超过约 300-500 行时必须检查是否存在多职责；行数不是自动失败条件，但必须有明确责任边界说明。
12. 一个模块如果存在两个以上独立修改原因，应优先拆分。

---

## 14. 测试策略

### 14.1 Domain Test

纯内存、无 IO：

```text
canonical merge policy
priority policy
dedup relation
answer hard failures
quality score
review scheduling policy
```

要求：快、确定、可重复。

### 14.2 Application Test

使用 InMemory Repository：

```text
merge use case
split use case
promote answer use case
apply dedup decision
review mark use case
```

重点验证业务编排与副作用边界。

### 14.3 Adapter Contract Test

验证：

```text
JSONL Repository
GitHub adapter
filesystem archive
AI adapter schema
```

### 14.4 End-to-End

继续保留现有：

```bash
node --test
npm run ci:check
```

并确保旧 CLI 行为在迁移期间保持兼容。

---

## 15. 渐进迁移策略

禁止一次性重写全部 `scripts/`。

### Phase A：建立边界

1. 建立 `src/domain`、`src/application`、`src/ports`、`src/infrastructure`。
2. 不改变 CLI 用户接口。
3. 新逻辑不再进入大型 command 文件。

### Phase B：优先迁移 Canonical

优先原因：Canonical 是 Question、Answer、Review 的核心连接点。

顺序：

```text
priority policy
relation policy
merge policy
repository port
merge application use case
CLI delegation
```

每迁移一个 use case，立即补单元测试。

### Phase C：迁移 Dedup

将现有 tokenize / Jaccard / candidate relation 从 Canonical command 中移出，形成独立 detection pipeline。

### Phase D：迁移 Answer Quality

将：

```text
score
hard failure
evidence
type policy
promotion
```

分别拆分。

### Phase E：迁移 Review

拆分 review scheduler、review state transition 与 repository。

### Phase F：删除旧重复实现

只有当：

- 新 use case 已覆盖；
- CLI 行为兼容；
- 测试通过；
- CI 通过；

才删除旧实现。

---

## 16. 非目标

本轮架构重构明确不做：

- 为了分层而切换 SQLite；
- 增加 Web UI；
- 立即开发 MCP；
- 重写全部数据；
- 重做 9k+ Answer；
- 改变现有 Question / Canonical 数据语义；
- 为追求目录整齐进行无价值搬文件。

架构重构必须服务于降低耦合和提高可验证性，不以“目录变化数量”作为完成指标。

---

## 17. 验收标准

一个迁移后的模块必须同时满足：

### 17.1 SRP

可以明确回答：

> 这个模块唯一主要的修改原因是什么？

如果回答中出现多个独立原因，则继续拆分。

### 17.2 SoC

模块没有越层处理其他层职责。

### 17.3 Dependency

Domain 不依赖外部实现。

### 17.4 Testability

Domain 可无 IO 测试；Application 可使用 InMemory Port 测试。

### 17.5 Compatibility

现有 CLI 与 CI 行为保持兼容，除非有单独设计文档明确声明 breaking change。

---

## 18. 第一批建议改造对象

建议按以下顺序进入代码改造：

```text
1. scripts/commands/canonical.js
2. Canonical similarity / relation / priority policy
3. Canonical Repository Port
4. merge / split application use case
5. canonical CLI delegation
6. answer quality 拆分
7. audit / promote 分离
8. review application / domain 分离
```

第一阶段不要同时改所有 command。

优先把 `canonical.js` 做成示范模块，验证架构后再复制模式到 Answer 和 Review。

---

## 19. 最终目标

重构完成后，系统应该具备以下性质：

```text
换 CLI              -> Domain 不变
增加 MCP            -> Domain 不变
JSONL 换 SQLite     -> Domain 不变
换 AI 模型          -> Domain 不变
GitHub Issue 停用   -> 核心知识资产不变
修改复习算法        -> Canonical 不变
修改答案评分规则    -> Question Store 不变
```

最终标准不是“代码被拆成更多文件”，而是：

> 不同变化被限制在正确的边界内，核心业务规则可独立验证，任何新入口都复用同一套 Application + Domain。
