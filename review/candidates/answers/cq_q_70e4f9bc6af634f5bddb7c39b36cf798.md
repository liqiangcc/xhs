<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_70e4f9bc6af634f5bddb7c39b36cf798","version":1,"status":"draft","updated_at":"2026-08-21","quality_tier":"candidate","answer_type":"coding"} -->
# 并发手撕：使用两个 Goroutine 交替打印 1-100

## 核心结论

用两个“轮到谁”的 channel 做显式交接：奇数 Goroutine 只有拿到 `oddTurn` token 才打印，打印后把 token 交给 `evenTurn`；偶数 Goroutine 对称执行。这样顺序由 channel 同步关系保证，不依赖 `time.Sleep`、调度器时序或共享计数器抢锁。最后用 `sync.WaitGroup` 等待两个 Goroutine 退出。

## 1 分钟版

- 启动两个 worker Goroutine：一个负责 `1,3,...,99`，另一个负责 `2,4,...,100`。
- `oddTurn` 和 `evenTurn` 分别表示奇数/偶数方的执行许可；主 Goroutine 先给 `oddTurn` 一个 token。
- 奇数方收到 token 后打印当前奇数，再把 token 交给偶数方；偶数方收到后打印当前偶数，再交还。
- 打印 `100` 后不能再向 `oddTurn` 发送，否则没有接收者，会把最后一个 Goroutine 卡住。
- `WaitGroup.Add(2)` 必须在启动 worker 之前完成；每个 worker `defer wg.Done()`，主流程 `wg.Wait()`。
- 这题的关键不是“两个 Goroutine 都能打印”，而是把**顺序约束编码进同步协议**。

## 3 分钟版

最简单可靠的做法是把“谁能打印下一项”建模成 token。两个 worker 不竞争共享 `i`，各自只遍历自己的奇数或偶数序列。奇数 worker 必须先从 `oddTurn` 收到许可，打印后再向 `evenTurn` 发送；偶数 worker 同理。因此每一次输出之前，都有一次来自对方的 channel 交接。

Go 规范说明 Goroutine 由 `go` 语句独立并发执行，channel 可以被多个 Goroutine 用于通信；Go 内存模型进一步规定，channel 的发送与匹配接收之间建立同步顺序。这里正是利用这个性质把 `1 -> 2 -> 3 -> ... -> 100` 的执行次序串起来，而不是赌调度器“刚好轮流运行”。

```go
package alternateprint

import (
    "fmt"
    "io"
    "sync"
)

// Print1To100 starts exactly two worker goroutines that print 1..100 in order.
func Print1To100(w io.Writer) {
    oddTurn := make(chan struct{}, 1)
    evenTurn := make(chan struct{}, 1)

    var wg sync.WaitGroup
    wg.Add(2)

    go func() {
        defer wg.Done()
        for i := 1; i <= 99; i += 2 {
            <-oddTurn
            fmt.Fprintln(w, i)
            evenTurn <- struct{}{}
        }
    }()

    go func() {
        defer wg.Done()
        for i := 2; i <= 100; i += 2 {
            <-evenTurn
            fmt.Fprintln(w, i)
            if i < 100 {
                oddTurn <- struct{}{}
            }
        }
    }()

    oddTurn <- struct{}{} // 1 先执行
    wg.Wait()
}
```

这里给 channel 容量 `1` 只是为了让主 Goroutine 可以直接放入第一个 token；之后每个 token 仍然只有一个，两个 worker 仍按严格交接执行。也可以使用无缓冲 channel，但要把第一次发送放到能与接收同时进行的位置，避免主 Goroutine 在 worker 启动前阻塞。

## 关键细节

- **不要用 `time.Sleep` 控制顺序**：sleep 只能延迟当前 Goroutine，不能建立“下一次一定轮到对方”的协议，机器负载变化后仍可能乱序。
- **不要只用一个无保护共享计数器**：两个 Goroutine 同时读写会产生 data race；即使用 mutex 修掉 race，还需要额外的条件变量/轮次状态才能保证严格交替。
- **最后一次交接要收口**：偶数 worker 打印 `100` 后直接退出；如果还执行 `oddTurn <- struct{}{}`，此时奇数 worker 已完成 50 次循环，不再接收，程序会死锁在最后一次发送。
- **WaitGroup 只负责“等完成”**，不负责“排顺序”。顺序来自 channel token，完成等待来自 `WaitGroup`，职责不要混在一起。
- `WaitGroup.Add(2)` 在创建 worker 前调用，避免 `Wait` 与正向 `Add` 的生命周期竞态。`Done` 让计数减一，`Wait` 在计数归零后返回。
- 当前 `sync` 文档在 Go 1.25 新增了 `WaitGroup.Go`；这里使用传统 `Add/Done` 写法，便于兼容更早版本，也更直接展示面试题的同步边界。
- 固定题目规模下总共打印 100 次；若推广到 `1..N`，时间复杂度是 `O(N)`，额外同步状态是 `O(1)`（不计输出本身和 Goroutine 栈）。
- `go test -race` 应作为并发题的必要验证之一；仅“跑一次看起来是 1..100”不足以证明没有数据竞争或偶发乱序。

## 原理机制

这个方案把输出序列分解成 100 个有向依赖：打印 2 必须发生在打印 1 并完成 token 发送之后，打印 3 又必须发生在打印 2 的交接之后，以此类推。每个 worker 内部的循环顺序是程序顺序；跨 worker 的顺序由 channel send/receive 建立。两类顺序串联后，得到完整的 `1 < 2 < ... < 100`。

从不变量看，在任意时刻最多只有一个有效 token：初始在 `oddTurn`，奇数方消费后转移到 `evenTurn`，偶数方消费后再转回。拿不到 token 的一方不能输出，因此不可能出现 `2` 先于 `1`、连续输出两个奇数、或两个 worker 同时推进输出的情况。

结束时要特别处理最后一个偶数。`100` 已经是目标序列末尾，没有“下一轮奇数”需要唤醒，所以最后一次不发送 token。这样两个 worker 都能自然执行 `Done`，主 Goroutine 的 `Wait` 最终返回。

## 项目经验版

这是并发手写题，不应包装成虚构生产经历。复习时可以真实记录自己的验证过程：先写 channel 交接协议，再用测试解析输出是否恰好为 `1..100`，循环运行多次并加 `go test -race`。如果没有真实线上使用经历，就只陈述这个可复现实验，不声称生产结果。

## 常见追问

- 问：为什么不能两个 Goroutine 都 `for` 循环然后 `Sleep`？答：`Sleep` 不提供跨 Goroutine 的顺序保证，只是让当前 Goroutine 暂停一段时间；严格交替需要显式同步协议。
- 问：能不能只用一个 channel？答：可以设计成传递“下一个数字/所有权”的单 channel 状态机，但要避免某个 Goroutine 取到不属于自己的值后反复塞回造成复杂性；两个 turn channel 更直观地表达二方握手。
- 问：为什么 channel 容量是 1？答：只是为了方便主 Goroutine 预置初始 token。协议始终只有一个 token；改成无缓冲 channel 也可以，但初始发送必须和接收并发发生。
- 问：`WaitGroup` 能保证 1..100 的顺序吗？答：不能。它只保证主 Goroutine 等两个 worker 完成；输出顺序由 `oddTurn/evenTurn` 的交接保证。
- 问：如果要打印到 `1..N` 怎么改？答：把上界参数化，并在每次发送前判断对方是否还有下一项；核心原则是“最后一个输出者不能再向已经退出的一方发送”。
- 问：怎样证明没有 race？答：一方面共享 writer 的访问被 token 严格串行化，另一方面用 `go test -race` 做动态检查；测试还应重复执行并逐项断言输出恰好是 1 到 100。

## 易错点

- `wg.Add(2)` 放到 worker 内部，主 Goroutine 可能先执行 `Wait`。
- 打印 100 后仍向 `oddTurn` 发送，导致结尾死锁。
- 只检查输出长度是 100，没有逐项检查顺序和值。
- 两个 Goroutine 共享 `i` 并自增，却没有同步，产生 data race。
- 使用 `Sleep`、`GOMAXPROCS(1)` 或“调度器通常会轮换”来替代同步协议。
- 为了退出而随意 `close` 两个 channel，导致对已关闭 channel 发送 panic；这题无需 close，Goroutine 生命周期本身已经有界。
