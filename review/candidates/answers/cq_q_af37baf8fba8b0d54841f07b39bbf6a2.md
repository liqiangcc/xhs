<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_af37baf8fba8b0d54841f07b39bbf6a2","version":1,"status":"draft","updated_at":"2026-08-27","answer_type":"coding","quality_tier":"candidate"} -->
# Go 并发：goroutine 同步与 channel 使用

## 核心结论

来源只保留“写一个 Go 并发（如协程同步或 channel 使用）”，没有保留具体输入输出、并发度、排序或取消语义，因此不能假装还原出唯一原题。下面明确采用一个可执行参考练习：给定 `[]int` 和正整数 worker 数，多个 goroutine 从 jobs channel 取任务并计算平方，单个 collector 从 results channel 收集结果，并按原输入下标恢复顺序。这个例子同时展示 goroutine 生命周期、channel 所有权、`WaitGroup` 同步、关闭顺序以及避免 data race 的基本做法。

## 1 分钟版

- 主线程只负责启动 worker、投递任务和收集结果；worker 之间不共享可写结果切片。
- jobs 的发送方负责 `close(jobs)`，表示不会再有新任务。
- `WaitGroup` 只等待 worker 退出；等所有 worker 退出后，再由协调 goroutine `close(results)`。
- collector 用 `for range results` 读到关闭，因此不会依赖“猜测任务何时结束”。
- 每个结果带原始下标，collector 单线程写 `out[index]`，所以即使 worker 完成顺序随机，最终输出仍与输入顺序一致。

## 3 分钟版

下面代码把题目未冻结的部分显式定义为参考契约；它不是声称原面试题一定要求“并发平方”：

```go
import "sync"

type indexedValue struct {
    index int
    value int
}

func squareConcurrent(values []int, workers int) []int {
    if workers <= 0 {
        panic("workers must be positive")
    }

    jobs := make(chan indexedValue)
    results := make(chan indexedValue)

    var wg sync.WaitGroup
    wg.Add(workers)
    for i := 0; i < workers; i++ {
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- indexedValue{index: job.index, value: job.value * job.value}
            }
        }()
    }

    go func() {
        for i, value := range values {
            jobs <- indexedValue{index: i, value: value}
        }
        close(jobs)
        wg.Wait()
        close(results)
    }()

    out := make([]int, len(values))
    for result := range results {
        out[result.index] = result.value
    }
    return out
}
```

关键关闭顺序是：生产者投递完任务后关闭 jobs；worker 因 jobs 关闭而自然退出并 `Done`；协调者 `Wait` 到所有 worker 退出后再关闭 results；collector 的 range 最终结束。若过早关闭 results，仍在发送结果的 worker 会 panic；若没人关闭 results，collector 会永久阻塞。

## 关键细节

- **channel 关闭权属于发送方/协调方**：接收方通常不能知道是否还会有后续发送，随意关闭会造成 `send on closed channel`。
- **`WaitGroup.Add` 在启动 goroutine 前完成**：避免 goroutine 已经 `Done` 而计数尚未建立的竞态式用法。
- **结果顺序与执行顺序分离**：goroutine 完成顺序不稳定，所以结果携带 index；最终顺序由 collector 恢复，而不是依赖调度器。
- **避免共享写**：示例让 worker 只向 channel 发送，只有 collector 写结果切片；这样并发正确性更容易审查，也能通过 race detector 验证。
- **空输入也能结束**：生产者立即关闭 jobs，worker 退出，results 随后关闭，collector 返回空切片。
- **取消不是来源约束**：如果面试官补充“支持超时/取消”，应引入 `context.Context` 并让生产、worker、发送结果三处都能响应 `ctx.Done()`，不能只在最外层检查一次。

## 原理机制

channel 在这里既是数据通道也是同步边界：一次无缓冲发送必须和一次接收配对，因此天然提供背压；`WaitGroup` 则只表达“所有 worker 已经结束”，并不承担数据传输。把二者分工后，关闭协议可以写成一个清晰的 happens-before 链：停止产生 jobs → worker 消耗完并退出 → results 不可能再有发送 → 关闭 results → collector 结束。这个协议比用 sleep 或共享布尔变量猜结束时机可靠。

## 项目经验版

来源没有真实项目、吞吐、延迟或 goroutine 数量数据，不能虚构线上收益。实际工程里我会先确定任务是否 CPU/IO 密集、是否需要有界并发、取消和错误传播，再决定 worker pool、`errgroup` 或更简单的同步方式；并用 `go test -race`、基准测试和 goroutine/阻塞 profile 验证，而不是把“多开 goroutine”直接等同于更快。

## 常见追问

- 问：为什么不是 worker 直接写 `out[index]`？答：如果严格保证每个 index 只写一次也可以无数据竞争，但把所有写集中到 collector 能让共享状态和关闭协议更直观，也更容易扩展错误处理。
- 问：谁应该关闭 channel？答：知道“以后绝不会再发送”的一方。这里生产者关闭 jobs，等待所有 worker 结束的协调者关闭 results。
- 问：为什么 `WaitGroup` 不能替代 results channel 的关闭？答：`WaitGroup` 只能告诉你 worker 结束，collector 的 `range results` 仍需要 channel close 才能终止。
- 问：把 channel 改成带缓冲会不会改变正确性？答：在容量足够且关闭协议不变时主要改变阻塞/背压特征，不应改变结果；容量应根据负载和内存预算设计，而不是越大越好。
- 问：如何支持取消并避免 goroutine 泄漏？答：给 producer 和 worker 的发送/接收都加 `select` 监听 `ctx.Done()`，并由统一协调路径关闭后续通道；否则下游停止消费时，上游 goroutine 可能永久阻塞在发送上。

## 易错点

- 接收方或多个 worker 竞争关闭同一个 results channel。
- 先关闭 results，再等待 worker，导致仍在发送的 goroutine panic。
- 用 `time.Sleep` 等待并发任务“应该完成”，把调度时机当同步协议。
- 多个 goroutine 无保护写同一共享变量或 map，却没有锁、原子操作或单 owner 设计。
- 忽略错误传播、取消和有界并发，在生产场景里造成 goroutine 泄漏或资源失控。
