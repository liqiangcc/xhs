# 08 内容建设阶段目标

> 本文是当前内容建设路线的执行依据。目标不是继续堆积原始题目，而是把高频题稳定转化为可口述、可追问、可复习、可迭代的知识资产。

---

## 1. 建设定位

当前工程底座已经具备 `Question -> CanonicalQuestion -> Answer -> ReviewProgress` 主链路。接下来的主任务是内容建设，固定选择如下：

```text
建设顺序：高频主干优先
答案形态：中高级 Java 后端社招口述 + 连续追问
知识资产单位：CanonicalQuestion
答案绑定单位：canonical_id
复习状态单位：canonical_id
最终覆盖：所有真实面试题都必须可查询、可查看答案、可进入复习
质量优先级：在保证最终全覆盖的前提下，先建设高价值内容
```

安全治理、仓库体积、Web UI 和复杂自动化不进入本路线的主里程碑；它们不得挤占内容建设批次。高频优先只决定建设顺序，不缩小最终范围。

---

## 2. 当前基线

基线日期：2026-07-10。

| 指标 | 当前值 | 说明 |
|---|---:|---|
| Question rows | 9,620 | 原始题目行 |
| Valid question rows | 9,362 | 当前标记为可进入题库的题目行，数字仍会因无效题复核而增加 |
| Canonical questions | 34 | 已确认知识资产 |
| Assigned question rows | 134 | 已绑定 Canonical 的题目行，占有效题约 1.43% |
| Ready answers | 34 | 当前 Canonical 均有结构完整答案 |
| P0 / P1 | 12 / 22 | 当前高价值批次 |
| Review progress records | 34 | 已初始化复习状态 |
| Reviewed canonical | 0 | 尚无真实 `review mark` |
| Unassigned exact hotspots | 211 | 尚未进入 Canonical 的重复题热点 |

基线结论：原始题量已经足够，瓶颈是归一化覆盖、答案口述质量和真实复习反馈，不是继续采集。最终需要重新审计全部 9,620 条 Question：所有真实面试题都进入 Canonical 并可复习，只有信息残缺到无法还原问题或确属提取噪声的记录才允许排除。当前 258 条无效题中仍包含项目、行为、HR、场景和智力题等真实问题，不能直接当作最终排除集合。

---

## 3. 全程不变的内容原则

### 3.1 先归入已有题簇，再创建新题簇

每个候选必须先检查已有 Canonical：

1. 比较规范化标题和 aliases。
2. 比较 `primary_domain` 与核心技术实体。
3. 判断是同义问法、同一主问题的追问，还是边界独立的新问题。
4. 同义题绑定已有 `canonical_id`；边界独立时才新建。

例如已有“TCP 和 UDP 的区别”时，新的“TCP 与 UDP 有什么不同”应优先补充到已有题簇，而不是创建第二份答案。

### 3.2 每批都完成闭环，不积累内容债

从 C2 阶段开始，每个批次固定完成：

```text
候选召回
  -> 去重与边界确认
  -> canonical accept / merge / split
  -> 编写或升级答案
  -> answer validate --strict
  -> answer sync
  -> canonical check
  -> 加入复习队列
```

不得只增加 Canonical 而长期保留 missing answer，也不得批量生成答案后跳过内容复核。

### 3.3 高频不等于只看重复次数

候选排序依次考虑：

1. 跨公司重复度。
2. 题目出现频次。
3. 社招、中高级岗位命中情况。
4. 是否属于 Java 后端核心实体。
5. 当前内容地图是否存在明显缺口。

算法题只补真实高频和目标公司需要的题，避免算法题继续挤占 Java、数据库、中间件和系统设计的建设额度。

### 3.4 不虚构项目经历

答案可以给出“项目映射提示”“指标清单”“可讲的决策点”，但不得替用户编造已经做过的项目、事故或优化结果。项目经验必须由真实经历补全。

### 3.5 高频优先，但长尾必须收口

内容按价值分层推进，但没有“长尾题永久不处理”的选项：

```text
Tier A：跨公司高频主干，最先建设
Tier B：核心专题必备题，补齐知识网络
Tier C：低频但有效的长尾题，逐条归一化并提供答案
Tier D：无效、重复噪声或非面试问题，记录排除原因
```

最终每条 Question 必须满足且只能满足一种结果：

1. 是真实、可还原的面试问题：`is_valid_for_library=true`，绑定一个 `canonical_id`，并能获得答案和复习入口。
2. 不是完整问题或属于提取噪声：`is_valid_for_library=false`，且有可解释的排除原因。

有效长尾题即使只有一次出现，只要语义独立，也应建立或归入 Canonical，不能为了提高聚合率强行合并。

---

## 4. 单个知识资产的完成定义

一个 Canonical 只有同时满足下列条件，才算内容建设完成：

### 4.1 Canonical 完成条件

- 标题可直接作为面试问题，语义边界单一。
- 已检查现有 Canonical，不存在已知重复题簇。
- aliases 覆盖当前确认的主要问法，但不混入独立子问题。
- `primary_domain`、`primary_entities`、公司和频次与原题一致。
- 所有关联 Question 的 `canonical_id` 一致。

### 4.2 社招答案完成条件

- `核心结论` 能在 20–30 秒内说清本质。
- `1 分钟版` 有明确主干，不是定义堆砌。
- `3 分钟版` 包含原理、取舍、场景和边界。
- `关键细节` 与 `原理机制` 不重复抄写。
- `项目经验版` 使用真实经验或项目映射提示，不使用虚构口吻。
- 至少 3 个高频追问，每个追问都带可口述短答。
- 易错点包含面试中容易说反、说绝对或遗漏的内容。
- 版本敏感结论注明适用版本或核对日期。
- 通过 `answer validate --strict` 并同步到 Canonical 状态。

### 4.3 分题型附加条件

| 类型 | 附加完成条件 |
|---|---|
| 概念/对比 | 讲清比较维度、选择条件和反例 |
| 原理/源码 | 讲清核心数据结构、主流程、关键版本差异和性能边界 |
| 场景/系统设计 | 包含需求假设、容量、核心链路、一致性、故障与降级、观测指标 |
| 算法 | 包含不变量、Java 实现、复杂度、边界用例和至少一个变体 |
| 项目深挖 | 包含背景、个人职责、关键决策、指标、取舍、故障或复盘 |
| 行为题 | 使用真实 STAR 证据，结果可量化，不写空泛价值观 |

---

## 5. 阶段总览

| 阶段 | 名称 | 核心结果 | 主要量化目标 |
|---|---|---|---|
| C0 | 标准与基线冻结 | 全仓使用同一套内容完成定义 | 路线、模板、内容地图和指标口径确定 |
| C1 | 现有资产校准 | 34 个现有 Canonical 边界清晰、答案可信 | 12 个 P0 完成人工内容审查 |
| C2 | 高频主干成型 | 第一批可稳定复习的 Java 后端主干 | Canonical >= 60，assigned rows >= 200 |
| C3 | 社招答案升级 | 答案从统一摘要升级为分题型口述材料 | C2 范围内 P0/P1 均满足内容 DoD |
| C4 | 真实复习试跑 | 用真实作答验证答案与调度是否有效 | >= 5 个 Canonical、>= 10 次 review mark |
| C5 | 核心专题成网 | 高频点形成专题知识地图，而非孤立卡片 | Canonical >= 100，assigned rows >= 300 |
| C6 | 规模化复习资产 | 支持专题突破、综合复习和目标公司组题 | Canonical >= 200，assigned rows >= 600 |
| C7 | 全量题目归一化 | 复核全部原始题，所有真实问题都有 Canonical | 真实题 assigned=100%，噪声 reason=100% |
| C8 | 全量答案覆盖 | 所有 Canonical 都有合格可复习答案 | 全部 Canonical missing answer=0 |
| C9 | 全量可复习性验证 | 任意真实原题都能到达答案和复习状态 | 原题到 ReviewProgress 的可达率=100% |
| C10 | 持续经营 | 内容按新增面经和复习反馈滚动更新 | 每周有闭环批次，全量覆盖不回退 |

阶段数字是中间退出门槛，不是最终范围，也不是为了凑数。若达到数量但存在重复题簇、空泛答案或没有复习价值，不得进入下一阶段；最终完成以 C7/C8 的全量内容覆盖和 C9 的全量可复习性验证为准。

---

## 6. C0：标准与基线冻结

### 目标

建立统一内容口径，让后续 Agent、脚本和人工审查对“什么算完成”没有歧义。

### 主要产物

- 本内容建设阶段目标文档。
- 高频实体与专题内容地图。
- Canonical 候选批次清单。
- 分题型答案模板及审查清单。
- 质量报告中的内容覆盖指标定义。

### 退出条件

- 明确高频主干优先、社招口述优先。
- 明确 Canonical 与 Answer 的完成定义。
- 明确 C1–C10 的量化门槛和顺序。
- 新增内容不再引用相互冲突的历史目标。

### 非目标

- 不在本阶段追求新增题量。
- 不先实现 Web UI、数据库或复杂自动生成器。

---

## 7. C1：现有 34 个资产校准

### 目标

先把已有内容变成可信样板，避免带着重复边界和通用模板继续扩量。

### 主要任务

1. 审查 34 个 Canonical 的标题、aliases 和题目边界。
2. 将未绑定但明显同义的热点优先吸收到现有 Canonical。
3. 修正领域或题型明显不一致的记录。
4. 优先人工审查 12 个 P0 答案的事实、口述节奏和追问质量。
5. 将泛化的“项目经验版”改成真实经验或项目映射提示。
6. 为算法、场景和原理题标记后续应使用的答案类型。

### 退出条件

- `canonical check` 通过且没有已知重复 Canonical。
- 34 个答案继续通过严格校验。
- 12 个 P0 答案满足本文的社招答案完成条件。
- 已形成一批可供 C2 复用的合格样板。

---

## 8. C2：高频主干成型

### 目标

以 10 个知识资产为一个批次，把最常见的 Java 后端问题转化为第一套可持续复习主干。

### 首轮约 40 个候选的建设额度

| 方向 | 候选额度 | 重点 |
|---|---:|---|
| Java 集合/JVM/并发 | 10 | HashMap、线程池、synchronized/volatile、AQS、ThreadLocal、GC、类加载 |
| MySQL/数据库 | 8 | B+ 树、事务、隔离级别、MVCC、锁、日志、SQL 优化 |
| Redis/缓存 | 5 | 数据结构、过期淘汰、高可用、缓存风险、分布式锁、big/hot key |
| Spring | 4 | IoC、Bean、AOP、事务、循环依赖、MVC |
| Kafka/RocketMQ | 4 | 可靠性、顺序、幂等、重复消费、积压、事务消息 |
| 网络/操作系统 | 4 | TCP、HTTP、IO 多路复用、进程线程、IPC |
| 系统设计 | 3 | 高并发、幂等、一致性、限流降级、排障 |
| 算法 | 2 | 只选真实高频或目标公司必需题 |

额度用于控制内容结构，不要求每个候选都新建 Canonical；若命中已有 Canonical，应增加绑定而不是凑新记录数。

### 每批退出条件

- 完成候选去重和边界确认。
- 新增或扩展 Canonical 后立即补齐答案。
- `answer validate --strict`、`answer sync`、`canonical check` 全部通过。
- 本批没有遗留 missing answer。
- 更新覆盖统计后再开始下一批。

### 退出条件

- Canonical >= 60。
- Assigned question rows >= 200。
- 所有 P0/P1 Canonical 均有 ready 答案。
- Java、数据库、Redis、Spring、消息队列不存在完全空白的核心子方向。

---

## 9. C3：社招答案升级

### 目标

把“八段式完整答案”升级为真正能在面试现场表达并扛住追问的内容。

### 主要任务

1. 先升级 P0，再升级 P1。
2. 概念题补齐比较维度、选择条件和边界。
3. 原理题补齐主流程、数据结构、复杂度和版本差异。
4. 场景题补齐容量假设、失败链路、降级和观测指标。
5. 算法题补齐 Java 代码、边界用例和变体。
6. “常见追问”统一改为问题加短答。
7. 对版本敏感知识保留核对依据，过期时标记 `needs_update`。

### 退出条件

- C2 范围内所有 P0/P1 答案满足内容 DoD。
- 每份答案至少有 3 个带短答的追问。
- 算法答案全部有可运行思路和 Java 实现。
- 场景答案不再只有组件罗列，必须包含取舍与失败处理。
- 项目表达不存在未经用户确认的虚构经历。

---

## 10. C4：真实复习试跑

### 目标

用真实回答检验内容，而不是只依赖答案文件和结构校验判断质量。

### 试跑范围

- 至少选择 5 个不同类型的 Canonical：概念、原理、场景、算法、排障各 1 个。
- 至少记录 10 次 `review mark`。
- 每次记录回答缺失点、危险表述、追问失守点和下一次复述骨架。

### 反馈规则

- 多次答不出的要点进入答案的“易错点”或“追问短答”。
- 答案太长而无法复述时，压缩 1 分钟版。
- 追问与主问题边界不同且重复出现时，升级为独立 Canonical 候选。
- 答案存在事实或版本问题时标记 `needs_update`，修复后再进入复习。

### 退出条件

- Reviewed canonical >= 5。
- Review marks >= 10。
- 至少完成一轮“复习反馈 -> 答案修改 -> 再复习”。
- 证明当前模板能支持 1 分钟表达和连续追问。

---

## 11. C5：核心专题成网

### 目标

从孤立高频卡片升级为专题知识地图，能够沿一个实体连续复习主问题、原理、场景和追问。

### 必建专题

```text
Java 集合与语言基础
Java 并发与 JUC
JVM
MySQL
Redis
Spring
Kafka / RocketMQ
计算机网络与操作系统
高并发与分布式系统设计
线上排障与性能优化
```

每个专题至少定义：

- 必读主干题。
- 原理题。
- 场景题。
- 高频追问。
- 已有 Canonical。
- 待建设缺口。
- 用户 weak 项。

### 退出条件

- Canonical >= 100。
- Assigned question rows >= 300。
- 十个必建专题均有可执行题单，不存在只有一张孤立卡片的专题。
- 必读主干题至少 80% 具备 ready 答案。
- 复习反馈能够定位到专题缺口和 weak 项。

---

## 12. C6：规模化复习资产

### 目标

在不复制答案的前提下，用同一批 Canonical 组合出多种复习入口。

### 目标能力

- 专题突破：按 Redis、MySQL、JVM 等连续训练。
- 综合复习：按 P0/P1 和到期时间训练。
- 公司模拟：按公司、岗位、轮次组合原题，但答案仍复用 Canonical。
- 弱项回炉：按历史失分和追问失守点重新组题。
- 快速复述：只展示结论骨架、上次错因和一个追问。

### 退出条件

- Canonical >= 200。
- Assigned question rows >= 600。
- P0/P1 missing answer = 0。
- 专题、公司和 weak 三种复习入口都能生成题单。
- 同义原题不会因为不同复习入口产生重复答案。
- 至少一个完整专题经历过多轮复习并形成 weak -> learning -> mastered 记录。

---

## 13. C7：全量题目归一化

### 目标

完成 Question 层到 Canonical 层的全量收口，使每条原始题都有明确、可审计的内容归宿，并把当前误标为无效的真实问题恢复为可复习内容。

### 覆盖范围

```text
全部 Question rows：9,620
当前有效题：9,362
必须重新人工/语义审计的当前无效题：258
最终真实题数量：审计完成后确定，必须全部绑定 Canonical
```

数据增长后以实时质量报告为准，百分比要求不变。

### 推进方式

1. 先逐条复核当前 258 条无效题；项目题、行为题、HR 题、智力题和场景题只要问题完整，都恢复为有效题。
2. 按归一化领域和核心实体切分全量队列，避免一次处理全库。
3. 每个队列先匹配已有 Canonical，再处理无法匹配的 singleton 和长尾题。
4. 对低频但语义独立的问题建立独立 Canonical，不以频次作为有效性标准。
5. 对过大 Canonical 执行 split，对重复 Canonical 执行 merge。
6. 只有非问题文本、无法还原具体题意的残片和提取噪声可以排除，并记录原因。
7. 每批完成后重新计算未绑定真实题和未解释排除记录数量。

### 数据契约

Question 数据需要补充可审计的排除信息：

```text
exclusion_reason: null | not_a_question | incomplete_or_unreadable | extraction_noise | other
exclusion_note: 可选说明；exclusion_reason=other 时必填
```

- 技术题、项目题、行为题、HR 题、智力题和完整场景题都属于可复习问题，不能使用“非技术”作为排除理由。
- 有效题的 `exclusion_reason` 必须为 `null`，并且必须有 `canonical_id`。
- 无效题的 `canonical_id` 必须为 `null`，并且必须有 `exclusion_reason`。
- 内容相同或相似不是排除理由；重复问法应绑定同一个 Canonical。
- Schema、迁移、质量报告和测试必须同时支持该字段，不能只在临时报告中维护。

### 全量覆盖指标

```text
reviewable_assigned_rate = assigned reviewable rows / all reviewable rows
invalid_reason_rate = invalid rows with exclusion reason / all invalid rows
unassigned_reviewable_count
unexplained_invalid_count
orphan_binding_count
duplicate_canonical_count
```

### 退出条件

- 当前 258 条无效记录已全部复核，所有真实问题均恢复为有效题。
- `reviewable_assigned_rate = 100%`。
- `invalid_reason_rate = 100%`。
- `unassigned_reviewable_count = 0`。
- `unexplained_invalid_count = 0`。
- 每条有效 Question 只绑定一个 Canonical。
- `canonical check` 通过且没有已知重复或孤儿绑定。
- 全量覆盖报告可重复生成，新增数据会明确重新打开覆盖缺口。

---

## 14. C8：全量答案覆盖

### 目标

让 C7 形成的每个 Canonical 都拥有可以进入复习系统的答案，不留下永久 missing 的低频题。

### 推进顺序

1. P0/P1 继续使用完整社招口述标准，优先人工复核。
2. P2/P3 按专题批量建设，但仍必须满足对应题型的内容 DoD。
3. 对事实边界不确定的答案保留 `draft` 或 `needs_update`，不得伪装成 ready。
4. 每批先完成生成和事实检查，再统一严格校验与同步。
5. 长尾答案可以更紧凑，但不能缺少结论、原理、边界和追问短答。

### 退出条件

- 全部 Canonical 都存在答案文件。
- 全部答案通过对应题型的严格校验并达到 `ready`；确需继续研究的少量内容必须有明确 `needs_update` 计划，清零后才算最终完成。
- 全部 Canonical 的 `answer_status` 与答案文件一致。
- 全库 `missing answer = 0`、`draft = 0`、`needs_update = 0`。
- 算法、场景、原理、项目和行为题分别满足其附加完成条件。
- 任意有效 Question 都能通过 `canonical_id` 找到唯一可复习答案。

---

## 15. C9：全量可复习性验证

### 目标

从用户视角证明所有真实面试题都已经可以复习，而不是只证明数据文件存在。

### 必须可达的完整链路

```text
任意原始 Question
  -> 唯一 CanonicalQuestion
  -> 唯一 ready Answer
  -> ReviewProgress
  -> query / topic / company / review today 中至少一个可发现入口
```

### 验证能力

- 增加全量 reviewability 检查，逐条遍历所有 `is_valid_for_library=true` 的 Question。
- 验证 Canonical 存在且绑定一致。
- 验证答案文件存在、状态为 ready、严格校验通过。
- 验证 ReviewProgress 已初始化且未被意外 archived。
- 验证原题可以通过 question_id 查询，并能追溯到复习卡。
- 验证专题与公司筛选不会让孤立长尾题永久不可发现。
- 输出不可复习题清单；清单非空时整体失败。

### 全量可复习指标

```text
reviewable_question_count
reviewable_question_ready_count
reviewable_question_progress_count
unreachable_question_count
reviewability_rate = reviewable_question_ready_count / reviewable_question_count
```

### 退出条件

- `reviewability_rate = 100%`。
- `unreachable_question_count = 0`。
- 任意抽样或指定 `question_id` 都能返回 Canonical、ready 答案路径和复习状态。
- 全量检查能够在新增题目后发现并阻断覆盖回退。
- “所有题目可以复习”由自动报告证明，不依赖人工抽样推断。

---

## 16. C10：持续经营

### 目标

把内容建设变成稳定节奏，让新增面经和复习反馈持续改善已有知识资产。

### 固定节奏

#### 每周

1. 查看质量报告和新增热点。
2. 处理一个不超过 10 个知识资产的闭环批次。
3. 补齐本批答案并通过严格校验。
4. 完成到期复习并处理 weak 项。
5. 记录本周新增、合并、更新和验证结果。

#### 每月

1. 检查高频实体内容地图缺口。
2. 检查重复 Canonical 和边界过大的题簇。
3. 检查版本敏感答案和 `needs_update`。
4. 分析真实复习数据，调整下一月批次优先级。
5. 只在目标公司明确时更新公司模拟题单。

### 稳态指标

```text
canonical check: 通过
reviewable_assigned_rate: 100%
invalid_reason_rate: 100%
all canonical missing answer: 0
reviewability_rate: 100%
unreachable_question_count: 0
新增批次未闭环数量: 0
reviewed_count: 持续增长
weak 项: 有明确下一次复习日期
needs_update: 有负责人或下一批处理计划
```

### 退出条件

C10 没有一次性完成点。连续四周保持每周闭环、全量可复习率不回退、没有新增内容债，并能用复习反馈决定下一批内容时，视为进入稳定运营。

---

## 17. 阶段状态与推进规则

当前状态：

| 阶段 | 状态 | 当前判断 |
|---|---|---|
| C0 | DONE | 路线、机器可读策略、内容盘点、候选队列和分题型标准均已落盘 |
| C1 | DONE | 34 个资产边界与类型已校准，吸收 8 组同义题，原始 12 个 P0 答案已完成人工内容审查 |
| C2 | DONE | 已达到 60 个 Canonical、208 条 assigned rows；全部 60 份答案 ready 且复习进度已初始化 |
| C3 | DONE | C2 范围内 20 个 P0、16 个 P1 均达到分题型社招内容 DoD；7 道算法题全部含 Java 实现 |
| C4 | DONE | 已完成概念、原理、场景、算法、排障各 1 题的两轮受控复述，共 10 次 mark；5 个缺口已回写答案 |
| C5 | DONE | 已达到 100 个 Canonical、328 条 assigned rows、100 份 ready 答案，并形成 10 条专题学习路径 |
| C6 | IN_PROGRESS | 需扩展到 200 个 Canonical / 600 assigned rows，并验证专题、公司和综合复习入口 |
| C7 | TODO | 尚未复核 258 条无效记录，也未实现全部真实题 100% Canonical 绑定 |
| C8 | TODO | 尚未实现所有 Canonical 的答案全覆盖 |
| C9 | TODO | 尚无逐题全链路 reviewability 验证，无法证明所有题都可复习 |
| C10 | TODO | 尚未形成连续四周且全量可复习率不回退的稳定节奏 |

推进规则：

1. C1、C2、C3 可以小范围交错，但每个 10 题批次必须完整闭环。
2. C4 必须在大规模扩到 100 个 Canonical 之前完成，以真实反馈校准模板。
3. C5 完成后才能以公司模拟和规模化组题为主推进 C6。
4. C6 只是规模化能力验证，不能替代 C7/C8 的全量覆盖和 C9 的可复习性证明。
5. C9 通过后才可以宣称“所有题目都可以复习”。
6. 任一阶段出现重复 Canonical、missing answer、不可达题目或严格校验失败，先清债再扩量。

---

## 18. 每批验证命令

```bash
node scripts/xhs.js canonical check --noWrite
node scripts/xhs.js answer validate --strict --noWrite
node scripts/xhs.js index build --check --noWrite
node scripts/xhs.js report quality --noWrite --noFail
node scripts/xhs.js review today --limit 10 --noWrite
npm test
```

需要写入状态时再显式执行：

```bash
node scripts/xhs.js answer sync
node scripts/xhs.js review mark --canonical-id <cq_id> --result <again|hard|good|easy> --notes "<复习反馈>"
```

每批交付记录至少说明：新增或扩展了哪些 Canonical、合并了哪些同义题、补了哪些答案、验证结果、复习反馈和下一批缺口。
