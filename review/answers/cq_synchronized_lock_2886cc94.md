<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_synchronized_lock_2886cc94","version":1,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# synchronized 和 Lock 的区别

## 核心结论

synchronized 是 JVM monitor 语义，自动获取释放且不可中断等待；Lock 是显式接口，提供可中断、超时、公平策略和多个 Condition。选择重点是控制能力、正确释放和可观测性，不是简单判断谁更快。

## 1 分钟版

- synchronized 进入退出代码块时由 JVM 自动加解锁，异常也会释放。
- ReentrantLock 必须 finally unlock，但支持 tryLock、lockInterruptibly、公平锁和多个条件队列。
- 现代 JVM 已对 synchronized 做大量优化，性能必须按临界区和竞争度压测。

## 3 分钟版

两者都提供互斥及相应可见性保证。monitor 适合结构化、简单临界区；Lock 适合需要超时取消、多个等待条件或显式公平策略的流程。 回答时先统一比较维度，再给选择条件与反例；定义本身不是终点，必须说明代价和不适用边界。

## 关键细节

- synchronized 进入退出代码块时由 JVM 自动加解锁，异常也会释放。
- ReentrantLock 必须 finally unlock，但支持 tryLock、lockInterruptibly、公平锁和多个条件队列。
- 现代 JVM 已对 synchronized 做大量优化，性能必须按临界区和竞争度压测。

## 原理机制

从参与对象、状态变化和主流程展开，再补充并发/故障保证与资源开销。 synchronized 是 JVM monitor 语义，自动获取释放且不可中断等待；Lock 是显式接口，提供可中断、超时、公平策略和多个 Condition。选择重点是控制能力、正确释放和可观测性，不是简单判断谁更快。

## 项目经验版

项目映射提示：从真实代码或架构中选择一个使用点，补齐选择条件、替代方案和验证指标；没有事实时不虚构收益。

## 常见追问

- 问：Lock 为什么必须 finally 释放？答：目标代码或异常路径都不会自动 unlock，遗漏会永久阻塞后续线程。
- 问：公平锁一定更好吗？答：不一定，公平降低饥饿风险但增加调度和吞吐成本。
- 问：二者能混用同一个条件队列吗？答：不能，monitor 的 wait/notify 与 Lock 的 Condition 是不同同步机制。

## 易错点

- 不要只背定义而不说明选择条件。
- 不要把常见实现说成跨版本唯一结论。
- 不要沿用早期 JDK 的绝对性能结论。
