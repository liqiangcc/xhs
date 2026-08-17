<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_message_exactly_once_4aede2ce","version":2,"status":"draft","updated_at":"2026-08-17","answer_type":"scenario","quality_tier":"candidate"} -->
# 消息如何做到业务上的 Exactly Once？

## 核心结论

业务上的 Exactly Once 不能只靠 MQ 的“恰好一次”开关。可靠做法是把“消息是否处理过、业务状态变更、待发送的下游事件”放进同一个本地数据库事务，用 `event_id` 唯一约束做幂等；事务提交后再提交消费位点。下游发送通过 outbox 重试，并保持同一个事件 ID，让下游同样幂等。这样重复投递、消费者宕机和发送结果不确定都只会重复尝试，不会重复产生业务效果。

## 1 分钟版

先给设计假设：峰值 2 万消息/s，单条业务处理目标 P99 小于 500ms，允许至少一次投递，但要求同一个 `event_id` 最多产生一次业务状态变更；这些数值是设计输入，必须通过压测验证。

消费事务里做三件事：`INSERT processed_event(event_id)`、更新业务表、`INSERT outbox(event_id,payload,status)`。`event_id` 唯一约束保证重复消息第二次进入时直接识别为已处理。事务提交后再提交 Kafka offset；如果提交 offset 前进程崩溃，消息会再投，但数据库幂等把它变成 no-op。

outbox relay 独立发送下游事件。网络超时意味着“发送结果未知”，不能换一个新 event_id 重发；必须用同一 ID 重试，下游也要有去重键。Kafka producer idempotence/transaction 能减少传输层重复，但不能替代外部数据库和下游系统的业务幂等。

## 3 分钟版

### 需求与不变量

假设每条消息都有稳定 `event_id`，业务要求“同一 event_id 最多改变一次本地业务状态”，失败允许重试。核心表可以是：

`processed_event(event_id PK, processed_at)`
`business_state(...)`
`outbox(event_id PK, payload, status, retry_count, next_retry_at)`

三者由同一个数据库事务保护。

### 消费状态机

消费者收到消息后开启事务。先插入 `processed_event`；若唯一键冲突，说明该 event_id 已成功提交过，直接结束本次业务处理。首次处理则更新业务表并写 outbox，随后一起提交。数据库事务成功后再提交 Kafka offset。

关键故障是“数据库已提交但 offset 未提交”：重启后 Kafka 会再次投递，但 `processed_event` 已存在，所以不会第二次修改业务状态。相反，如果数据库事务回滚，则没有去重记录、没有业务修改、没有 outbox，下一次投递可以安全重试。

### 下游发送

outbox relay 只读取已提交记录。每次发送都携带原 `event_id`。如果请求超时，relay 不能知道下游是否已经成功，因此保持同一 ID 重试；下游若要求同样的业务 Exactly Once，也必须以该 ID 做唯一约束或幂等记录。成功确认后把 outbox 标记为 sent。长期失败进入退避、告警和人工补偿，而不是静默删除。

### Kafka 边界

Kafka `enable.idempotence` 解决 producer retry 造成的 Kafka 内部重复；`transactional.id` 与 `read_committed` 可以在 Kafka 记录/消费位点范围内提供事务语义。但一旦业务状态在外部数据库，正确性边界就跨出了 Kafka，仍需要数据库事务、唯一约束和下游幂等协作。

### 运维与验收

监控消费延迟、去重命中率、数据库事务失败、outbox backlog/最大年龄、relay 重试、下游幂等冲突和 DLQ。压测至少覆盖重复投递、事务提交后 offset 提交前宕机、relay 发送后响应丢失、下游超时和数据库故障。验收不是“消息只收到一次”，而是相同 event_id 在这些故障下仍只有一个业务结果和一个稳定 outbox 身份。

## 关键细节

- `processed_event`、业务修改、outbox 必须在同一个本地事务；分两次提交会留下“业务成功但没有事件”或“有去重记录但业务没成功”的缝隙。
- offset 只能在本地事务提交后推进；否则可能先确认消息、后丢业务结果。
- outbox 重试不能生成新的 event_id；“发送结果未知”必须保持同一幂等身份。
- Kafka transport 的 EOS 不能自动覆盖 MySQL、HTTP 下游等外部系统。
- 删除历史去重记录前必须明确消息最大重投窗口和审计要求，否则旧消息可能重新产生业务效果。

## 原理机制

本地不变量是：

`processed_event(event_id) 存在 ⇔ 该 event_id 的业务事务已经提交`

并且该事务同时生成唯一 outbox 记录。

状态流是：

`Kafka delivery → DB transaction → dedup insert → business update → outbox insert → commit → offset commit`

以及：

`outbox pending → send(event_id) → confirmed → sent`

失败恢复依赖可重复执行：数据库事务失败全部回滚；offset 失败导致再次 delivery，但唯一键挡住重复业务；发送结果未知导致同 event_id 再发，下游幂等挡住重复副作用。代价是多写两张状态表、唯一索引、outbox 扫描和重试运维，换来跨系统可审计的收敛路径。

## 项目经验版

项目映射提示：补入真实消息量、处理 P99、数据库类型、event_id 来源、事务边界、offset 提交方式、outbox 扫描/CDC 方案、下游幂等协议、最大重试时间和故障演练结果。没有真实数据时不要声称“线上已经 Exactly Once”。

## 常见追问

- 问：Kafka 开启幂等 producer 就够了吗？答：不够。它约束 Kafka producer retry，不会替外部数据库或 HTTP 下游去重。
- 问：数据库提交成功但 offset 提交失败怎么办？答：允许重投；再次处理时 `event_id` 唯一约束识别已提交事务，不重复改业务。
- 问：outbox 发出后超时怎么办？答：结果未知时保持同一 event_id 重试；下游必须用同一 ID 幂等。
- 问：为什么不先提交 offset 再写数据库？答：进程可能在两者之间崩溃，Kafka 认为已消费而业务结果没落库，形成不可重放的数据丢失。
- 问：去重表会无限长吗？答：会有存储成本；清理策略必须大于可能的重投/补偿窗口，并满足审计要求，不能按固定天数拍脑袋删除。

## 易错点

- 不要把“消费者只收到一次”当成业务 Exactly Once；真正目标是副作用只生效一次。
- 不要把 Kafka transaction 无边界扩展到外部数据库。
- 不要把 offset、业务事务、outbox 分成互不相关的提交步骤。
- 不要在模糊超时时生成新 event_id 重发。
- 不要只写正常链路，必须说明重复投递、崩溃、结果未知和长期失败如何收敛。
