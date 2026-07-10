<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_binlog_86a375fd","version":2,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_evidence_version":"v1"} -->
# MySQL binlog 模式与主从复制流程

## 核心结论

binlog 是 MySQL Server 层的逻辑变更日志，用于复制和时间点恢复。STATEMENT 记录 SQL、ROW 记录行事件、MIXED 自动选择；生产复制通常优先 ROW，以更确定的重放结果换取更大日志量。

## 1 分钟版

- STATEMENT 日志小、可读，但非确定函数、执行环境和顺序差异可能导致主从不一致。
- ROW 记录被修改行的前后镜像或必要列，重放确定、便于 CDC，但批量更新可能产生大日志。
- MIXED 默认按语句记录，遇到不安全语句切换为行格式，复杂度和排障心智更高。
- 复制中主库写 binlog，从库 I/O 线程拉取并写 relay log，SQL/applier 线程应用；现代并行复制可多 worker 执行。

## 3 分钟版

事务提交时，InnoDB redo log 与 Server 层 binlog 需要协调，经典两阶段提交避免出现“引擎已提交但 binlog 缺失”或相反状态。副本通过 file/position 或 GTID 定位事件，拉取、持久化 relay log 后重放。复制通常是异步的，主库提交不等于副本已应用；半同步也只增强至少一个副本收到日志的保证，不等于副本业务已完成应用。延迟、网络分区和大事务都可能放大只读副本陈旧性。

## 关键细节

- binlog 与 InnoDB redo log 分层不同：前者逻辑且跨引擎，后者服务崩溃恢复。
- ROW 模式仍需正确的主键/索引，避免副本应用时扫描过多数据。
- GTID 简化故障转移定位，但切换仍要处理数据完整性与旧主隔离。
- binlog 过期策略必须覆盖备份恢复窗口和最慢副本延迟。

## 原理机制

写链路是“事务产生引擎日志和 binlog 事件 → 协调提交 → dump/协议发送 → 副本 relay log → applier 重放”。恢复则从全量备份起点重放目标时间之前的 binlog。

## 项目经验版

项目映射提示：真实复制方案要提供 RPO/RTO、复制延迟告警、GTID/位点、备份校验和切换演练。没有演练记录时不声称“主从零丢失”。

## 常见追问

- 问：binlog 和 redo log 有什么区别？答：binlog 是 Server 层逻辑日志，用于复制/PITR；redo 是 InnoDB 物理变化日志，主要用于崩溃恢复。
- 问：ROW 为什么更可靠？答：它记录实际行变化，减少函数、触发条件和执行计划差异带来的不确定性。
- 问：半同步复制是否零丢失？答：不是，它只等待至少一个副本确认收到日志，仍需结合配置、故障场景和切换策略评估。
- 问：大事务为何导致复制延迟？答：生成、传输和应用都耗时，还可能阻塞后续可并行事务和产生大 relay/binlog。

## 易错点

- 不要说 binlog 是 InnoDB 独有日志。
- 不要把“副本收到”说成“副本已执行完成”。
- 不要忽略日志保留不足会破坏恢复和追平能力。
