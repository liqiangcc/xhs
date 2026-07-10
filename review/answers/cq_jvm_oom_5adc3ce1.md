<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_jvm_oom_5adc3ce1","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# JVM OOM 如何定位和处理？

## 核心结论

OOM 不是“堆不够”的同义词。先按错误消息区分 Java heap、Metaspace、Direct buffer、unable to create native thread 等区域，再止血、保留证据、分析增长来源，最后修复泄漏或容量模型。

## 1 分钟版

- 先确认时间点、错误类型、容器是否 OOMKilled、GC/堆/进程内存和流量变化。
- 预先配置 `HeapDumpOnOutOfMemoryError`、dump 路径和 GC 日志，磁盘与权限必须可用。
- 堆 OOM 用 histogram/dump 查 dominator、retained size 和 GC roots；原生内存结合 NMT、线程数、direct buffer 和容器指标。
- 先限流、摘流量、扩容或重启止血，但重启前尽量留存 dump、日志、线程栈和配置。

## 3 分钟版

Java heap space 要判断是业务峰值容量不足、无界缓存/队列，还是对象无法回收；频繁 Full GC 后占用仍高更像泄漏。Metaspace 常与动态生成类、ClassLoader 泄漏有关。Direct buffer memory 要检查 Netty/直接缓冲区上限与释放；native thread OOM 要核对线程池失控、每线程栈和系统 pid/内存限制。容器中 RSS 包括堆外、线程栈、代码缓存和本地库，不能只看 `-Xmx`。修复后用相同流量模型回归，验证对象增长斜率、GC 停顿和水位，而不是仅把内存调大。

## 关键细节

- heap dump 会产生大文件和停顿风险，路径需容量充足并保护敏感数据。
- `jmap -histo:live` 等 live 操作可能触发 Full GC，线上执行需评估。
- NMT 需在 JVM 启动时启用，不能事后凭空获得完整基线。
- Kubernetes OOMKilled 可能由 cgroup 直接终止，未必来得及抛 Java OOM。

## 原理机制

定位链路是“错误分区 → 时间序列 → 对象/原生内存归因 → GC Root 或分配路径 → 最小复现”。保留基线与故障快照的差异，比只看一次类实例排行榜更可靠。

## 项目经验版

项目映射提示：真实案例需填写内存曲线、触发流量、证据文件、最大保留对象链、止血动作、代码修复和回归结果。没有真实事故时只描述演练流程，不虚构根因。

## 常见追问

- 问：OOM 后能直接重启吗？答：可先止血，但若条件允许应先保留 dump、日志和线程栈，否则根因证据会丢失。
- 问：把 Xmx 调大能解决吗？答：只能缓解真实容量不足；泄漏会再次耗尽，还可能增加 GC 和 dump 成本。
- 问：为什么堆没满进程也被杀？答：RSS 还包括堆外、线程栈等，容器 cgroup 限制也可能先触发 OOMKill。
- 问：怎么看 ClassLoader 泄漏？答：检查大量重复类加载器及其 retained path，寻找线程、ThreadLocal、缓存或静态引用阻止卸载。

## 易错点

- 不要在未区分 OOM 类型时只分析堆。
- 不要在线上无评估执行可能长时间 STW 的诊断命令。
- 不要把重启和扩容当成根因修复。
- 复习反馈：第一步按报错与进程退出方式分流 Java heap、Metaspace、DirectBuffer、native thread 和 cgroup OOMKilled，再选择证据工具。
