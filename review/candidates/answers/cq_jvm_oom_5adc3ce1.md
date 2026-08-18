<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_jvm_oom_5adc3ce1","version":4,"status":"draft","updated_at":"2026-08-18","answer_type":"scenario","quality_tier":"candidate"} -->

# JVM OOM 如何定位和处理？

## 核心结论

JVM 出现 OOM 时，第一步不是直接“加大 `-Xmx`”，而是先确认**到底是哪一种资源耗尽**，再按资源类型留证、止损和定位：

- `Java heap space` / `GC overhead limit exceeded`：优先看 Java 堆、对象存活集、分配速率和 GC 行为；
- `Metaspace`：优先看类加载数量、ClassLoader 生命周期和 Metaspace 使用；
- `unable to create native thread`、进程 RSS 接近容器/主机上限、容器 `OOMKilled`：优先看 native memory、线程数、容器限制和宿主机证据；
- 只有确认是**容量不足**而不是**持续增长的泄漏**后，扩容才是根治方案的一部分。

线上处理要同时满足两个目标：**尽快恢复 API/SLO**，以及**在重启或扩容前尽量保留可复盘证据**。OOM 往往会让进程本身连分配诊断缓冲区都困难，因此 heap dump、JFR、GC 日志、NMT、容器/节点监控等证据应尽可能在事故前就配置好，而不是出事后才临时开启。

## 1 分钟版

1. **确认现象**：保留完整 OOM 文本、JDK 版本和 JVM 参数，同时看容器 limit、RSS、`-Xmx`、Metaspace、Direct/Native memory、线程数、GC 指标，先区分 heap / metaspace / native / thread / container OOM。
2. **先止损**：把异常实例摘流或限流，必要时扩容健康实例；若业务 API 会因为重试或重启重放请求，先确认写操作有幂等键、事务边界或补偿机制，避免 OOM 事故演变成重复扣款/重复写入等一致性事故。
3. **保留证据**：heap OOM 预先启用 `-XX:+HeapDumpOnOutOfMemoryError` 并配置有足够磁盘空间的 `-XX:HeapDumpPath`；持续保留 GC 日志和低开销 JFR。需要 native 维度时，NMT 必须在 JVM 启动时用 `-XX:NativeMemoryTracking=summary|detail` 开启。
4. **按类型定位**：heap 看 `GC.class_histogram`、heap dump 的 dominator/retained size、Full GC 后 live set 是否持续增长；Metaspace 看 ClassLoader；native 看 NMT baseline/diff、线程栈、RSS 与 heap 的差值，同时记住 NMT 不覆盖任意第三方 native 分配。
5. **修复并验证**：泄漏就修引用生命周期/缓存无界增长/ClassLoader/native 资源释放；容量不足则按峰值请求量、并发、单请求存活对象和缓存规模重新做容量估算。灰度后用压测和线上指标验证内存平台期、GC、延迟、成功率和 SLO，再恢复全部流量。

## 3 分钟版

我会把线上 OOM 处理成“分类 → 止损 → 留证 → 定位 → 修复 → 回归验证”六步，而不是把所有 OOM 都当成 Java heap 不够。

| 现象 | 优先证据 | 常见假设 | 处理方向 |
| --- | --- | --- | --- |
| `Java heap space` | heap dump、class histogram、GC/JFR、Full GC 后 live set | 内存泄漏、无界缓存、单次大对象、峰值容量不足 | 找 retained path / 增长对象；修生命周期或重新估算 heap |
| `GC overhead limit exceeded` | GC 日志、JFR、heap dump | 堆接近耗尽，GC 花大量时间但回收很少 | 先确认 live set 与分配速率，再区分泄漏和容量不足 |
| `Metaspace` | class count、ClassLoader、`VM.metaspace`、NMT | 动态生成类过多、ClassLoader 泄漏、Metaspace 上限过小 | 找不能卸载的 ClassLoader 或重新评估上限 |
| `unable to create native thread` | OS/容器线程限制、线程 dump、RSS、NMT | 线程池失控、线程栈和 native memory 不足、PID/ulimit 限制 | 收敛线程模型/池大小并保留 native headroom |
| 容器 `OOMKilled` 但 Java heap 未打满 | 容器事件、RSS、heap、NMT、direct/native 指标 | `Xmx` 之外的 Metaspace、线程栈、code cache、direct buffer、JNI/第三方 native 占用 | 给非 heap 留安全余量；继续追踪 NMT 覆盖与未覆盖部分 |

### 事故现场怎么做

假设一个 8 GiB memory limit 的 Java Pod，`-Xmx6g`，高峰 1000 QPS。告警显示 RSS 已到 7.8 GiB，而 old-gen 在 Full GC 后稳定在 4.5 GiB，这时我不会因为“还有 1.5 GiB heap 空间”就排除内存问题，也不会直接把 `Xmx` 调到 7.5 GiB。JVM 还需要 Metaspace、线程栈、code cache、GC/JIT 结构、direct/native memory；容器看的是整个进程内存，不只 Java heap。

事故控制流应独立于业务核心流：**监控告警 → 摘除/限流异常实例 → 捕获已有证据 → 必要时滚动重启 → 诊断 → 修复 → canary → 恢复流量**。如果系统有数据库或缓存写入，重启前还要评估 in-flight 请求：下游写接口必须依赖幂等键、唯一约束、事务或可补偿语义来防止重试产生重复副作用。不要为了“释放内存”而盲目清数据库/缓存，这可能破坏一致性且掩盖真正的泄漏。

### 怎么判断“泄漏”还是“容量不足”

不要只看某一时刻“heap 用了多少”，而要看趋势：

- 在相似请求量下，Full GC 后的 live set 是否一轮比一轮高；
- 相同业务窗口内，某些 class 的实例数/retained size 是否单调增长；
- 请求量下降后，内存是否回不到原来的平台；
- 缓存、队列、批处理或大结果集的增长是否与业务规模一致；
- native 维度下，NMT baseline 与后续 `summary.diff/detail.diff` 是否持续增长；如果进程 RSS 在涨但 NMT 基本不涨，要继续检查 NMT 覆盖不到的第三方 native/JNI 等来源。

容量不足则要回到规模模型。例如峰值 1000 QPS、平均 200 ms 在途时间，粗略并发约 200；如果一次请求链路平均维持 500 KiB 的 live object，仅在途请求就可能贡献约 100 MiB live data。这个估算还没有算缓存、连接池、队列、框架对象和安全余量，所以最终应以压测与 JFR/heap 实测校准，而不是只用公式拍 `Xmx`。

## 关键细节

### 1. 证据要在事故前准备

生产环境建议至少准备：

- `-XX:+HeapDumpOnOutOfMemoryError` 和明确的 `-XX:HeapDumpPath`，并监控目标磁盘空间；
- GC 日志；
- 持续 JFR（使用与当前 JDK 相匹配的配置）；
- heap、RSS、Metaspace、线程数、GC pause/频率、分配速率、容器 memory limit/OOMKilled 等监控与告警；
- 如果需要追踪 HotSpot native memory，在启动参数中启用 NMT，之后用 `jcmd <pid> VM.native_memory baseline` 和 `summary.diff/detail.diff` 做差分。

`HeapDumpOnOutOfMemoryError` 不能替代所有 OOM 诊断。Oracle 的 `java` 工具规范明确说明，它针对 Java heap exhaustion；像 native thread creation 这类其他资源耗尽不能指望自动得到 heap dump。

### 2. `jcmd` 本身也有代价

`jcmd <pid> GC.class_histogram` 和 `GC.heap_dump` 都可能对大堆产生明显停顿，官方将其标为 High impact。线上是否执行，要结合剩余容量、流量和 SLA 决策，必要时先摘流。诊断命令不是“免费读操作”。

### 3. NMT 有边界

NMT 默认关闭，必须在 JVM 启动时开启；它适合分析 HotSpot/JVM 自身 native memory 的分类和趋势，但不覆盖任意第三方 native code/JDK class library 的全部分配。所以“RSS 变大 + NMT 没变”不能推出“没有 native leak”。

### 4. dump/JFR 是敏感数据

heap dump、JFR 可能包含请求参数、Token、用户数据和业务对象。证据文件应写到受限目录，并放入有权限控制、加密和保留期策略的存储，不能通过普通诊断 API 直接暴露给公网，也不应长期散落在 Pod 临时盘。

### 5. `Xmx` 不是容器内存上限

容器 limit 要覆盖 heap 之外的所有进程内存。即使业务主要在 heap 内运行，也应为 Metaspace、线程栈、direct buffer、code cache、JVM native structures 和不可预期峰值保留余量。正确比例必须用实际负载测，而不是固定套一个百分比。

## 原理机制

OOM 的本质是 JVM 或其所在进程无法满足某类新的资源分配请求，但“资源”并不只有 Java heap。

对于 heap leak，典型链路是：对象持续被 GC Root 可达引用持有 → Full GC 之后仍不能回收 → live set 逐步抬高 → 可分配空间越来越少 → GC 更频繁、停顿加重 → 最终抛出 OOM。heap dump 的关键不是“哪个 class 最大”这么简单，而是找对象为什么仍可达：谁在持有它、retained size 多大、生命周期为什么超过业务预期。

Metaspace 位于 native memory，用来保存类元数据。动态类生成、频繁创建且不能卸载的 ClassLoader 都可能让它增长。线程也消耗 native 资源；线程数量失控不仅有调度成本，还会占用栈和 OS 线程资源。因此同一个 `OutOfMemoryError` 家族，需要针对实际资源池诊断。

重启能清掉进程内存，所以往往能让服务暂时恢复，但如果触发条件仍存在，增长曲线会重复。是否算“修复”，要看灰度后同等请求量和相同时间窗口内，内存是否进入稳定平台，而不是只看重启后瞬间下降。

## 项目经验版

以下是方法论和**假设性事故样例，不代表真实个人事故经历**。生产环境应预先建立 OOM runbook，并把诊断能力放在观测/运维边界，而不是业务 Controller 里临时塞一个 `/dumpHeap` 接口。

假设某 Java 服务在 8 GiB Pod 中运行，连续三天每天晚高峰后 RSS 增长 300–500 MiB，但 heap Full GC 后稳定。处置时先将高风险实例摘流，保存 JFR、GC 日志、容器 RSS 和 NMT baseline/diff，再对比线程数、Metaspace、NMT 分类。如果 NMT 的 Thread/Metaspace/Code 等分类也稳定，而 RSS 仍持续增长，就把排查范围转到 direct buffer、JNI/第三方 native 库和 OS 级证据，而不是继续围着 heap dump 转。

如果最终发现是无界业务缓存导致 heap live set 随 key 数量增长，就修缓存容量/TTL/淘汰策略，并给 key 数、hit rate、eviction、heap live set 建监控；如果发现只是促销把请求量和 in-flight object 推高，则基于真实分配率、并发和 GC 目标重新做容量规划。两类问题的“看起来都是内存满了”，修法完全不同。

修复后要做回归：

1. 用接近生产的请求量和数据分布压测；
2. 至少跑过足以覆盖原来泄漏增长周期的时间窗口；
3. 检查 heap live set、RSS、Metaspace、线程、allocation rate、GC pause/throughput 是否稳定；
4. 验证业务 API 的 P95/P99 延迟、成功率和 SLO；
5. 做一次可控重试/滚动重启验证，确认事务、幂等和补偿不会造成重复副作用；
6. 确认证据存储和告警仍可用，避免“修好了业务，却把下次诊断能力删掉”。

## 常见追问

### 1. OOM 后第一反应要不要重启？

如果服务已经不可用，重启可能是必要止损，但尽量先获取已经自动落盘的 dump/JFR/GC/容器证据。不要为了留证无限拖延恢复；正确做法是提前配置自动证据，使“恢复”和“复盘”不冲突。

### 2. Heap dump 很大，线上还能不能导？

能不能导取决于实例剩余资源和 SLA。`jcmd GC.heap_dump` 是高影响操作，大 heap 下可能造成明显停顿；高流量实例应先摘流、确认磁盘，并避免把 dump 写满文件系统。

### 3. `jmap -histo` / `jcmd GC.class_histogram` 看到 byte[] 最大，就是 byte[] 泄漏吗？

不是。`byte[]`、`char[]` 往往只是实际业务对象的底层载体。要继续沿引用链、retained size 和业务 owner 找到“谁在长期持有这些数组”。

### 4. 把 `-Xmx` 调大就能解决吗？

如果确认是合理峰值容量不足，可以；如果是泄漏，只是延后爆炸。容器场景还必须考虑 `Xmx` 之外的 native/Metaspace/thread/direct/code cache 等空间，盲目接近容器 limit 反而可能更容易被 OOMKilled。

### 5. NMT 能找到所有 native leak 吗？

不能。NMT 主要追踪 HotSpot/JVM 的 native memory；官方明确指出第三方 native code 等分配不在完整覆盖范围内。它是缩小范围的证据，不是唯一真相源。

### 6. 怎么给监控定阈值？

不要只设“heap > 80%”这一条。至少把 Full GC 后 old-gen/live set 趋势、RSS 与容器 limit 距离、Metaspace、线程数、GC pause、allocation rate、OOMKilled、请求成功率与延迟联合起来。阈值应来自压测和历史基线，并围绕 SLO 留出处理窗口。

## 易错点

- 看到 OOM 就直接增大 heap，没有先区分 heap、Metaspace、native、thread、container；
- 事故后才想起配置 heap dump/JFR/NMT，结果关键证据拿不到；
- 把一次 heap 快照当成泄漏结论，没有做时间序列、Full GC 后 live set 或 baseline/diff 对比；
- 只看 `-Xmx` 不看进程 RSS 和容器 limit，忽略非 heap 内存；
- 认为 NMT 覆盖所有 native 分配，导致第三方 native/JNI 泄漏漏诊；
- 在高流量实例上直接跑高影响 `GC.heap_dump` / histogram，不考虑暂停、磁盘和 SLO；
- OOM 后重启导致请求重试，却没有幂等、事务或补偿，内存事故叠加数据一致性事故；
- 把 dump/JFR 暴露在普通 API 或不受控存储中，制造敏感数据泄露风险；
- 修复后只看“没有再 OOM”，不验证相同请求规模下内存平台、GC、延迟、成功率和告警是否恢复正常。