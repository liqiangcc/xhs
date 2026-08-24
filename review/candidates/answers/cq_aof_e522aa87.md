<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_aof_e522aa87","version":2,"status":"draft","updated_at":"2026-08-17","answer_type":"mechanism","quality_tier":"candidate"} -->
# Redis AOF 重写的过程

## 核心结论

AOF 重写不是压缩旧日志，而是根据当前数据集重新生成更短、仍可完整恢复状态的 AOF。回答时必须先区分版本：Redis 7.0 之前是“子进程生成新临时 AOF + 父进程继续写旧 AOF并缓存重写期间增量 + 合并增量 + 原子替换”的单文件流程；Redis 7.0 起改为 multi-part AOF，重写开始时父进程先打开新的 INCR AOF，子进程生成新的 BASE AOF，成功后通过新的 manifest 原子切换到新 BASE+INCR 集合。

## 1 分钟版

- `BGREWRITEAOF` 会异步启动 AOF 重写；Redis 2.4 起也可以按配置自动触发。若已有后台持久化子进程，重写可能被调度而不是立即开始。
- Redis 7.0 之前：fork 后子进程从 fork 时刻的内存视图生成临时 AOF；父进程仍服务客户端，把新写入继续追加旧 AOF，同时放入重写增量缓冲。子进程完成后，父进程把缓冲增量追加到新文件，再原子替换旧 AOF。
- Redis 7.0 起：父进程在重写开始时打开新的 INCR AOF继续记录新写入，子进程生成新的 BASE AOF；成功后父进程生成包含新 BASE 和新 INCR 的临时 manifest，并原子替换生效的 manifest。
- 失败语义也要区分版本：旧流程失败时旧 AOF不被替换；7.0+ 重写失败时，旧 BASE/INCR 加上重写开始时新开的 INCR 仍构成完整可恢复集合。
- “后台重写”不等于无成本：fork/COW、AOF 写入和磁盘 I/O 都可能造成内存与延迟压力。

## 3 分钟版

先说明共同目标：AOF 会随着写操作持续增长，而恢复当前数据集并不需要保留所有已被覆盖的历史命令，所以 Redis 可以从当前内存状态重建一份更短的恢复日志。

对 Redis 7.0 之前的单文件流程，主进程触发重写后 fork 子进程。子进程把 fork 时刻可见的数据集写成新的临时 AOF；父进程继续处理请求，并同时把 fork 后的新写入追加到旧 AOF、记录到重写增量缓冲。这样即使重写失败，旧 AOF仍是安全的。子进程写完后，父进程把增量缓冲追加到新 AOF，随后原子 rename 让新文件替换旧文件，再继续向新 AOF追加。

Redis 7.0 起不再沿用这条单文件合并链路。重写开始时，父进程先打开一个新的 INCR AOF，后续写入直接进入这个增量文件；子进程生成新的 BASE AOF。若重写失败，现有旧 BASE/旧 INCR 与新 INCR 仍可覆盖最新状态。若重写成功，父进程构造并持久化一个临时 manifest，列出新的 BASE 和新的 INCR，然后原子替换当前 manifest，使新集合生效，之后再清理不再使用的旧文件。

运维验证不能只看“命令返回 OK”。重启、备份或故障操作前，应通过 `INFO persistence` 确认 `aof_rewrite_in_progress=0`、`aof_rewrite_scheduled=0`，并检查 `aof_last_bgrewrite_status=ok`。Redis 7+ 备份 AOF 时还要把 `appenddirname` 下的多文件集合视为一个整体；重写进行中直接拷贝目录可能得到无效备份。

## 关键细节

- `BGREWRITEAOF` 命令本身是异步触发入口；如果 RDB 子进程正在持久化，AOF 重写会被调度到其完成之后。
- Redis 7.0 之前的安全性来自“父进程继续写旧 AOF + 保存重写期间增量”，发布前旧文件不被破坏。
- Redis 7.0+ 的关键不变量是 manifest 指向一组可恢复文件；重写期间新写入进入新开的 INCR，因此失败时不会依赖未发布的新 BASE 才能恢复最新状态。
- Redis 7+ 的 BASE/INCR/manifest 是文件组织边界；不要把旧版“把 rewrite buffer 追加到子进程临时文件”的机制套到新版本。
- `INFO persistence` 可观测 `aof_rewrite_in_progress`、`aof_rewrite_scheduled`、`aof_last_bgrewrite_status`、`aof_last_cow_size` 等状态；容量评估还应关注磁盘余量和 fork/COW 峰值。
- `appendfsync` 解决的是 AOF 写入何时同步到稳定存储的问题，不等同于 AOF 重写与发布机制。

## 原理机制

从状态机看，旧版是：`旧 AOF 可恢复` → `fork` → `子进程生成临时 AOF，同时父进程继续写旧 AOF并累计增量` → `子进程完成` → `父进程追加增量` → `原子替换` → `新 AOF 可恢复`。失败发生在替换前时，旧 AOF仍保持可用。

Redis 7.0+ 是：`旧 manifest 指向旧 BASE/INCR 集合` → `父进程创建新 INCR并开始记录后续写入` → `子进程生成新 BASE` → `若失败，旧集合+新 INCR继续覆盖最新状态；若成功，生成临时 manifest` → `原子替换 manifest` → `新 BASE+新 INCR 成为已发布恢复集合` → `清理旧文件`。这里的原子切换对象从“单个 AOF 文件”变成了“描述文件集合的 manifest”。

## 项目经验版

项目映射时只填真实数据：Redis 大版本、AOF 配置、实例内存、写入峰值、fork 耗时、`aof_last_cow_size`、重写耗时、磁盘余量，以及重写前后 `INFO persistence` 状态。没有亲历过生产重写或恢复事故时，明确说“这是依据官方文档的方案推演”，不要虚构故障、职责或指标。

## 常见追问

- 问：为什么 AOF 重写不会简单地“压缩”旧文件？答：因为 Redis 根据当前内存数据集重新生成足以恢复当前状态的命令序列，已被后续操作覆盖的历史命令可以不再保留。
- 问：Redis 7.0 之前重写期间的新写入怎么不丢？答：父进程继续把它们追加到旧 AOF，同时保存在重写增量缓冲；子进程完成后再把增量追加到新文件，发布前旧 AOF一直有效。
- 问：Redis 7.0+ 为什么不需要把同一份 rewrite buffer 再追加到新 BASE？答：重写开始时父进程已经打开新的 INCR AOF，后续写入直接落在这个增量文件；成功时 manifest 发布“新 BASE + 新 INCR”这组恢复集合。
- 问：Redis 7.0+ 重写失败后数据靠什么恢复？答：官方流程保留旧 BASE/旧 INCR，同时重写期间的新写入已经进入新开的 INCR；失败时这些已存在的文件仍构成完整、更新后的数据集恢复链。
- 问：上线或备份前怎么确认重写已经结束？答：检查 `INFO persistence`，至少确认 `aof_rewrite_in_progress` 和 `aof_rewrite_scheduled` 为 0，并确认 `aof_last_bgrewrite_status` 为 `ok`。

## 易错点

- 把 AOF 重写、AOF fsync 和 RDB 快照混为一谈。
- 不声明 Redis 7.0 的 multi-part AOF 边界，把旧版单文件流程说成所有版本都适用。
- 在 Redis 7+ 仍强调旧版 rewrite buffer 追加到新 BASE，忽略新的 INCR+manifest 机制。
- 说“后台重写完全无阻塞/无影响”，忽略 fork、COW 和磁盘 I/O 的资源代价。
- 只看 `BGREWRITEAOF` 返回成功，不检查重写是否仍在进行、是否被调度以及最后一次后台重写状态。
