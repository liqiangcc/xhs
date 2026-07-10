<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_thread_states_2db7d11","version":1,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# Java 线程有哪些状态，如何转换？

## 核心结论

Java `Thread.State` 有 NEW、RUNNABLE、BLOCKED、WAITING、TIMED_WAITING、TERMINATED 六种；它是 JVM 视角的状态，不与操作系统线程状态一一对应。

## 1 分钟版

- 创建未启动是 NEW，调用 `start()` 后进入 RUNNABLE，既包含正在 CPU 上运行，也包含可运行等待调度。
- 争抢 `synchronized` monitor 失败进入 BLOCKED。
- `Object.wait`、`join`、`LockSupport.park` 等无期限等待进入 WAITING；带超时版本、`sleep` 进入 TIMED_WAITING。
- 获得 monitor、收到通知/许可、超时或被中断后会回到可竞争/可运行路径；`run` 正常结束或抛出未捕获异常后 TERMINATED。

## 3 分钟版

状态排查要结合线程栈中的具体阻塞点。大量 BLOCKED 通常指向 monitor 竞争；`WAITING (parking)` 常见于 AQS 锁、线程池空闲工作线程或队列等待，不等于死锁；`TIMED_WAITING` 可能只是正常定时任务。`wait()` 会释放当前对象 monitor 并在被通知后重新竞争，`sleep()` 不释放已持有的锁，`park()` 依赖许可且不要求持有 monitor。调用 `run()` 只是普通方法调用，不会创建新线程；线程结束后不能再次 `start()`。

## 关键细节

- Java 的 RUNNABLE 合并了操作系统的 running 和 ready 等状态。
- `interrupt()` 通常只是设置标志或让可中断阻塞抛出异常，不是强杀线程。
- `notify` 不会立刻让等待线程执行，它还需重新获得 monitor。
- 线程转储应多次采样，区分瞬时等待和持续卡死。

## 原理机制

线程状态由执行位置和等待原语共同决定。monitor 竞争、条件等待、AQS park 与定时阻塞走不同的队列和唤醒机制，因此同样“没运行”会显示不同状态。诊断时要从状态进入具体锁对象、owner 和调用栈。

## 项目经验版

项目映射提示：线上排查可连续采集三份 `jstack`，按线程状态和相同栈聚类，再结合 CPU、锁 owner、线程池队列和请求链路定位。不要仅凭一份 dump 中 WAITING 数量就判断故障。

## 常见追问

- 问：BLOCKED 与 WAITING 有什么区别？答：BLOCKED 特指等待进入 `synchronized` monitor；WAITING 是主动进入无期限条件/许可等待。
- 问：`sleep` 会释放锁吗？答：不会；`wait` 会释放调用对象的 monitor。
- 问：中断能终止线程吗？答：需要线程协作处理中断标志或异常，Java 不保证强制终止。
- 问：为什么线程池空闲线程常是 WAITING？答：工作线程会在任务队列或 AQS 条件上 park 等待新任务，这是正常状态。

## 易错点

- 不要把 Java RUNNABLE 等同于正在占用 CPU。
- 不要把 WAITING 一律视为死锁。
- 不要直接调用 `run()` 后声称线程已启动。
