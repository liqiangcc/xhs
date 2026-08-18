<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_kafka_duplicate_0a558c94","version":3,"status":"draft","updated_at":"2026-08-18","answer_type":"scenario","quality_tier":"candidate"} -->

# Kafka 如何处理重复消费？

## 核心结论

Kafka 的“重复消费”不能只靠调一个 Consumer 参数消除。只要采用常见的 **at-least-once** 处理方式，业务处理已经成功、但 offset 还没成功提交时发生进程崩溃、超时或 rebalance，恢复后就可能再次拿到同一条记录。工程上应把问题拆成三层：

1. **Producer 层**：开启并保持 Kafka idempotent producer 的约束，避免客户端自动重试在 Kafka 日志里制造不必要的重复；
2. **Consumer/Kafka 层**：明确“什么时候算处理完成”，只提交已经完成处理的连续 offset；consume-transform-produce 场景可用 Kafka transaction 把输出记录和 consumer offset 原子提交；
3. **业务副作用层**：对数据库、缓存、HTTP API 等 Kafka 之外的副作用使用稳定业务幂等键、唯一约束、状态机条件更新、inbox/outbox 或补偿机制。Kafka 的 transaction 不会自动把任意外部数据库写入纳入同一事务。

因此目标通常不是“保证一条消息永远只被拉取一次”，而是**允许重放，但让重复重放产生与第一次相同的业务结果**，并用重复率、重试、lag、DLQ/停车场、提交失败等指标验证系统处于可控状态。

## 1 分钟版

- Consumer 的 `position` 会随着 `poll()` 前进，但 `committed position` 是故障恢复点；两者不是一回事。业务处理成功、offset 尚未提交时宕机，恢复后就会重放。
- `enable.auto.commit=false` 只是让应用自己控制提交时机，**不是**“关闭重复消费开关”。手动提交同样存在“业务成功 → offset 提交成功”之间的故障窗口。
- 对关键业务，给事件定义稳定 `eventId`/业务幂等键，在数据库里建立唯一约束或 inbox 记录，并把“首次处理判定”和业务写放进同一数据库事务；重复事件命中唯一约束后返回已处理结果。
- 并行消费时只能提交“已经连续完成”的最高 offset 的下一位，不能因为高 offset 先处理完就越过仍未完成的低 offset。
- Producer 侧保持 `enable.idempotence=true` 的兼容配置；Kafka 4.x 文档要求 idempotence 配合 `acks=all`、`retries>0`、`max.in.flight.requests.per.connection<=5`。不要再在应用层盲目二次 resend，因为新的应用级 send 不属于同一次 producer retry 去重范围。
- 如果是 Kafka→Kafka 的 consume-transform-produce，可用 `transactional.id` + transaction + `sendOffsetsToTransaction`，并让下游 consumer 使用 `isolation.level=read_committed`。如果副作用是 MySQL/Redis/第三方 HTTP，则仍要单独设计幂等或 outbox/inbox。

## 3 分钟版

先看一个最常见窗口：Consumer 拉到 `order-paid-123`，数据库已经把订单状态改成 PAID，但 `commitSync()` 之前进程被杀。新实例会从最后的 committed offset 恢复，于是同一事件再次到达。如果处理逻辑是“余额减 100”这种非幂等写，就会产生二次扣款；如果处理逻辑是 `UPDATE order SET status='PAID' WHERE id=? AND status='UNPAID'`，或者先在同一事务插入 `consumer_inbox(event_id UNIQUE, ...)`，重复重放就可以被安全吸收。

我会按下面的顺序设计：

| 边界 | 主要重复来源 | 正确控制 |
| --- | --- | --- |
| Producer→Kafka | broker 响应丢失、客户端自动 retry | idempotent producer；`acks=all`、重试和 in-flight 配置保持兼容 |
| Kafka→Consumer | 处理成功后提交失败、进程崩溃、rebalance | 处理完成后提交；提交下一条待处理 offset；rebalance 时正确处理 in-flight |
| Consumer→Kafka | 输入处理与输出消息是两个状态 | Kafka transaction + `sendOffsetsToTransaction` |
| Consumer→DB/API | Kafka offset 与外部副作用是两个事务域 | 业务幂等键、唯一约束、条件更新、inbox/outbox、补偿/查询确认 |

对于 2,000 QPS、20 个 partition 的消费组，平均每 partition 100 QPS。如果单条处理 P99 已接近 500 ms，却一次 `poll()` 拉几千条并串行处理，就很容易碰到 `max.poll.interval.ms` 边界并触发 group membership 变化。调大 `max.poll.interval.ms` 可以给批处理更多时间，但不是根治；还应根据单批最大处理时间配置 `max.poll.records`，或把处理移到工作线程，同时对相应 partition `pause()`，并确保 offset 不会提交到仍在处理的记录之后。Kafka 官方 Consumer API 也明确提醒：多线程处理时必须避免 committed offset 跑到实际完成位置之前。

失败处理也要有边界。可重试错误使用有限次数 + 指数退避/抖动；不可恢复或超过预算的毒消息进入 DLQ/parking lot，保留原 topic/partition/offset/eventId/错误分类，避免一个永久失败记录无限阻塞整个 partition。重试必须继续复用同一个业务幂等键，不能每次重试重新生成 eventId。

## 关键细节

### 1. offset 提交的是“下一条要读的位置”

Kafka Consumer API 把 `position` 与 `committed position` 区分开：`poll()` 会推进当前 position，而 committed position 是重启或 rebalance 后恢复使用的位置。手工提交指定 offset 时，应提交**下一条待处理记录的 offset**，而不是“刚处理完那条的 offset”。

这也解释了为什么并行消费不能简单提交“当前见到的最大 offset”。例如同一 partition 的 offset 100、101、102 并行执行，101/102 已完成而 100 仍在处理，此时提交 103；如果实例随后崩溃，100 的业务结果会直接丢失。安全做法是维护每个 partition 的完成水位，只推进连续完成前缀。

### 2. 手动提交降低不确定性，但不消除重复窗口

`enable.auto.commit=false` 后，可以在业务完成后再调用 `commitSync/commitAsync`，从而避免“offset 已提交、业务还没做完”的明显丢消息风险。但数据库成功和 offset 成功仍是两个独立状态；二者之间发生故障时，重放依旧存在。所以“关闭自动提交”不能替代业务幂等。

`commitAsync` 还必须认真处理 callback 错误；Kafka API 说明它不会阻塞，错误会交给 callback，如果 callback 不提供则可能被丢弃。对需要严格恢复点的路径，常见做法是在正常循环中谨慎使用 async，在关闭/revoke 等边界用 sync 收口，并基于真实错误语义决定是否重试，而不是无限提交。

### 3. rebalance 与长耗时处理会放大重复

Consumer 如果长时间不 `poll()`，可能因为 `max.poll.interval.ms` 被认为失去 group membership，之后提交可出现 `CommitFailedException`。如果处理耗时不可预测，可减小 `max.poll.records`，或者让 poll loop 与工作线程分离；后一种方案必须暂停对应 partition、追踪 in-flight、只提交已完成的连续 offset。

使用 `ConsumerRebalanceListener` 时，`onPartitionsRevoked` 可以做必要的 offset/状态收口，但不要假设任何时候都一定能靠 revoke callback 完成全部业务；突然进程退出本身就不会给你一个“完美收尾”机会，因此幂等仍是最终兜底。

### 4. Producer idempotence 只解决它自己的边界

Kafka 4.1 Producer 文档指出，idempotent producer 可避免 producer retry 在日志中写出重复；但应用层重新调用一次新的 send 并不自动属于同一个 retry 去重语义，而且保证受 producer session/配置边界约束。因此不要把“Producer 开了 idempotence”解释成“业务端到端 exactly-once”。

### 5. Kafka transaction 的 exactly-once 要写清边界

Kafka transaction 适合 consume-transform-produce：把本次产出的 Kafka records 和输入 consumer offsets 放在同一个 transaction 中，`sendOffsetsToTransaction` 的 offsets 只有 transaction 成功提交后才算 committed；消费事务输出的一侧应使用 `isolation.level=read_committed`，否则会看到 aborted transactional records。

但如果中间步骤是 `UPDATE mysql_order ...` 或调用支付 API，这个外部副作用并不会因为 Kafka transaction 自动回滚/提交。典型方案是：

- 业务数据库内用 inbox + 业务写同事务；
- 数据库写与“待发 Kafka 事件”用 transactional outbox 同事务，再由独立 relay 投递；
- 外部 API 使用稳定 idempotency key，超时时先查询最终状态再决定重试；
- 无法做到强原子时，用状态机 + 补偿 + 对账收敛。

### 6. 去重表也需要容量和生命周期设计

如果 `consumer_inbox.event_id` 永久保留，吞吐 2,000 QPS 理论上一天约 1.728 亿条记录，存储和索引很快成为新瓶颈。真实设计要基于 Kafka 保留期、最大可重放窗口、业务追溯要求确定分区/归档/TTL，并确保 TTL 不短于允许重放的窗口。关键金融/库存副作用不能因为 Redis key 被淘汰就失去幂等保证。

## 原理机制

重复的根源是**两个状态机之间没有天然的原子提交**。

Consumer 从 Kafka 得到记录后，本地 `position` 已向前；业务数据库是另一个状态；Kafka 中的 committed offset 又是第三个状态。若顺序是：

`poll → DB commit → offset commit`

那么 DB commit 和 offset commit 之间崩溃会造成“业务已做、offset 未推进”，恢复后重复；如果反过来：

`poll → offset commit → DB commit`

那么 offset commit 和 DB commit 之间崩溃会造成“offset 已推进、业务未做”，恢复后消息可能被跳过。

在一个事务域内，原子事务可以合并状态：Kafka transaction 能合并 Kafka 输出 records 和 consumer offsets；数据库事务能合并 inbox 去重标记与业务写。但跨 Kafka 与任意外部系统通常不能凭一个普通本地事务自动合并，所以工程上转向**幂等 + 可重放 + 可观测 + 补偿/对账**。

稳定幂等键必须代表“同一个业务动作”，而不是“某次处理尝试”。优先使用上游天然唯一业务 ID（如 paymentId、orderId+eventType+version），或者由生产端生成一次并随消息传播的 eventId。重复消费、重试和 DLQ 回放都复用这个值。

## 项目经验版

以“订单支付完成事件驱动积分发放”为例：topic 有 24 个 partition，正常峰值约 4,800 msg/s，consumer group 有 12 个实例。每条消息带 `eventId`、`orderId`、`eventType`、`occurredAt`。

数据库设计一个 `points_event_inbox(event_id UNIQUE, order_id, status, processed_at, ...)`。事务内先尝试插入 inbox；若唯一键冲突，查询已存在状态并直接返回成功；首次事件则执行积分状态机更新，并把 inbox 标为完成，再提交数据库事务。只有这一步成功后才推进该 partition 的连续 offset 水位。

如果处理超时，消费者不会创建新的 eventId，而是按错误分类有限重试；数据库连接超时后先根据 `eventId` 查询是否已提交，避免“未知结果就再加一次积分”。超过重试预算进入 parking topic。回放工具同样保留原 eventId，因此人工重放不会绕过幂等。

监控至少包括：consumer lag、records consumed rate、rebalance 次数/耗时、offset commit failure、处理 P95/P99、retry rate、幂等冲突/duplicate-hit rate、DLQ rate、parking backlog、数据库唯一冲突异常分类和业务成功率。告警不应只看 lag；例如 lag 为 0 但 duplicate-hit 突然从 0.01% 升到 8%，通常说明上游重发、consumer 重启/rebalance 或提交链路出现异常。

上线前回归验证包括：

1. 在 DB commit 后、offset commit 前主动 kill consumer，验证重放只命中同一 eventId，业务结果不增加第二次；
2. 注入 offset commit timeout/失败，验证恢复后仍可安全重放；
3. 处理时间故意超过正常 poll 周期，验证 rebalance/in-flight 管理不会越过未完成 offset；
4. producer 注入可重试错误，确认 idempotent producer 配置有效且不会应用层盲目 resend；
5. 对 Kafka→Kafka 流程注入 transaction abort，确认 `read_committed` 下游看不到 aborted 输出；
6. 回放 DLQ/parking 消息，确认仍使用原 eventId，且成功率、延迟、lag 和幂等冲突指标符合 SLO。

## 常见追问

### 1. 把 `enable.auto.commit` 关掉就不会重复了吗？

不会。它只把 offset 提交时机交给应用；业务成功到手工提交成功之间仍然有故障窗口。真正控制业务重复副作用的是幂等或同事务状态设计。

### 2. 手动 `commitSync()` 比 `commitAsync()` 更安全吗？

`commitSync()` 会等待成功、不可恢复错误或超时，边界更直观；`commitAsync()` 不阻塞，错误通过 callback 返回。二者都不能把外部数据库写与 Kafka offset 自动变成一个事务，也都不能替代幂等。

### 3. Kafka 开启 `enable.idempotence=true` 后，Consumer 就不会重复了吗？

不是。idempotent producer 主要防止 producer retry 在 Kafka 日志里产生重复；consumer 在“业务完成但 offset 未提交”的故障窗口仍可能重新读取同一 record。

### 4. Kafka transaction 能不能保证 MySQL 只写一次？

不能自动保证。Kafka transaction 能原子协调 Kafka records 与 consumer offsets；MySQL 是另一个事务域。对 MySQL 仍应使用唯一约束/inbox/outbox/条件更新等方案，或采用经过明确验证的跨系统事务架构。

### 5. Redis `SETNX` 能不能做消费幂等？

低风险、短窗口场景可以作为辅助，但关键业务必须考虑 key 过期、淘汰、故障恢复和数据持久性。若 Redis 去重键比 Kafka 可重放窗口更早消失，旧消息一旦回放仍会重复执行。通常将去重记录和业务写放在同一数据库事务更容易得到强边界。

### 6. 为什么并行消费后不能直接提交最大 offset？

因为同 partition 内低 offset 可能仍未完成。如果 100 没完成而 101、102 完成后提交 103，实例崩溃后 100 会被跳过。必须提交“连续完成前缀”的下一 offset。

### 7. 出现大量 duplicate-hit 是坏事吗？

幂等命中本身说明保护生效，但突增通常是上游重复生产、consumer crash/rebalance、offset commit 失败或重放行为发生变化的信号。应把 duplicate-hit 当成观测指标，而不是静默吞掉后完全不管。

## 易错点

- 把 at-least-once 误解成“Kafka 有 bug 才会重复”，没有把故障窗口当成正常语义设计；
- 认为关闭自动提交或改用手动提交就彻底解决重复；
- Producer 开启 idempotence 后仍在应用层收到模糊错误就重新构造并发送新消息，扩大重复来源；
- 把 Kafka EOS 宣传成“Kafka + MySQL + HTTP 全链路天然 exactly-once”；
- 并行处理同一 partition 时越过未完成低 offset 提交高 offset；
- eventId 每次重试重新生成，导致幂等表形同虚设；
- 使用短 TTL/易淘汰 Redis key 保护关键资金或库存副作用，却没有按最大重放窗口设计；
- `commitAsync` 不提供 callback 或忽略提交错误，导致恢复点长期落后；
- 毒消息无限重试，造成 partition 卡死、lag 飙升和下游雪崩；
- 只监控 consumer lag，不监控 rebalance、commit failure、duplicate-hit、retry/DLQ 和业务成功率；
- 只做正常路径测试，没有在 DB commit 与 offset commit 之间 kill 进程做真实重放验证。