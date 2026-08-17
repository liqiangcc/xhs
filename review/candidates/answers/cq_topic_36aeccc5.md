<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_36aeccc5","version":2,"status":"draft","updated_at":"2026-08-17","answer_type":"concept","quality_tier":"candidate"} -->
# 线程池的拒绝策略有哪些？

## 核心结论

Java 21 的 `ThreadPoolExecutor` 在两类情况下会拒绝新任务：线程池已经关闭，或者线程数上限与有界工作队列都已饱和。拒绝后交给 `RejectedExecutionHandler`。JDK 提供四个预置策略：`AbortPolicy` 抛异常、`CallerRunsPolicy` 让提交线程执行、`DiscardPolicy` 静默丢弃、`DiscardOldestPolicy` 丢队首后重试。选型核心不是背类名，而是明确“任务能不能丢、失败要不要显式暴露、提交线程能不能承担反压”。

## 1 分钟版

- `AbortPolicy`：拒绝时抛 `RejectedExecutionException`。当上游必须知道系统过载并决定失败、重试或降级时最清晰。
- `CallerRunsPolicy`：线程池未 shutdown 时，由调用 `execute` 的线程直接运行被拒绝任务；JDK 将它描述为一种简单的反馈控制，会降低新任务提交速率。
- `DiscardPolicy`：直接丢弃被拒绝任务且不抛异常；只适用于业务明确允许丢失、且不依赖任务完成的场景。
- `DiscardOldestPolicy`：线程池未 shutdown 时丢弃工作队列队首任务，再重新调用 `execute`；JDK 明确指出它很少是可接受的策略，因为它牺牲的是等待最久的任务而不是业务最低优先级任务。

## 3 分钟版

先说触发条件。`ThreadPoolExecutor.execute` 不只是“队列满了就拒绝”。如果 executor 已经 shutdown，任务会被拒绝；如果最大线程数和工作队列容量都是有限的，并且两者都达到饱和，也会进入拒绝处理。具体构造器若没有显式传入 handler，会使用文档规定的默认拒绝处理器；常见默认处理器是 `AbortPolicy`。

四种策略可以用三个维度比较：任务是否继续执行、拒绝信号由谁承担、对上游的反压是什么。

`AbortPolicy` 保留最强的显式失败信号：提交方立即得到 `RejectedExecutionException`。它不会替你决定是否重试，所以重试必须结合幂等性、截止时间和上游容量，否则可能把线程池过载放大成重试风暴。

`CallerRunsPolicy` 在 executor 未 shutdown 时由提交线程同步执行任务。JDK 文档把它描述为一个简单的反馈控制机制，因为提交线程被占用后，新任务自然提交得更慢。它的边界也很明确：如果提交线程是延迟敏感的事件循环、请求线程或关键调度线程，任务耗时会直接转移到调用路径，所以必须先确认调用线程角色。

`DiscardPolicy` 静默丢弃任务，因此只有“任务完成从不被依赖”的场景才合适。`DiscardOldestPolicy` 丢的是队列 head，然后重试当前任务；它不了解业务优先级，重试也可能继续失败，所以不能把它误解成“自动淘汰低优先级任务”。

工程上通常先确定队列是否有界、任务是否可丢、提交协议是否允许同步反压，再决定 handler。自定义 `RejectedExecutionHandler` 可以计数、日志、转业务错误或进入降级路径，但不能增加线程池真实容量，因此还必须配合限流、容量规划和拒绝监控。

## 关键细节

- 拒绝处理器入口是 `RejectedExecutionHandler.rejectedExecution(Runnable, ThreadPoolExecutor)`；它处理的是任务无法被 executor 接收，不是 worker 线程中业务代码抛出的异常。
- `CallerRunsPolicy` 只有在 executor 未 shutdown 时才由调用 `execute` 的线程运行任务；shutdown 时它不会执行该任务。
- `DiscardOldestPolicy` 丢工作队列的 head，再重新尝试 `execute`；它没有“这次重试一定成功”的保证。
- “默认是 AbortPolicy”要限定到使用 JDK 文档中未显式提供 handler、由 executor 选择默认拒绝处理器的构造路径，不能把它说成存在一个无参默认构造器。
- 自定义 handler 只能决定拒绝后的处理方式，不能替代 core/max、队列容量、上游限流和任务超时设计。

## 原理机制

状态链可以概括成：

`execute(task) → 尝试 core worker → 尝试入队 → 尝试 non-core worker → shutdown 或 max+queue 饱和 → rejectedExecution(task, executor)`。

到最后一步后：

1. `AbortPolicy`：结束提交并抛 `RejectedExecutionException`。
2. `CallerRunsPolicy`：若未 shutdown，将任务转移到提交线程同步执行。
3. `DiscardPolicy`：结束该任务，不报告异常。
4. `DiscardOldestPolicy`：若未 shutdown，删除队首等待任务，再回到 `execute` 重试。

因此拒绝策略改变的是“过载后的任务命运”，不是线程池容量本身。资源取舍也不同：`CallerRunsPolicy` 消耗调用线程时间形成反压；两个 discard 策略牺牲任务完成；`AbortPolicy` 将失败显式交给上游。监控至少应覆盖拒绝次数、队列长度、活跃线程数，以及按业务协议统计的失败/丢弃/CallerRuns 次数。

## 项目经验版

项目映射提示：补入真实的 core/max、队列类型和容量、任务平均/尾延迟、提交线程角色、任务是否幂等、拒绝时的上游协议、限流阈值和压测结果。没有这些事实时，只讲选择框架，不虚构“线上用 CallerRuns 扛住某次洪峰”或具体拒绝数量。

## 常见追问

- 问：线程池满了为什么不等于“队列满了”？答：拒绝还可能因为 executor 已 shutdown；运行中则要同时看最大线程数、队列是否有界以及当前饱和状态。
- 问：`CallerRunsPolicy` 会创建新线程吗？答：不会。未 shutdown 时它让调用 `execute` 的线程直接运行被拒绝任务，把执行成本传回提交路径。
- 问：`DiscardOldestPolicy` 为什么危险？答：它只按队首删除最久等待的任务，不知道业务优先级，而且随后重试仍可能失败。
- 问：自定义拒绝策略能解决容量不足吗？答：不能。它只能定义拒绝后的动作；真正的容量问题仍要通过任务耗时、线程数、队列、限流和上游协议一起处理。

## 易错点

- 不要把四个类名背完就结束；先讲拒绝触发条件和任务语义。
- 不要说 `CallerRunsPolicy` “保证任务最终完成”；shutdown 边界下它不会执行被拒绝任务。
- 不要把 `DiscardPolicy` 用于必须处理的订单、持久化或通知任务，除非业务明确接受丢失并有观测。
- 不要把 `DiscardOldestPolicy` 说成“淘汰低优先级任务”；它只处理队首。
- 不要把拒绝策略当容量规划、限流和重试治理的替代品。
