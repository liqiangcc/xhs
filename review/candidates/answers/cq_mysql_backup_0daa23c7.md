<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_mysql_backup_0daa23c7","version":2,"status":"draft","updated_at":"2026-08-18","answer_type":"mechanism","quality_tier":"candidate"} -->
# MySQL 备份与基于 binlog 的恢复流程

## 核心结论

可靠的 MySQL 时间点恢复（PITR）是一个可证明的状态链：**一致的全量备份 + 与该备份对应的 binary-log 坐标 + 从该坐标起连续可用的 binlog + 明确的停止事件边界 + 恢复演练**。恢复时先把隔离实例还原到备份状态，再按 binlog 顺序重放到误操作前已确认的 event position。最容易出错的不是 `mysqlbinlog` 命令本身，而是备份并不一致、备份坐标与数据快照不对应、日志链缺段，或把不受事务一致性保护的表与并发 DDL 当成普通 InnoDB 一样处理。

## 1 分钟版

- **先拿到一致基线。** 物理备份偏向大库和快速恢复，逻辑备份偏可移植与细粒度；在线备份必须选择能保证一致性的锁或快照机制。
- **InnoDB 逻辑备份可用事务快照。** MySQL 8.4 的 `mysqldump --single-transaction` 在 `REPEATABLE READ` 下从一次一致性事务快照读取 InnoDB，正常 DML 可以继续，但它只保证 InnoDB 一致；MyISAM/MEMORY 等非事务表可能继续变化。
- **坐标必须与基线绑定。** 对 InnoDB，`--source-data --single-transaction` 可在开始阶段短暂取得全局读锁、读取 binary-log 坐标后释放，再无表锁地继续 dump；不要拿“备份文件完成时间”替代坐标。
- **PITR 再按连续 binlog 推进。** 从基线记录的文件/position 之后重放，时间筛选只用于定位事故附近事件，最终按经过审阅的 start/stop position 应用。
- **并发 DDL 是边界。** `ALTER/CREATE/DROP/RENAME/TRUNCATE TABLE` 在 `--single-transaction` dump 期间可能让内容或 binary-log 坐标失效；需要冻结这类变更或改用能提供相应一致性保证的备份方案。

## 3 分钟版

先说明恢复模型。全量备份给出状态 `S0`，binary log 记录之后的数据变化；MySQL 8.4 官方把 PITR 定义为先恢复全量备份，再把备份之后的 binary-log 事件增量应用到更近的目标点。于是一个真正可恢复的“基线”必须同时有两部分：**数据快照**和**与这个快照一致的日志坐标**。只知道备份任务几点结束，不足以证明从哪一个事件开始重放。

备份方式首先按恢复目标选。物理备份是数据文件的原始副本，适合大且需要快速恢复的数据库；逻辑备份保存 DDL 和数据表示，恢复更慢但更便于查看、编辑和跨机器迁移。在线备份不等于天然一致：MySQL 8.4 的备份类型文档明确要求运行中的数据库使用适当锁或工具机制，避免并发修改破坏备份完整性。

以常见的 InnoDB `mysqldump` 为例，`--single-transaction` 会设置 `REPEATABLE READ` 并在 dump 前开始事务，因此它能在不长期锁表的情况下导出 InnoDB 在事务起点的一致状态。若同时需要 PITR 起点，官方 8.4 文档给出的 `--source-data --single-transaction` 流程会在 dump 开始时短暂取得全局读锁，读取 binary-log 坐标后立即释放；随后 InnoDB dump 可以继续而普通读写不被长期表锁阻塞。这个“短锁拿坐标 + 一致性事务快照”正是数据基线与日志起点对齐的关键。

但边界必须一起说。第一，`--single-transaction` 只保证 InnoDB 等事务表的一致状态，MyISAM/MEMORY 等非事务表在 dump 过程中仍可能变化；如果混用引擎，要使用适当锁、物理/专用备份工具或把这类表纳入单独一致性方案。第二，在 single-transaction dump 期间，其他连接执行 `ALTER TABLE`、`CREATE TABLE`、`DROP TABLE`、`RENAME TABLE`、`TRUNCATE TABLE`，官方文档明确说可能让 dump 的表内容或 binary-log 坐标不正确，甚至使查询失败。因此备份窗口应冻结这些 DDL 或使用能够处理相应并发变更的产品/流程。

恢复阶段再从 `S0` 向前推进。确认备份记录的 binlog 文件和 position，恢复到隔离实例，确认从该点到目标事故前的 binlog 文件连续存在；用 `mysqlbinlog` 的时间选项定位事故附近事件，再检查实际 event position，最后从基线坐标之后按文件顺序重放，在误操作前的 stop position 停止。MySQL 官方 position 示例强调，用时间范围做“定位”，再用 position 做“应用”更可靠。重放会重新执行 binlog 代表的数据修改，所以不能直接拿未经检查的区间对生产执行。

验收不是“命令退出码为 0”。应校验关键表行数/校验和、约束、业务不变量、目标事件是否被包含或排除、应用连接与只读验证；同时记录实际恢复耗时、最老可恢复点、binlog 缺段检测和演练结果。RPO/RTO 是部署和演练结果，不是 MySQL 文档给出的通用常数。

## 关键细节

- MySQL 8.4 默认启用 binary logging，但真实部署仍应核对 `SHOW BINARY LOGS`、`SHOW BINARY LOG STATUS`、保留策略和备份产物，而不是只相信默认值。
- `mysqldump --single-transaction` 的一致性来源是事务快照；它适用于 InnoDB 这类事务表，不是所有 storage engine 的通用一致性开关。
- `--source-data --single-transaction` 在开始阶段短暂取得全局读锁以读取 binary-log 坐标，然后释放；长时间运行的更新可能让这个初始锁等待，因此备份窗口要观察锁等待和业务延迟。
- single-transaction dump 期间要禁止对被备份表执行 `ALTER/CREATE/DROP/RENAME/TRUNCATE TABLE`，否则表内容或 binary-log 坐标可能不正确，甚至 dump 失败。
- 物理在线备份同样必须使用工具定义的锁/一致性机制；直接在运行中的数据目录复制文件不能自动等价于一致快照。
- `mysqlbinlog` 可以按时间或 position 选择事件区间；事故恢复应先定位事件，再用明确的 position 边界重放。
- binlog 缺段、起点坐标不可信、终点误包含事故事务，任一项都足以让 PITR 失去可证明性。
- binary log 记录数据库变化并用于恢复；对于非事务表，修改不能靠普通事务回滚恢复，因此更要把引擎类型和备份一致性策略纳入演练。

## 原理机制

把恢复抽象成状态机：

`取得一致备份 S0 + 记录匹配的 binlog 坐标 P0`
→ `保存并验证 S0 / P0`
→ `持续归档 P0 之后的连续 binlog`
→ `事故时在隔离环境恢复 S0`
→ `从 P0 后逐事件重放`
→ `在事故前确认的 stop position P1 停止`
→ `校验得到目标状态 St`
→ `受控切流或导出修复数据`。

这里每个箭头都有不变量。`S0` 与 `P0` 必须描述同一个一致时间边界；日志链不能缺段；`P1` 必须落在不希望重放的事件之前；恢复验证必须证明 `St` 满足业务不变量。`--single-transaction` 解决的是 InnoDB 逻辑备份的一致读，不解决非事务表和并发 DDL；binlog 解决的是增量变化，不替代全量备份；position 解决的是精确重放边界，不替代事件内容审阅。

资源成本也要明确：逻辑 dump/restore 会消耗 CPU、网络、SQL 重放和索引构建时间；物理备份更占文件传输与存储，但通常恢复更快；binlog 长期保留占磁盘/对象存储；短暂全局读锁可能等待长更新；隔离演练需要额外实例和验证时间。这些成本换来的是可验证的恢复链。

## 项目经验版

项目映射时只填真实事实：MySQL 大版本、storage engine 分布、全量备份工具与参数、是否使用 `--single-transaction`/`--source-data`、备份频率、备份坐标保存位置、binlog 保留期、最近一次恢复演练、实测 RPO/RTO、校验项和切换/回滚责任人。

如果库里混有 MyISAM/MEMORY 或备份窗口仍允许 DDL，必须单独说明如何保证这些对象的一致性；如果没有演练过，就明确说这是“依据 MySQL 官方机制设计的恢复流程”，不要虚构生产恢复记录或指标。

## 常见追问

- **问：为什么全量备份不能单独完成误删后的时间点恢复？** 答：它只能回到基线；基线之后到目标点的变化要靠连续 binlog 推进。
- **问：`--single-transaction` 是否意味着备份期间什么都不用管？** 答：不是。它能为 InnoDB 提供一致事务快照，但非事务表仍可能变化，而且并发 `ALTER/CREATE/DROP/RENAME/TRUNCATE TABLE` 会破坏 dump 的内容或坐标正确性。
- **问：怎样让备份和 binlog 起点对应？** 答：MySQL 8.4 文档给出的 InnoDB 逻辑备份方案可用 `--source-data --single-transaction`：开始时短暂全局读锁读取 binary-log 坐标，随后释放锁并继续一致性事务 dump。
- **问：为什么不直接按时间参数重放？** 答：时间参数适合快速定位事故附近事件；官方 position 恢复示例建议审阅真实 event position 后，用 start/stop position 精确应用，减少漏事件或包含误操作的风险。
- **问：binlog 文件少一段还能算 PITR 吗？** 答：不能证明能恢复到跨过缺口的状态；需要更早的完整基线、补齐日志链或接受更大的数据损失边界。
- **问：可以直接把 `mysqlbinlog` 输出打到生产吗？** 答：不应作为默认流程。重放会重新执行数据修改，应先在隔离环境验证基线、日志链、stop position 和结果，再受控切换或提取修复数据。

## 易错点

- 不要把“备份任务成功”当作“备份可恢复”；没有一致性证明、坐标、日志链和演练，就没有完整恢复证据。
- 不要把备份完成时间当作 binary-log 起点；使用备份工具输出的匹配坐标或等效可证明位置。
- 不要说 `--single-transaction` 能保证所有引擎一致；官方只保证 InnoDB 等事务表，MyISAM/MEMORY 仍可能变化。
- 不要忽略备份期间的并发 DDL；它可能使 table contents 或 binary-log coordinates 不正确。
- 不要只保留 binlog 而没有可用全量基线，也不要只留全量基线而没有连续增量。
- 不要编造固定 RPO/RTO；它们必须来自真实保留策略、基础设施和恢复演练。
