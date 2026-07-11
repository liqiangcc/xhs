<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_2494ec69","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"concept","quality_tier":"candidate"} -->
# Redis持久化机制

## 核心结论

Redis 有 RDB 快照、AOF 追加日志、两者组合和关闭持久化四种选择。RDB 定时保存数据集的时间点快照，文件紧凑且大数据集恢复快；AOF 记录收到的写命令并在启动时重放，耐久性由 `appendfsync` 策略决定。选择不是“谁更好”，而是在可接受数据丢失窗口、重启时间、磁盘与 fork 开销、备份恢复需求之间取舍。

## 1 分钟版

- RDB：在配置的保存点生成二进制快照，适合备份、灾备和较快重启；故障时会丢失上次快照以来的写入。
- AOF：每个改变数据集的命令追加到日志，重启时重放；`appendfsync always` 最安全但慢，`everysec` 是 Redis 文档建议且默认的策略，灾难时可能丢约 1 秒，`no` 交给 OS。
- 组合：官方建议重视数据安全时同时保留 RDB 和 AOF；RDB 仍适合作为备份与较快恢复手段。
- 关键边界：RDB/AOF 都有 fork/磁盘成本；不要只背 `everysec` 而忽略实际存储延迟、断电风险、恢复目标和版本。

## 3 分钟版

先按同一维度比较。RDB 是指定间隔的 point-in-time snapshot：Redis 可以按 N 秒内至少 M 次改动触发，也可以由 `SAVE`/`BGSAVE` 触发。持久化时子进程写临时 RDB 文件，完成后替换旧文件。它是紧凑单文件，便于异地备份与灾备，且 Redis 官方文档说明大数据集下恢复通常快于 AOF；代价是快照之间的写入不在最近 RDB 中，异常停止可能丢失最近几分钟的数据，且大数据集的 fork 可能造成服务短暂停顿。

AOF 是命令日志：Redis 接到改变数据集的命令后追加，重启时重放以重建状态。耐久性由 `appendfsync` 定义：`always` 每批命令追加后 fsync，最安全但很慢；`everysec` 每秒 fsync，文档说明灾难时可能丢失 1 秒；`no` 不主动 fsync，由 OS 决定。AOF 的代价是通常比同一数据集的 RDB 更大，且性能受具体 fsync 策略影响。不能把“每秒最多丢一秒”说成网络、主从切换、磁盘损坏或业务端确认的完整数据不丢保证。

AOF 会随着写入增长，因此 Redis 可在后台 rewrite：生成恢复当前数据集所需的最小操作集合，同时旧 AOF 继续追加，完成后切换到新文件。Redis 7.0.0 起使用 multi-part AOF：一个 base file、一个或多个 incremental file，由 manifest 跟踪；重写时父进程打开新 incremental AOF，完成后原子替换 manifest。此版本细节不应倒灌到 Redis < 7.0。

选型先问 RPO、RTO、写入量、磁盘延迟、允许的 fork 停顿和备份策略。可接受分钟级丢失且优先备份/快速恢复时可选 RDB；需要较小写入丢失窗口时评估 AOF `everysec` 或更严格策略；数据重要时同时用 RDB+AOF，并做恢复演练。关闭持久化只适合能从其他真源重建且明确可丢的缓存，不是默认高可用方案。

## 关键细节

- `appendfsync always` 的“每次”指多个客户端/管道命令执行后的一批 AOF 追加；Redis 文档说明会在回复前执行单次 write/fsync。
- `everysec` 是 Redis 文档建议且默认的 AOF 策略；`no` 的实际刷盘时机受 OS 内核调优影响，不能给固定数据丢失时间承诺。
- Redis 7.0.0 multi-part AOF 由 base/incremental 文件与 manifest 组成；排障和备份应按 manifest 一组处理，而不是假设永远只有一个 AOF 文件。
- AOF 截断与中间损坏的恢复行为不同：最新版本可在允许截断加载时丢弃最后一个不完整命令；中间无效字节可能需要先备份再检查/修复，修复可能丢弃后续部分。

## 原理机制

RDB 的状态链是 `内存数据 → fork 子进程 → 临时快照 → 原子替换 RDB`；它以快照间隔换恢复速度和紧凑性。AOF 的状态链是 `写命令 → AOF 追加 → 按 fsync 策略落盘 → 重启重放`；它以更多日志和 fsync 成本换更小的本地持久化窗口。AOF rewrite 把“长历史命令序列”压缩为“恢复当前状态所需的命令集”，同时保留重写期间的增量写入，因此不能只看文件大小而忽略重写状态与剩余磁盘空间。

两条链都不承诺业务端到端强一致：持久化仅覆盖 Redis 本机数据的恢复材料。应用仍要处理上游真源、复制/故障切换、写入确认、备份校验和灾备恢复流程。

## 项目经验版

项目映射提示：补充真实 Redis 版本、RPO/RTO、数据集大小、写 QPS、磁盘类型与延迟、`save`/`appendfsync` 配置、AOF rewrite 指标、备份保留、一次从备份与 AOF 恢复的演练结果。没有这些事实时不要虚构“线上从未丢数据”或固定恢复耗时。

## 常见追问

- 问：为什么有 AOF 还要 RDB？答：RDB 是紧凑快照，官方文档指出它适合备份、灾备和大数据集较快重启；数据重要时官方建议两者结合，而不是把 AOF 当作唯一备份策略。
- 问：`appendfsync everysec` 就绝不丢数据吗？答：不是。它只限定本机 AOF 的 fsync 频率，灾难时文档说明可能损失约 1 秒写入；还不能覆盖业务确认、磁盘故障、复制与切换问题。
- 问：AOF rewrite 会停写吗？答：正常重写时 Redis 继续向旧 AOF 追加，同时生成新文件，完成后切换；但仍要监控重写状态、fork、磁盘空间和版本差异。
- 问：Redis 7 的 AOF 有什么边界？答：7.0.0 起是 base+incremental+manifest 的 multi-part AOF；运维脚本、备份和恢复必须尊重 manifest，不能沿用单文件假设。

## 易错点

- 不要把 RDB 说成“完全不丢数据”，它只保存某个时间点快照。
- 不要把 AOF `everysec` 说成端到端数据不丢或把默认值套到未开启 AOF 的实例。
- 不要混淆 AOF rewrite 和 RDB snapshot：前者重建当前状态的命令日志，后者生成数据集快照。
- 不要把 Redis 7 的 multi-part AOF、老版本单文件 AOF 和应用自己的备份/复制语义混成一个结论。
