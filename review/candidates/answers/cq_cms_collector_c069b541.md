<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_cms_collector_c069b541","version":4,"status":"draft","updated_at":"2026-08-18","answer_type":"mechanism","quality_tier":"candidate"} -->
# CMS 垃圾收集器的执行流程及 STW 阶段

## 核心结论

CMS（Concurrent Mark Sweep）是 HotSpot 历史上的低停顿老年代收集器：它把大部分可达性追踪和清扫与应用线程并发执行，但**并不是无 STW**。在 Oracle JDK 8 的 CMS 周期里，初始标记（initial mark）和重新标记（remark）会暂停应用线程；两者之间进行并发追踪，remark 之后并发清扫。CMS 还要为并发阶段让出 CPU 和老年代空间余量；如果并发回收来不及完成，可能发生 concurrent mode failure。版本边界必须一起回答：CMS 已在 JDK 14 被移除，现代 JDK 不能再把它当作可选收集器。

## 1 分钟版

- **Initial Mark：STW。** 暂停应用线程，标记从 GC Roots 等位置直接可达的对象，然后恢复应用。
- **Concurrent Mark / Preclean：并发。** GC 线程沿可达对象图继续追踪，并提前重新检查并发期间被修改的区域；应用线程同时运行，因此停顿更短，但会争用 CPU。
- **Remark：STW。** 再次暂停应用线程，补齐并发追踪期间由于引用更新而可能遗漏的可达对象。
- **Concurrent Sweep / Reset：并发。** 回收已判定不可达的对象，把空间归还到 free lists，并为下一轮准备；如果老年代在完成前耗尽或空闲块无法满足分配，可能发生 concurrent mode failure，转入全停顿完成路径。
- **版本边界。** JDK 8 仍可用 `-XX:+UseConcMarkSweepGC`；OpenJDK JEP 363 在 JDK 14 移除了 CMS 及其专用选项。

## 3 分钟版

回答 CMS 最容易错在只背“初始标记 → 并发标记 → 重新标记 → 并发清除”四个词，却没有解释为什么只有部分阶段能并发。

第一步 initial mark 需要一个稳定窗口来确定根直接可达对象，所以会 STW。随后 concurrent mark 沿对象图追踪；这段时间应用仍在修改引用，因此 GC 得到的是一个不断变化的对象图。Oracle JDK 8 文档描述了并发 retrace/preclean，并在 remark 时暂停应用，重新检查自上次检查后可能发生变化的 roots 和对象图，收敛最终存活集合。remark 完成后，CMS 可以与应用并发地 sweep 不可达对象，并把回收空间交还给 free lists。

并发的代价有三类。第一是 **CPU 竞争**：并发 GC 线程会占用本可供业务使用的处理器资源，所以“低停顿”不等于“没有吞吐损失”。第二是 **空间余量**：应用在并发回收期间仍可能继续分配，CMS 必须足够早启动，争取在老年代耗尽前完成。第三是 **floating garbage**：已经被追踪为存活、但在本轮结束前又变成不可达的对象，可能留到下一轮才回收。

因此调优时不能只盯某一次 STW。要把 initial-mark、remark、concurrent-mark/preclean/sweep 的耗时、老年代占用增长速度、concurrent mode failure，以及与 young GC 相邻造成的连续停顿一起看。Oracle JDK 8 还说明 CMS 会根据历史估算选择启动时机，并允许通过 initiating occupancy 控制触发；具体默认阈值会随版本变化，不应脱离 JDK 版本背固定数字。

最后补版本边界：JEP 363 明确在 JDK 14 移除 CMS，使用 `UseConcMarkSweepGC` 会被忽略并继续使用默认收集器。因此这道题属于理解旧 HotSpot GC 机制和迁移背景的历史题；新系统选型应基于实际 JDK 支持的收集器，而不是继续给 CMS 参数。

## 关键细节

- CMS major cycle 的两次核心停顿是 initial mark 和 remark；young generation collection 与 CMS 老年代周期相互独立，minor collection 也会暂停应用线程，因此日志上可能出现相邻停顿。
- remark 的目的不是“重新做一遍完整标记”，而是处理并发追踪期间引用变化导致的遗漏，并收敛可达性结果。
- preclean 属于 Oracle JDK 8 CMS 的并发准备阶段；面试可以说“经典四阶段 + 实现/日志中的 preclean/reset”，避免把教学简化模型误当成完整运行日志。
- CMS 的 concurrent sweep 把不可达对象回收到 free lists。发生分配失败时要看“是否有可满足该分配的空闲块”，不能只看一个总空闲字节数。
- concurrent mode failure 的关键是“并发周期没有在老年代压力越界前完成或可用空闲块不能满足分配”，它会把低停顿目标打回更重的全停顿路径。
- floating garbage 是并发可达性追踪的自然代价之一：本轮曾被认为可达、后来才变成不可达的对象可能等到下一轮回收。
- JDK 14 之后 CMS 已被移除；回答任何 CMS flag、日志格式或默认阈值，都应先注明对应的历史 JDK 版本。

## 原理机制

CMS 的核心交换是“用并发工作换停顿时间”。Initial mark 先建立一个可追踪起点；concurrent mark 把最重的对象图遍历与业务执行重叠；preclean/remark 处理并发期间发生的引用变化，其中 remark 用 STW 获得稳定窗口；concurrent sweep 再把不可达对象回收到可分配空间。因为应用在并发阶段没有停止，GC 同时承担 CPU 竞争、引用变化和老年代继续增长三个压力，所以 CMS 必须保留足够 headroom，并监控并发周期能否在空间耗尽前结束。

## 项目经验版

如果维护的是仍使用 CMS 的旧 JDK 系统，先确认**真实 JDK 版本和实际 GC**，再基于 GC 日志回答：initial-mark/remark 的停顿分位数是多少、并发阶段持续多久、老年代在周期内增长多快、有没有 concurrent mode failure、young GC 是否与 remark 紧邻。只有这些证据齐全，才讨论是否需要调整启动时机或迁移。

如果是现代 JDK 项目，不应为了回答旧面试题伪造“线上仍在调 CMS”。应直接说明 CMS 已从 JDK 14 移除，再把问题转成“为什么历史上 CMS 能降低停顿、代价是什么、迁移后如何用当前收集器和日志重新验证 SLO”。

## 常见追问

- **问：CMS 哪些阶段 STW？** 答：经典 CMS 老年代并发周期中，initial mark 和 remark 是两次核心 STW；此外 young GC 有自己独立的 STW，不能混成“CMS 只有两次暂停整个 JVM 生命周期”。
- **问：为什么 remark 还要停顿？** 答：因为 concurrent mark 时应用仍在修改引用，需要在稳定窗口里重新检查并发期间可能变化的 roots/对象图，补齐遗漏。
- **问：什么是 floating garbage？** 答：并发追踪时曾被认为可达，但之后才变成不可达、来不及在本轮回收的对象；它们通常留到后续周期处理。
- **问：什么会触发 concurrent mode failure？** 答：并发回收没有在老年代耗尽前完成，或当前可用空闲块无法满足分配时，会进入更重的全停顿完成路径。
- **问：JDK 17/21 还能开 CMS 吗？** 答：不能。OpenJDK 在 JDK 14 已移除 CMS；CMS 专用选项也被移除/废弃处理，应该使用该 JDK 实际支持的收集器。
- **问：CMS 默认多少占用率启动？** 答：先说版本。Oracle JDK 8 文档给过约 92% 的历史默认描述，同时明确该值可能随 release 改变；工程上应以运行 JDK 的文档、flags 和日志为准，不背成跨版本常量。

## 易错点

- 不要说“CMS 全程并发、完全没有 STW”。
- 不要把教学用四阶段列表当作完整实现阶段；JDK 8 日志还能看到 preclean、reset 等阶段。
- 不要把“并发”解释成免费：它以 CPU、额外空间余量和更复杂的并发可达性处理换停顿。
- 不要把 concurrent mode failure 简化成单一“老年代 100% 才发生”；Oracle 文档还明确包含可用 free-space blocks 不能满足分配的情况。
- 不要在现代 JDK 上继续给出 CMS 调参方案而不说明 JDK 14 移除边界。
