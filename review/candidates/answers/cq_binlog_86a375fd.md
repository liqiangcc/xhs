<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_binlog_86a375fd","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"mechanism","quality_tier":"candidate"} -->
# MySQL binlog 模式与主从复制流程

## 核心结论

以 MySQL 8.4 为边界，binlog 是 source 记录数据或结构变更事件的复制日志：`STATEMENT` 记录 SQL，`ROW` 记录受影响的行事件，`MIXED` 默认用语句格式并在特定情形切到行格式。复制不是“提交后立刻所有副本可读”：replica 主动拉取 binlog，先写本地 relay log，再由 applier 执行；因此格式、延迟、确认语义和故障切换都必须绑定配置。

## 1 分钟版

- 格式：MySQL 8.4 中 `ROW` 是默认格式；STATEMENT 的可重放性受非确定性语句等约束，MIXED 会在特定情形使用 ROW。
- source 侧把修改写入 binlog；replica 连接后主动请求并接收事件，先写本地 relay log，同时维护 source 与 relay 的处理位点。
- replica 的 applier 再从 relay log 执行事务；接收、落盘和应用是不同状态，异步复制的读副本可能落后。
- 半同步是可选确认路径：source 等待至少一个 replica 已接收并落盘 relay log 的确认，不等于该事务已在 replica 执行提交。

## 3 分钟版

先声明适用面：以下是 MySQL 8.4 的经典 source/replica 复制链路，实际行为还受 `binlog_format`、复制过滤、GTID/位点配置、relay log 相关配置和半同步插件配置影响。

一次事务提交后，source 的 binlog 提供可传输的事件序列。replica 并不是被动推送，而是主动请求 binlog：收到事件后先写本地 relay log，并保存源端 binlog 与本地 relay log 的位置信息；applier 读取 relay log 并在 replica 上执行，因此链路至少有“source 已记录、replica 已接收/写入 relay、replica 已应用”三种可观测状态。异步复制中这三者可分离，排障不能只看连接存在。

格式决定事件表达而不是复制拓扑：STATEMENT 传播语句，但要面对非确定性和 source/replica 执行环境差异；ROW 传播行变更，重放边界更直接但日志量和网络/relay I/O 会随变更行数和配置而变化；MIXED 以语句格式为主，在 MySQL 判定不适合语句复制的情形切换为 ROW。答案不应把三种模式说成固定的性能排序。

若启用半同步，source 等到配置数量的 replica 已接收并把事件写入且刷入 relay log 才向会话返回；它提高了“至少一份副本已持久接收”的保证，但确认不表示 applier 已执行，也不替代故障切换时的旧主隔离、位点/GTID 一致性检查。MySQL 8.4 的并行 applier 由 coordinator 从 relay log 调度 worker；增大 worker 只提高潜在并行度，锁竞争和大事务仍可能限制收益。

## 关键细节

- MySQL 8.4 的 `ROW` 为默认 `binlog_format`；若环境不是 8.4 或被显式配置，先查 `binlog_format`，不要背默认值。
- STATEMENT 的风险是同一语句在副本上未必得到同一结果；MySQL 会对无法保证安全的语句给出潜在不可靠警告，ROW 是规避这一类问题的路径。
- relay log 是 replica 本地接收、待应用的日志队列，不是 source binlog 的别名；应分别观察接收进度、应用进度和错误。
- `replica_parallel_workers` 大于等于 1 时，coordinator 从 relay log 读取事务并调度 worker；并行度、提交顺序与实际吞吐都要结合配置和工作负载验证。
- 半同步超时且没有 replica 确认时，source 会退回异步复制；这是一条可用性与数据保护之间的配置边界。

## 原理机制

参与者是 source binlog、replica 接收侧、relay log、位点元数据以及 applier（单线程或 coordinator/worker）。状态流是：source 记录变更事件 → replica 主动请求并接收 → 写入本地 relay log 并推进接收进度 → applier 读取 relay log、执行事务并推进应用位点。

保证来自顺序事件与可恢复的位点，而不是“网络一通就强一致”。ROW/STATEMENT/MIXED 影响事件如何表达；relay log 将接收与应用解耦；半同步把 source 对客户端的返回点延后到至少一个 replica 的接收落盘确认。代价则分别落在 binlog/relay 的存储与网络、applier 执行延迟，以及半同步等待的提交延迟上。

## 项目经验版

项目映射提示：请按真实环境补充 MySQL 版本、`binlog_format`、GTID 或 file/position、是否启用半同步、replica 数量、写入量和监控截图。排障叙述应区分“接收慢、relay 积压、应用慢、复制错误、切换前位点确认”，没有真实证据时不要虚构延迟数值或切换事故。

## 常见追问

- 问：ROW 一定比 STATEMENT 更好吗？答：不是。ROW 避开一类语句重放不确定性，但日志与 I/O 成本取决于实际行变更规模与配置；应按正确性、流量和运维需求选择。
- 问：replica 已收到 relay log，业务读就一定看到数据了吗？答：不一定。接收写 relay 与 applier 执行是两个阶段；半同步确认也只覆盖接收并落盘，不代表已应用。
- 问：半同步为什么仍不能保证故障切换绝不丢数据？答：它只约束确认点；切换还要处理已应用差异、旧主隔离和 GTID/位点选择，不能把一项确认机制等同于完整的选主协议。
- 问：为什么加大并行 worker 后延迟不一定下降？答：worker 只提高可并行执行的上限；事务依赖、锁竞争和大事务都可能让调度无法转化为吞吐。

## 易错点

- 不要把 binlog、relay log 和 InnoDB redo log 混成同一份日志。
- 不要把“replica 收到”说成“replica 已应用”，尤其在半同步场景。
- 不要把 MySQL 8.4 的默认格式、并行 applier 默认值或插件行为套到所有版本和所有配置。
- 不要只讲三种格式定义而漏掉 source 记录、replica 接收、relay 落盘、applier 执行这条状态链。
