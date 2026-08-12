# 10 SoC / SRP 架构重构设计

> 目标：把关注点分离（Separation of Concerns, SoC）、单一职责原则（Single Responsibility Principle, SRP）、依赖倒置、单一事实源和一致性边界固化为 `xhs` 后续开发的架构硬约束。
>
> 本文只定义模块边界、依赖方向、迁移策略和验收标准，不在本次文档阶段修改业务代码。

---

## 1. 文档地位与适用范围

本文是 `xhs` 后续架构边界和依赖方向的最新规范。

与 `docs/refactor/03_technical_design.md` 的关系：

- `03_technical_design.md` 中的数据模型、JSONL -> SQLite 演进、索引、Question/Canonical/Answer/Review 主链路等未冲突内容继续有效；
- 如果两份文档在“代码分层、职责归属、依赖方向、Adapter/Port 边界”上冲突，以本文为准；
- 本文不重新定义 Question、CanonicalQuestion、Answer、ReviewProgress 的业务语义。

主链路保持：

```text
Question -> CanonicalQuestion -> Answer -> ReviewProgress
```

当前统一 CLI 入口保持兼容：

```bash
node scripts/xhs.js <command> [subcommand] [options]
```

---

## 2. 当前问题

当前 `scripts/commands/*.js` 已经混合多类职责：

- CLI 参数解析；
- Application 用例编排；
- Canonical 业务规则；
- 相似度与候选检测；
- JSONL / 文件读写；
- ReviewProgress 迁移；
- Answer 归档和失效；
- Index 重建；
- Report / stdout / stderr；
- 多文件状态修改。

例如 Canonical merge 当前会跨 Question、Canonical、Review、Session、Answer、Archive、Index、History 多个状态源执行副作用。如果中间失败，存在部分修改已经落盘而后续修改未完成的风险。

因此本轮重构的目标不是“把文件拆小”，而是建立：

```text
稳定责任边界
+ 单向依赖
+ 单一规则事实源
+ 明确 mutation 边界
+ 可独立测试的 Domain
+ 可复用的 Application use case
```

---

## 3. 核心原则

### 3.1 SoC：不同变化进入不同边界

```text
交互协议变化       -> Interface
用例执行顺序变化   -> Application
业务规则变化       -> Domain
持久化方式变化     -> Infrastructure Adapter
外部系统变化       -> Infrastructure Adapter
```

一个模块不应因为多个彼此独立的变化原因反复修改。

### 3.2 SRP：一个模块只有一个主要修改原因

统一判断问题：

> 这个模块唯一主要的修改原因是什么？

如果答案同时包括 CLI、业务规则、存储格式、GitHub API、Review 状态等多个独立原因，则必须重新划分边界。

SRP 不意味着“每个函数只能做一个微小动作”，而是一个模块只服务一个稳定责任。

### 3.3 Dependency Inversion：核心不依赖实现

编译期依赖方向固定为：

```text
Interfaces --------> Application --------> Domain
                         |
                         +-----------> Outbound Ports
                                          ^
                                          |
                                  Infrastructure
```

Composition Root 负责把具体 Adapter 注入 Application。

禁止：

```text
Domain -> JSONL
Domain -> fs
Domain -> GitHub
Domain -> AI SDK
Application -> new JsonlRepository(...)
```

### 3.4 单一事实源（SSOT）

同一个业务规则只能有一个权威来源。

推荐规则：

```text
config / schema      = 声明式规则与阈值的事实源
Domain evaluator     = 解释并执行规则
Skill / Prompt       = 执行指导
Docs                 = 人类可读说明
```

例如答案质量阈值已经由 `config/answer_quality.json` 定义，则 Domain 不得再硬编码另一套分值、晋级阈值或 hard failure 列表。

文档、Skill、Prompt 不得成为系统正确性的唯一依据。

### 3.5 Detection != Decision != Mutation

全仓统一：

```text
Detect != Decide != Apply
Audit != Promote
Suggestion != Mutation
```

任何检测器、评分器、AI suggestion 都不得直接修改正式业务状态。

---

## 4. 目标架构

```text
┌────────────────────────────────────────────┐
│ Interfaces                                 │
│ CLI / GitHub Actions / future MCP          │
├────────────────────────────────────────────┤
│ Application                                │
│ use cases / orchestration / mutation plan  │
├────────────────────────────────────────────┤
│ Domain                                     │
│ Question / Canonical / Dedup / Answer /    │
│ AnswerQuality / Review                     │
├────────────────────────────────────────────┤
│ Outbound Ports                             │
│ repositories / mutation store / clock /    │
│ evidence / external services               │
├────────────────────────────────────────────┤
│ Infrastructure                             │
│ JSONL / FS / GitHub / AI / future SQLite   │
└────────────────────────────────────────────┘

Composition Root
    -> 创建 Adapter
    -> 注入 Application
```

推荐渐进目录：

```text
src/
├── domain/
│   ├── question/
│   ├── canonical/
│   ├── dedup/
│   ├── answer/
│   ├── answer-quality/
│   ├── answer-type/
│   └── review/
│
├── application/
│   ├── canonical/
│   ├── dedup/
│   ├── answer/
│   └── review/
│
├── ports/
│   ├── repositories/
│   ├── mutation/
│   └── services/
│
├── infrastructure/
│   ├── jsonl/
│   ├── filesystem/
│   ├── github/
│   ├── ai/
│   └── sqlite/
│
├── interfaces/
│   ├── cli/
│   ├── github-actions/
│   └── mcp/
│
└── bootstrap/
    ├── create-application.js
    └── cli.js
```

迁移期间允许旧 `scripts/` 与 `src/` 并存，但新领域规则不得继续沉积到大型 `scripts/commands/*.js`。

---

## 5. Interface Layer

Interface 只负责：

```text
transport / argv 输入解析
语法级校验
构造 Application DTO
调用 use case
格式化输出
exit code / transport response
```

禁止：

- 决定 Canonical 是否可 merge；
- 计算业务 priority；
- 实现 Jaccard / embedding 相似规则；
- 直接读写 JSONL；
- 迁移 ReviewProgress；
- 决定 Answer 是否 curated；
- 直接组合多个 Repository 实现业务流程。

CLI 示例：

```js
async function runMergeCommand(argv, app) {
    const input = parseMergeArgs(argv);
    const result = await app.mergeCanonical(input);
    printResult(result);
    return 0;
}
```

CLI 参数变化不能驱动 Domain 修改。

---

## 6. Application Layer

Application 负责“完成一个用例的执行顺序和副作用边界”。

例如 `MergeCanonical`：

```text
load required state
        ↓
call Domain policies
        ↓
build MutationPlan
        ↓
validate complete plan
        ↓
commit through mutation port
        ↓
post validation
        ↓
return use-case result
```

Application 负责流程，但不定义：

- 什么关系算 same / alias；
- 什么 Canonical 可以合法 merge；
- priority 如何计算；
- 什么 Answer 算 curated；
- review level 如何演进。

禁止：

- 直接解析 JSONL；
- 直接操作 `fs`；
- 依赖 CLI argv；
- 依赖 GitHub payload；
- 创建具体 Infrastructure 实例；
- 将核心业务规则写成 Application 内部散落的 if/else。

---

## 7. Domain Layer

Domain 只描述业务概念、不变量和策略。

Domain 必须可使用纯内存对象测试，不依赖：

```text
fs
path
process.argv
console
JSONL path
SQLite
GitHub API
AI SDK
GitHub Actions
MCP transport
```

### 7.1 Canonical Domain ownership

Canonical 负责：

```text
Canonical entity invariants
merge legality
split legality
priority policy
aliases / bindings 的领域约束
Canonical mutation result
```

建议：

```text
src/domain/canonical/
├── canonical.js
├── merge-policy.js
├── split-policy.js
└── priority-policy.js
```

Canonical 不负责相似候选召回，也不负责 AI 推断两个题的关系。

### 7.2 Dedup Domain ownership

Dedup 负责：

```text
similarity signals
relation candidate
relation decision model
```

建议关系模型：

```text
same
alias
parent_child
followup
related
unrelated
```

建议：

```text
src/domain/dedup/
├── similarity.js
├── relation.js
└── decision.js
```

明确边界：

> Dedup 判断“两个知识项是什么关系”；Canonical 判断“基于已确认关系执行某种 Canonical mutation 是否合法”。

因此禁止：

```text
Dedup -> 直接 merge Canonical
Similarity score -> 自动修改 canonical_id
```

---

## 8. Canonical Dedup 流程

必须固定为：

```text
Detect
  ↓
Relation Candidate
  ↓
Review / Decide
  ↓
Explicit Decision
  ↓
Application Apply
  ↓
Canonical Merge/Split Policy
```

检测结果只是 evidence，不是 mutation authorization。

AI、Jaccard、Embedding 都只能参与 Detect / Suggest，不得直接 Apply。

---

## 9. Answer Quality 边界

答案质量包含多个独立关注点，禁止继续无限扩大单一 `answer_quality.js`。

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

题型规则独立：

```text
src/domain/answer-type/
├── concept-policy.js
├── mechanism-policy.js
├── scenario-policy.js
├── coding-policy.js
├── project-policy.js
└── behavior-policy.js
```

但规则值必须来自权威 config/schema，不得复制配置中的阈值和 hard failure 定义。

### 9.1 Audit 与 Promote 分离

```text
answer audit != answer promote
```

Audit 只能产生：

```text
PASS / FAIL
score
hard failures
findings
evidence status
```

Audit 不得修改正式 Answer。

Promote 是独立 Application use case，并在 mutation 前重新验证 promotion preconditions。

---

## 10. AI 是 Adapter

AI 可以参与：

- Candidate 召回；
- Relation 建议；
- Answer candidate 生成；
- Evidence discovery；
- 独立 review；
- 内容缺陷建议。

固定流程：

```text
AI Suggestion
    ↓
Deterministic validation / explicit review
    ↓
Application mutation
```

禁止：

```text
AI output -> 直接修改 Canonical / Answer / Review 正式状态
```

换模型不得驱动 Domain 修改。

---

## 11. Ports

Ports 是 Application 所需外部能力的抽象，不是基础设施实现。

不要强制所有 Repository 退化成通用 CRUD。

优先定义符合业务用例的窄接口，例如：

```text
CanonicalRepository
  get(id)
  getMany(ids)
  save(record)

QuestionBindingRepository
  findByCanonical(id)
  getByQuestionIds(ids)

ReviewRepository
  loadByCanonical(id)

CanonicalMutationStore
  preflight(plan)
  commit(plan)
```

Port 原则：

- 接口名称反映调用方需要的能力；
- 不暴露 JSONL 路径和文件格式；
- 不把业务判断放进 Repository；
- 不为了“像 ORM”而提供没有用例语义的通用接口。

---

## 12. 多文件 Mutation / 一致性边界

这是 Canonical merge/split 重构的 P0 设计要求。

### 12.1 问题

当前一个 merge 可能同时修改：

```text
questions.jsonl
canonical_questions.jsonl
review/progress.json
review/sessions/*.json
review/answers/*.md
review/archive/answers/*.md
indexes
merge history
```

如果采用“改一个文件 -> 再改下一个文件”的直接模式，中途失败会形成半完成状态。

### 12.2 目标模型

统一采用：

```text
Preflight
   ↓
Build MutationPlan
   ↓
Validate whole plan
   ↓
Stage
   ↓
Atomic Commit / Recoverable Commit
   ↓
Post Validate
   ↓
Audit History
```

`MutationPlan` 至少描述：

```text
expected current versions / hashes
records to update
files to write
files to archive
bindings to move
review migrations
answer invalidations
index rebuild requirements
history entry
```

### 12.3 JSONL / 文件阶段

在未迁移 SQLite 前，Infrastructure 必须提供等价的一致性方案，可选机制包括：

- temp file + atomic rename；
- repository-level lock；
- journal / recovery manifest；
- precondition hash；
- staged writes；
- failure recovery / idempotent retry。

具体机制由实现预研决定，但必须满足：

> 失败不能静默留下不可识别的半完成状态。

### 12.4 SQLite 阶段

未来 SQLite Adapter 可以用数据库 transaction 实现相同 Mutation Port；Application 和 Domain 不应因此修改。

---

## 13. Composition Root

只有 Composition Root 可以知道具体 Adapter 类型。

例如：

```js
const canonicalRepo = new JsonlCanonicalRepository(...);
const mutationStore = new FsCanonicalMutationStore(...);
const app = createApplication({
    canonicalRepo,
    mutationStore,
    clock,
});
```

建议：

```text
src/bootstrap/create-application.js
src/bootstrap/cli.js
```

禁止 Application 内部：

```js
new JsonlCanonicalRepository(...)
new GitHubClient(...)
```

这条规则用于保证依赖倒置不会在实现阶段被破坏。

---

## 14. GitHub Actions 与 future MCP

CLI、Actions、MCP 都是入口，不拥有业务逻辑。

```text
CLI --------┐
Actions ----┼----> Application ----> Domain
MCP --------┘
```

未来 MCP：

- 不复制 `canonical merge`；
- 不复制 `answer audit`；
- 不直接操作 JSONL；
- 不维护自己的业务状态机；
- 只做 transport schema <-> Application DTO 转换。

---

## 15. 架构硬规则

后续评审执行以下规则：

1. Interface 不包含领域规则。
2. Domain 不依赖 fs、数据库、GitHub、AI SDK、CLI 或 transport。
3. Application 不直接解析 JSONL/文件格式。
4. Application 不创建具体 Infrastructure。
5. Repository / Adapter 不定义业务规则。
6. Detection 与 Mutation 分离。
7. AI Suggestion 与 Apply 分离。
8. Dedup Detect / Decide / Apply 分离。
9. Answer Audit 与 Promote 分离。
10. 业务规则必须有单一事实源。
11. 跨多个状态源的 mutation 必须有显式一致性边界。
12. 外部系统变化不得驱动 Domain 修改。
13. CLI / Actions / MCP 必须复用同一 Application use case。
14. 单文件超过约 300-500 行时必须检查是否存在多职责；行数不是自动失败条件。
15. 一个模块存在两个以上独立修改原因时，优先重新划分边界。

---

## 16. 测试策略

### 16.1 Phase 0：Characterization Tests

在移动任何生产逻辑之前，先冻结当前外部行为。

优先覆盖：

```text
canonical accept
canonical merge
canonical split
canonical check
canonical stats
```

Characterization Test 应记录：

- 输入参数；
- stdout / exit code；
- 修改文件集合；
- Question/Canonical binding 结果；
- Review migration；
- Answer archive / invalidation；
- Index / history 变化；
- error behavior。

增加 failure injection 用例，例如：

```text
archive 已存在
review 状态异常
写文件失败
post-check 失败
重复 binding
```

目标不是证明旧实现完美，而是明确迁移前真实行为和已知缺陷。

### 16.2 Domain Tests

纯内存、无 IO：

```text
merge policy
split policy
priority policy
dedup relation
answer hard failures
quality score
review state policy
```

### 16.3 Application Tests

使用 InMemory Port：

```text
merge use case
split use case
apply dedup decision
promote answer
review mark
mutation plan build
```

### 16.4 Adapter Contract Tests

```text
JSONL repository
filesystem mutation store
GitHub adapter
AI adapter schema
future SQLite adapter
```

相同 Port 的不同 Adapter 必须通过相同 contract tests。

### 16.5 End-to-End

继续保持：

```bash
node --test
npm run ci:check
```

迁移期间旧 CLI 必须保持兼容，除非另有 breaking-change 设计。

---

## 17. 渐进迁移策略

禁止一次性重写全部 `scripts/`。

### Phase 0：冻结现有行为

1. 为 Canonical 核心命令补 Characterization Tests。
2. 记录已知不一致和失败模式。
3. 不做目录搬迁式重构。

退出条件：迁移前行为有可重复证据。

### Phase A：建立架构骨架

1. 建立 `src/domain`、`src/application`、`src/ports`、`src/infrastructure`、`src/bootstrap`。
2. 建立 Composition Root。
3. CLI 用户接口不变。
4. 新领域规则不再进入大型 command 文件。

### Phase B：抽取纯 Canonical Domain

顺序：

```text
priority policy
merge policy
split policy
Canonical invariants
```

只抽纯规则，不立即改变持久化流程。

### Phase C：建立 Port 与 Mutation Boundary

1. 建立窄 Repository Ports。
2. 设计 `CanonicalMutationStore` / Unit of Work。
3. 为文件模式实现 preflight/stage/commit/recovery。
4. 补 failure-injection tests。

这是开始替换现有 merge 写路径前的强制门槛。

### Phase D：迁移 Canonical Application

逐个迁移：

```text
merge
split
accept
check
stats
```

每迁移一个用例：

```text
characterization test green
+ domain/application tests green
+ CLI compatibility green
```

然后删除该用例在旧 command 中的重复业务逻辑。

### Phase E：迁移 Dedup

把 tokenize / Jaccard / candidate detection 从 Canonical command 移出。

明确：

```text
Dedup decision -> Application apply -> Canonical mutation
```

### Phase F：迁移 Answer Quality

拆分：

```text
score
hard failures
evidence
type-specific policy
audit
promotion
```

同时保持 `config/answer_quality.json` 为规则事实源。

### Phase G：迁移 Review

拆分：

```text
review scheduling policy
review state transition
review application
review repository
```

### Phase H：清理旧实现

只有满足：

- 新 use case 完整覆盖；
- CLI 行为兼容；
- mutation failure 可恢复；
- tests 通过；
- CI 通过；

才能删除旧实现。

---

## 18. 非目标

本轮架构重构明确不做：

- 为了分层而立即切 SQLite；
- 增加 Web UI；
- 立即开发 MCP；
- 重写全部数据；
- 重做 9k+ Answer；
- 改变 Question / Canonical 业务语义；
- 仅为了目录整齐而搬文件；
- 为实现“纯架构”引入没有现实用例的抽象层。

架构重构只以降低耦合、提高一致性和可验证性为目标。

---

## 19. 验收标准

### 19.1 SRP

每个模块可以明确回答：

> 唯一主要修改原因是什么？

### 19.2 SoC

模块不跨层处理其他关注点。

### 19.3 Dependency

Domain 不依赖外部实现；Application 只依赖 Domain 与 Ports。

### 19.4 SSOT

相同规则没有在 config、Domain、Skill、Prompt 中出现互相独立的实现。

### 19.5 Testability

Domain 无 IO 可测；Application 可用 InMemory Port 测试。

### 19.6 Mutation Safety

跨文件/跨状态源操作满足：

```text
preflight
+ complete mutation plan
+ recoverable/atomic commit
+ post validation
```

失败不会留下无法识别的半完成状态。

### 19.7 Compatibility

现有 CLI / CI 行为保持兼容，除非有单独 breaking-change 设计。

### 19.8 Replaceability

达到以下目标：

```text
换 CLI              -> Domain 不变
增加 MCP            -> Domain 不变
JSONL 换 SQLite     -> Domain / Application 不变
换 AI 模型          -> Domain 不变
GitHub Issue 停用   -> 核心知识资产不变
修改复习算法        -> Canonical 不变
修改答案评分规则    -> Question Store 不变
```

---

## 20. 第一批执行对象

第一批不直接“拆完整个 canonical.js”，而采用纵向切片：

```text
0. Canonical characterization tests
1. priority policy
2. merge/split Domain policy
3. Canonical Repository Port
4. Canonical MutationPlan / MutationStore
5. merge Application use case
6. merge CLI delegation
7. failure-injection + compatibility validation
8. 再迁移 split
```

只有 merge 纵向切片验证成功后，才复制模式到 accept、Dedup、Answer、Review。

---

## 21. 最终标准

重构成功的标准不是“产生了更多目录和类”，而是：

> 不同变化被限制在正确边界内，业务规则只有一个事实源，核心 Domain 可独立验证，跨状态 mutation 可恢复，任何新入口都复用同一 Application + Domain。
