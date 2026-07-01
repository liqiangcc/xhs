<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_36aeccc5","version":1,"status":"ready","updated_at":"2026-07-01"} -->
# 线程池的拒绝策略有哪些？

## 核心结论

线程池拒绝策略是在工作队列满且线程数达到最大线程数后处理新任务的兜底机制。JDK 默认提供 AbortPolicy、CallerRunsPolicy、DiscardPolicy、DiscardOldestPolicy，生产环境通常要结合业务做自定义策略和告警。

## 1 分钟版

AbortPolicy 会直接抛 RejectedExecutionException，是默认策略。CallerRunsPolicy 让提交任务的线程自己执行任务，能形成反压但会拖慢调用方。DiscardPolicy 直接丢弃新任务，不抛异常。DiscardOldestPolicy 丢弃队列里最老的任务，再尝试提交新任务。实际线上更推荐自定义 RejectedExecutionHandler，记录日志、打点、告警，必要时把任务写入降级队列。

## 3 分钟版

线程池执行流程是先用核心线程处理任务，核心线程满后任务进入阻塞队列，队列满后再扩到最大线程数，最大线程也满才触发拒绝策略。拒绝不是异常情况的唯一表现，而是容量规划不足、下游变慢或流量突增的信号。选择策略要看任务是否允许丢、是否可重试、调用方是否能承受同步执行。核心交易任务通常不能静默丢弃，应失败可感知并进入补偿；日志、埋点类任务可以在保护主链路时丢弃。

## 关键细节

- 默认拒绝策略是 AbortPolicy。
- CallerRunsPolicy 可以降低提交速度，但会影响调用线程延迟。
- DiscardPolicy 和 DiscardOldestPolicy 有数据丢失风险。
- 拒绝策略应该配合监控线程池活跃数、队列长度和拒绝次数。

## 原理机制

- 拒绝发生在队列无法接收任务且线程数不能继续增加时。
- RejectedExecutionHandler 是线程池暴露的扩展点。
- 有界队列加明确拒绝策略比无界队列更容易暴露容量问题。

## 项目经验版

我会按任务重要性拆线程池，例如核心交易、异步通知、日志埋点分开配置。拒绝发生时至少记录任务类型、线程池名称、队列长度和 traceId，并接入告警。对可补偿任务，可以落库或写 MQ 后异步重试；对不可补偿任务，要让调用方拿到明确失败。

## 常见追问

- 线程池任务提交流程是什么？
- 为什么不建议使用无界队列？
- CallerRunsPolicy 有什么风险？
- 如何设计自定义拒绝策略？

## 易错点

- 不要只背四个名字，要说明触发时机和业务影响。
- 不要静默丢弃核心业务任务。
- 不要把拒绝策略当成限流的完整替代品。
