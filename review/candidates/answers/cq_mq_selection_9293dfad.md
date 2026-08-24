<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_mq_selection_9293dfad","version":3,"status":"draft","updated_at":"2026-08-18","answer_type":"scenario","quality_tier":"candidate"} -->
# 如何根据业务场景选择 Kafka、RocketMQ 和 RabbitMQ？

## 核心结论

我不会先按“谁 TPS 最高”选 MQ，而是先冻结消息语义和容量边界，再看三类模型是否匹配：**需要长期保留、按 offset 重放、多消费组事件流时优先验证 Kafka；需要 FIFO/延时/事务等业务消息语义时优先验证 RocketMQ；需要 AMQP Exchange/Binding 的灵活路由、队列投递与成熟确认模型时优先验证 RabbitMQ。** 最终决策必须用同一硬件、同一消息大小、同一副本/持久化和确认策略做故障与积压恢复压测，不能拿不同厂商宣传峰值直接比较。

## 1 分钟版

我会用 5 个问题收敛选型：

1. **消息要不要保留和重放？** 需要把事件当可重复读取的日志、多下游各自维护消费位置，Kafka 的 partition + retention + consumer group 模型更自然。
2. **是不是典型业务消息？** 如果核心需求就是同一业务 key 的 FIFO、定时/延时触发、生产端本地事务与消息最终一致，RocketMQ 5.x 有明确的 FIFO、Delay、Transaction 消息类型，但要接受各类型自己的约束。
3. **路由拓扑复杂不复杂？** 如果要 direct/topic/fanout 等 Exchange + Binding 路由、工作队列、手工 ack/prefetch，RabbitMQ 的模型更直接；高可用队列要按当前版本评估 quorum queue，长积压/流式读取还要评估 RabbitMQ Streams，而不是把 RabbitMQ 当成只有一种 Queue。
4. **容量和恢复目标是什么？** 至少明确峰值 msg/s、MB/s、最大消息、消费组数、可接受 P99、最长积压、希望多久清空、故障域和 RPO/RTO。
5. **一致性边界在哪里？** MQ 的确认或事务能力不等于“数据库业务天然 exactly-once”；消费端仍要用业务幂等键、唯一约束/状态机等守住重复执行边界。

所以最后不是“Kafka > RocketMQ > RabbitMQ”这种排序，而是**需求矩阵先筛模型，再用目标环境压测决定**。

## 3 分钟版

### 第一步：先把需求写成可验收约束

我先问清楚：

- 峰值与稳态消息数 `λ_peak` / `λ_avg`，平均和 P99 消息大小 `S_avg` / `S_p99`；
- 是否需要保留几小时、几天或更久，是否允许任意 consumer 回放历史；
- 顺序是全局、topic、partition/message-group，还是“同一个订单/用户 key”局部有序；
- 是否需要定时/延时、死信、复杂路由、请求削峰、事件流、CDC、事务消息；
- 有多少独立消费组，下游失败后最大允许积压多少，要求多久追平；
- 生产确认、消费确认、重复投递、跨数据库副作用分别允许什么语义；
- 单机房、同城双活还是跨地域灾备，目标 RPO/RTO 是什么；
- 团队当前 Java SDK、监控、升级、容量治理能力以及是否使用托管服务。

没有这些约束，产品选型只有偏好，没有工程结论。

### 第二步：按消息模型做第一轮筛选

#### Kafka：日志/事件流和重放优先

Kafka 官方文档把 topic 建模为可保留的、分区的事件日志。事件消费后不会因为某个 consumer 已读就立即从 topic 删除，而是由 retention 控制保留周期；传统 consumer group 内，一个 partition 在同一时刻分配给一个 group member，多个 group 可以独立读取同一份数据。Kafka 只保证 partition 内顺序，所以业务顺序通常要把相同 key 路由到同一 partition。

因此，如果场景是 CDC、埋点/日志、事件总线、流处理、多个独立下游、需要按 offset 重放，我会先把 Kafka 放进候选。它的代价是你要认真治理 partition 数、key 倾斜、consumer rebalance、保留容量和磁盘/网络吞吐；如果只要一个简单工作队列，日志模型未必是最低复杂度选择。

Kafka 的事务和 exactly-once 也有明确边界：官方设计文档说明，读 Kafka → 处理 → 写回 Kafka 时可以用事务 producer、consumer offset 与 `read_committed` 形成 exactly-once processing；写外部数据库或外部系统时，仍需要外部系统与 offset/结果协同，不能把“Kafka 支持 EOS”翻译成所有业务副作用自动只执行一次。

#### RocketMQ：业务消息高级语义优先

RocketMQ 5.0 官方文档把 FIFO、Delay、Transaction 作为明确的消息类型。FIFO 通过 message group 约束同组消息顺序；Delay 在指定时间后变为可消费；Transaction 用 half message、生产者本地事务结果与 transaction check 解决“本地事务成功但消息发送结果不确定”一类生产侧最终一致问题。

因此，如果系统是订单、支付后置流程、库存/物流事件、超时关单、局部顺序状态流，并且这些高级语义能显著减少自研状态机，我会优先验证 RocketMQ。但版本和类型边界必须写清楚，例如 5.0 的 topic/message type 约束与 4.x 并不完全一样；事务消息只保证生产侧本地事务与消息提交的最终一致，并不替你保证下游消费结果和上游数据库天然处于一个全局事务里。

#### RabbitMQ：路由/队列拓扑和确认模型优先

RabbitMQ 的 AMQP 0-9-1 Exchange + Binding 模型直接表达 direct、topic、fanout 等路由：publisher 先发到 exchange，再由 binding 把消息路由到一个或多个 queue/stream。Consumer 可以使用手工 acknowledgement，并配合 prefetch 控制未确认的 in-flight 消息数量；publisher confirm 则用于确认 broker 已接管发布结果。

如果需求是复杂 routing key、多类工作队列、扇出、明确的队列消费和 ack 控制，我会优先验证 RabbitMQ。高可用与积压也要按当前队列类型判断：RabbitMQ 4.x 官方文档把 quorum queue 作为复制、高可用队列的重要选择，并明确提醒超长 backlog、最低延迟等场景未必适合 quorum queue，长积压/流式场景应把 Streams 纳入比较。因此不能用十年前“RabbitMQ 就是 classic queue”的经验直接做新版本选型。

## 容量估算：先算量，再谈产品

即使没有真实业务数字，也可以先把公式固定下来：

- 入口字节吞吐：`B_in = λ_peak × S_avg`；
- 若按副本/复制存储，磁盘与网络还要乘上实际复制因子和协议开销，不能只看生产者入口流量；
- 保留容量近似：`Storage ≈ λ_avg × S_avg × retention_seconds × replication_factor × safety_factor`；
- 最大积压消息数：`Lag_max = λ_in × outage_seconds`；
- 若要求 `T_recover` 时间清空积压，恢复阶段消费能力必须满足：`μ_recover > λ_live + Lag_max / T_recover`；
- 分区/queue/message-group 数不是越多越好，要同时验证单分片热点、leader/replica 开销、consumer 并行度和 rebalance/故障恢复成本。

举例只用于说明算法：假设峰值 `50,000 msg/s`、平均 `1 KiB`，应用入口就约 `49 MiB/s`；如果某下游停 30 分钟，会产生约 9,000 万条积压。若恢复后还要在 60 分钟内追平，除了继续承接在线 `50,000 msg/s`，消费侧还需额外平均处理约 `25,000 msg/s` 的历史积压。**这个算式只是容量验收方法，不代表任何一个 MQ 在你的硬件上一定达到该值。**

## 核心数据流与一致性设计

无论选哪个 MQ，我都会把业务数据流收敛成：

`业务事务/事件产生 -> Producer -> Broker 持久化/复制 -> Consumer 拉取或投递 -> 幂等业务处理 -> Ack/Offset 提交`

消息最少包含：

- `event_id`：全局业务幂等键；
- `aggregate_id` / `order_id`：需要局部顺序时作为 partition key/message group/routing key 的候选；
- `event_type`、`schema_version`；
- `occurred_at`；
- 业务 payload；
- 可选 `trace_id` / `correlation_id`。

消费端原则是**先完成可验证的业务副作用，再提交 ack/offset**；重复投递时用 `event_id + 业务唯一约束/状态机版本` 保证再次执行无害。若是 DB 更新 + 发消息，优先选择能明确证明原子边界的方案，例如事务 outbox/CDC，或者在适用场景验证 RocketMQ Transaction Message；不能靠“先写 DB 再 send，一般不会失败”。

顺序也必须局部化：如果只要求同一订单有序，就以 `order_id` 做 key/message group，而不是为了追求全局顺序把所有流量压到一个 partition/queue。局部顺序能换取更高并行度，但热点 key 仍要单独监控。

## 超时、重试、降级、补偿与灾备

### 超时与重试

Producer send、broker confirm、consumer processing 都要独立超时。重试必须区分“明确失败”和“结果未知”：结果未知时不能盲目生成新业务 ID，否则会把一次操作变成两次不同事件。Consumer 重试需要最大次数/退避/死信或停车队列，并把 poison message 与基础设施故障分开。

### 降级

非关键通知可以在 MQ 故障时降级为 outbox/本地持久化后补投；支付、库存等关键业务如果无法证明消息最终可达，则宁可阻断对应写路径或切换到经过演练的备用通道，也不能静默丢消息。降级策略要在产品选择前写进 DoD，因为它会反过来影响“是否必须依赖 broker 高可用”。

### 补偿

对已经产生外部副作用的消费失败，不能只无限重试；要有可审计的补偿任务、人工处置入口和幂等重放。事务消息也不是补偿机制的替代品，尤其是下游已经调用第三方系统时。

### 灾备

灾备验证至少覆盖 broker 节点丢失、leader 切换、网络隔离、磁盘满、单 AZ 故障、consumer 整组退出、producer 重连。跨地域复制/镜像必须按具体产品版本和部署形态单独设计，因为三者的复制机制、托管能力和一致性边界不同，不能在选型答案里假设统一行为。

## 对比矩阵

| 约束 | Kafka 优先验证 | RocketMQ 优先验证 | RabbitMQ 优先验证 |
|---|---|---|---|
| 长时间保留 + offset 重放 | 强匹配：partitioned retained log | 可回溯但需按版本/保留策略验证 | Queue 不应一概当日志；长保留要评估 Streams |
| 多独立消费组读同一事件流 | 强匹配 | 支持消费组，结合业务消息模型评估 | 可用多 queue/stream 拓扑实现，但模型不同 |
| 同业务 key 局部顺序 | key → partition，partition 内有序 | message group/FIFO 是一等语义 | 可设计单活 consumer/队列拓扑，但需验证并发边界 |
| 延时/定时业务消息 | 需要额外设计或对应能力评估 | 5.0 Delay Message 是明确类型 | TTL/DLX、插件或应用调度等方案需按当前能力验证 |
| 生产侧本地事务与消息最终一致 | Kafka transaction 更适合 Kafka 内部 read-process-write 边界；外部 DB 仍需协同 | Transaction Message 明确解决本地事务 + 消息提交最终一致的一类场景 | 常用 outbox + confirm 等组合，不能把 confirm 当 DB 事务 |
| direct/topic/fanout 等路由 | 主要依赖 topic/key/streaming 设计 | Topic/Tag/消息模型 | Exchange + Binding 是核心模型 |
| 复制高可用工作队列 | 不是典型“单队列”模型 | 按 broker/replica 部署验证 | 4.x quorum queue 是重要候选 |
| 极长 backlog/流式消费 | 典型候选 | 按保留、磁盘和消费模型压测 | RabbitMQ 官方建议长 backlog 同时评估 Streams |

这张表只是**进入 PoC 的筛选器**，不是最后评分表。

## PoC、观测和上线门槛

三个候选必须使用同一组 workload：

1. 小/中/大三档消息大小，不只测 1 KB；
2. 稳态、2 倍突发、consumer 全停形成积压、恢复追平；
3. producer/broker/consumer 分别故障，记录重试、重复、丢失和恢复时间；
4. 开启目标生产配置：副本、持久化、ack/confirm、压缩、批量策略必须与上线一致；
5. 顺序场景专门加入热点 key 和乱序断言；
6. 一致性场景故意在“业务提交前/后、send 前/后、ack 前/后”注入 crash；
7. 至少观察 P50/P95/P99 publish/consume latency、msg/s、MB/s、积压、积压年龄、磁盘/网络/CPU、GC、broker replication health、rebalance/leader switch、重试/死信率；
8. 记录节点故障到恢复服务的 RTO，以及故障窗口是否越过业务 RPO；
9. 用真实 Java SDK、真实序列化、真实 TLS/ACL，不用只测 broker 本机 benchmark；
10. 做 5% → 20% → 50% → 100% 灰度或按 topic/业务线迁移，保留双写/回滚窗口，并验证旧消息如何消费完。

## 怎么做最终选择

我会给需求矩阵加“硬门槛”和“加权项”：

- 硬门槛：消息语义、RPO/RTO、安全合规、客户端语言、目标部署环境必须满足；任何一项不满足就淘汰。
- 加权项：目标 workload 的 P99、积压恢复速度、稳定性、监控成熟度、升级复杂度、托管成本、团队熟悉度。
- 最后保留压测报告和失败注入证据，而不是一句“Kafka 性能最好”或“RabbitMQ 延迟最低”。

典型决策可以是：

- **事件平台/CDC/日志流**：先做 Kafka PoC；
- **订单状态、延时关单、局部 FIFO、生产侧事务消息**：先做 RocketMQ PoC；
- **复杂 AMQP 路由、传统工作队列、需要明确 ack/prefetch 控制**：先做 RabbitMQ PoC；
- **混合场景**：允许不同业务使用不同中间件，但要把平台维护成本算进方案；如果团队只能承受一套 MQ，就用“覆盖核心场景 + 最小自研补偿”的总成本做取舍，而不是为了功能全集同时维护三套集群。

## 常见追问

- **问：Kafka 为什么适合日志和事件流？** 答：topic 是可保留的 partitioned log，consumer group 维护读取位置，事件在 retention 窗口内可以重新读取；partition 同时提供扩展与局部顺序边界。
- **问：RocketMQ 事务消息是不是就不用做幂等了？** 答：不是。它解决的是生产者本地事务与消息提交结果之间的一类最终一致；下游消费仍可能面对重试和重复，需要业务幂等。
- **问：RabbitMQ 为什么不直接说“低延迟”？** 答：延迟受 queue 类型、confirm、持久化、副本、prefetch、消息大小和负载影响。更可靠的产品特征是它的 Exchange/Binding 路由和 ack/prefetch 模型；延迟必须在目标配置下实测。
- **问：顺序消息为什么不能直接做全局顺序？** 答：全局顺序会把并行度压缩到单一有序域。通常只要求同一订单/用户有序，把 key 映射到 partition/message group 可以保留跨 key 并行度。
- **问：怎么判断积压能力够不够？** 答：不要只看“能存多少”，要验证停消费形成 `Lag_max` 后，在继续承接在线流量的同时，能否在业务要求的 `T_recover` 内追平，并观察磁盘、网络、P99 和 consumer error 是否恶化。
- **问：三个 MQ 能不能只选一个？** 答：可以，但必须明确牺牲什么。单平台降低运维复杂度，代价可能是某些高级语义需要自研；多平台提高场景匹配度，代价是容量、监控、升级、SDK 和值班体系成倍增加。

## 易错点

- 不要用脱离消息大小、副本、持久化和 ack 策略的单一 TPS 数字排名。
- 不要说 Kafka 对任意外部数据库业务都“天然 exactly-once”。
- 不要把 RocketMQ Transaction Message 说成跨所有下游的全局分布式事务。
- 不要说 RocketMQ 全局有序；5.0 FIFO 的核心边界是 message group，生产和消费两端还要满足顺序条件。
- 不要把 RabbitMQ 新版本只理解成 classic queue；quorum queue 与 Streams 的适用边界会影响高可用和长积压设计。
- 不要把 publisher confirm、consumer ack、offset commit 等同于业务副作用已经幂等完成。
- 不要把“官方支持某功能”直接翻译成“我们环境一定满足 SLA”；最终结论必须回到真实 workload、故障注入和可回滚上线证据。
