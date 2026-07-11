<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_thread_states_2db7d11","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"concept","quality_tier":"candidate"} -->
# Java 线程有哪些状态，如何转换？

## 核心结论

Java SE 21 的 `Thread.State` 有六种 JVM 状态：NEW、RUNNABLE、BLOCKED、WAITING、TIMED_WAITING、TERMINATED。它们是 JVM 状态，不等同于操作系统线程状态；排障时尤其不要把 RUNNABLE 简化为“正在占用 CPU”，也不要把 BLOCKED 与 WAITING 混为一谈。

## 1 分钟版

- NEW：尚未启动；`start()` 负责调度执行 `run`，`getState()` 只是竞争快照，外部不能依赖必然先观察到某个固定中间状态。
- RUNNABLE：在 JVM 中执行，也可能等待操作系统资源（例如处理器）。
- BLOCKED：等待进入或重新进入 `synchronized` 关联的 monitor 锁。
- WAITING/TIMED_WAITING：分别是无限期和指定正等待时间的等待；常见来源是 `wait`、`join`、`park`，指定正等待时间的 `sleep`、`wait`、`join`、`parkNanos/parkUntil` 等。
- TERMINATED：`run` 正常完成或异常结束后终止。

## 3 分钟版

六种状态是 `Thread.State` 的完整枚举，一个线程任一时刻只能处于其中一个，且它们不反映操作系统线程状态。`start()` 调度线程执行 `run`；`run` 正常完成，或异常处理结束后，线程到 TERMINATED。

最容易混淆的是 BLOCKED 与 WAITING。BLOCKED 专指等待 monitor 锁进入 `synchronized` 块/方法，或 `wait()` 返回后重新取得该 monitor；它不是所有“被阻塞”的统称。WAITING 是等待其他线程采取动作，常见于无超时 `Object.wait()`、无超时 `join()`、`LockSupport.park()`；TIMED_WAITING 是指定正等待时间的对应等待，例如 `sleep`、带正等待时间的 `wait/join` 和 `parkNanos/parkUntil`。`wait(0)`、`join(0)` 属于无超时等待，不能误判成 TIMED_WAITING。

诊断时先看线程栈和等待对象，再解释状态：大量 BLOCKED 指向 monitor 竞争；大量 WAITING 要继续看是在等谁 `notify`、线程终止还是 permit；RUNNABLE 还需结合 CPU、I/O 和栈帧确认，不能仅凭状态下结论。状态快照用于定位等待关系，不替代死锁检测、超时和取消设计。

## 关键细节

- RUNNABLE 表示在 JVM 中执行，文档明确它仍可能等待处理器等 OS 资源。
- `Object.wait()` 无超时会进入 WAITING；被通知后若要重新进入同步区，还可能等待 monitor 并显示为 BLOCKED。
- `sleep` 不释放已持有的 monitor；它对应 TIMED_WAITING，不能用来解释成“让出锁”。
- `join()` 的语义是等待指定线程终止；无超时或 `join(0)` 是 WAITING，指定正等待时间才是 TIMED_WAITING。
- 本文范围为 Java SE 21 `Thread.State`；它不是 Linux `top` 或 JVM 内部调度器状态的逐一映射。

## 原理机制

线程从 NEW 被 `start()` 调度执行 `run`，运行期间因资源与同步点进入不同 JVM 可观测状态：等待 monitor 是 BLOCKED，等待其他线程动作是 WAITING，指定正等待时间的等待是 TIMED_WAITING。等待条件满足、超时到期或获得 monitor 后，线程回到可执行路径；`run` 正常完成，或未捕获异常处理结束后，线程成为 TERMINATED。状态名称本身只描述等待类别，真正的因果要通过栈帧、锁对象和调用方法确定。

## 项目经验版

项目映射提示：用真实 thread dump 说明线程名、状态、栈顶方法、持有/等待的锁、等待对象及采取的修复动作。没有 dump、指标和复现步骤时，不要凭一个 RUNNABLE/BLOCKED 快照编造 CPU 飙升或死锁结论。

## 常见追问

- 问：BLOCKED 与 WAITING 的根本区别？答：BLOCKED 等 monitor 锁；WAITING 等另一线程的特定动作，两者的触发 API 与排查对象不同。
- 问：RUNNABLE 一定在跑 CPU 吗？答：不一定；Java SE 21 说明它可能在等待处理器等 OS 资源，需要结合栈与 CPU 指标判断。
- 问：`sleep` 后锁会自动释放吗？答：不会；sleep 只造成带时限等待，不能替代 `wait` 的 monitor 协作语义。
- 问：为什么 `wait` 返回后可能又 BLOCKED？答：wait 返回后要重新进入同步块/方法，若 monitor 尚不可得就等待该锁。

## 易错点

- 不要把六种 JVM 状态当作 OS 线程状态的完整映射。
- 不要把 BLOCKED 说成所有锁等待；它在该枚举中专指 monitor 锁等待。
- 不要把 WAITING 说成死锁结论；它可能只是正常的 join、park 或 wait 协作。
- 不要把 RUNNABLE 直接等同于 CPU 饱和或 sleep 等同于释放锁。
