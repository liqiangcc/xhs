<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_2494ec69","version":3,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_failure":"missing_evidence"} -->
# Redis持久化机制

## 核心结论

Redis 主要有 RDB 和 AOF 两类持久化机制。RDB 是某个时间点的数据快照，恢复快但可能丢失最近写入；AOF 记录写命令，数据更完整但文件更大、恢复更慢，生产中常组合使用。

## 1 分钟版

RDB 会按配置或手动触发生成 dump 文件，适合备份和快速恢复。AOF 会把写命令追加到日志文件，根据 appendfsync 策略决定刷盘频率，常见 everysec 会最多丢约 1 秒数据。AOF 文件会随着写入增长，需要 rewrite 重写压缩。Redis 4 之后还支持混合持久化，用 RDB 快照作为 AOF rewrite 的前半部分，再追加增量命令。

## 3 分钟版

RDB 通常通过 fork 子进程生成快照，父进程继续处理请求，依赖操作系统写时复制降低阻塞。但 fork 和 COW 在大内存实例上仍可能带来抖动。AOF 追加日志对数据更友好，刷盘策略分 always、everysec、no：always 最安全但慢，everysec 是常用折中，no 依赖操作系统刷盘。AOF rewrite 不是简单压缩旧日志，而是根据当前内存状态生成能恢复同样数据的最小命令集合。

## 关键细节

- RDB 恢复快，数据完整性弱于 AOF。
- AOF 数据更完整，但文件和恢复成本更高。
- everysec 是性能和可靠性的常见折中。
- 大实例 fork 可能造成延迟抖动。

## 原理机制

- RDB 保存的是内存数据快照。
- AOF 保存的是写命令追加日志。
- AOF rewrite 通过当前数据状态重建精简日志。
- 混合持久化结合 RDB 恢复速度和 AOF 增量完整性。

## 项目经验版

项目映射提示：先定义 Redis 数据是否可从数据库重建及允许的 RPO/RTO，再选择 RDB、AOF 或混合持久化。真实运行数据应包含 fork 耗时、AOF rewrite、COW 内存、磁盘余量和 fsync 延迟；没有数据时不承诺最多只丢固定秒数。

## 常见追问

- 问：RDB 和 AOF 如何选择？答：RDB 恢复快且适合备份，AOF 通常提供更小数据丢失窗口；可组合使用，但都需验证恢复。
- 问：AOF rewrite 会阻塞吗？答：大部分后台完成，但 fork、COW、磁盘竞争和最终切换仍可能造成延迟。
- 问：三种 appendfsync 策略区别？答：always 每次写后刷盘、everysec 由后台约每秒刷、no 交给 OS，可靠性与吞吐依次取舍。
- 问：宕机最多丢多少数据？答：取决于策略、OS 和故障类型；everysec 常说约一秒窗口，但不能作为所有故障下绝对保证。

## 易错点

- 不要说开启持久化就绝对不丢数据。
- 不要忽略磁盘 IO 对 Redis 延迟的影响。
- 不要把 AOF rewrite 理解成直接压缩原文件。
