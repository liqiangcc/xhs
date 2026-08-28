<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d52ca0aa328f82f1166ebc5bd3cc0ad7","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# t1、t2 并发执行，二者完成后再运行 t3

## 核心结论

先让 `t1`、`t2` 都 `start()`，不要让其中一个等待另一个；协调线程再等待二者的完成条件，最后才启动 `t3`。如果题目强调“线程对象已经终止”，`Thread.join()` 最直接：分别 `join` t1、t2，两个 `join` 都返回后再 `t3.start()`。如果强调“两项工作都完成后进入下一阶段”，`CountDownLatch(2)` 更适合把“完成信号”与具体线程对象解耦。Java 调度器不能保证两个线程在同一 CPU 时刻真正同时执行，这里的“同时”应理解为没有先后依赖、可以并发推进。

## 1 分钟版

- 先创建并启动 `t1`、`t2`，这样两者都具备并发执行机会。
- **严格等待线程终止**：主线程依次 `t1.join()`、`t2.join()`；两个调用都返回后再启动 `t3`。
- **等待两项任务完成**：创建 `CountDownLatch(2)`，t1/t2 各自在 `finally` 中 `countDown()`，协调线程 `await()`；计数到 0 后启动 t3。
- `join()` 和 `await()` 都会响应中断，不能把 `InterruptedException` 静默吞掉。
- `CountDownLatch` 是一次性的，计数到 0 后不能重置；重复多轮阶段同步应换适合重复使用的同步器或重新创建 latch。

## 3 分钟版

```java
import java.util.concurrent.CountDownLatch;

public final class ThreadStageSolution {
    public static void runWithJoin(
            Runnable task1, Runnable task2, Runnable task3) throws InterruptedException {
        Thread t1 = new Thread(task1, "t1");
        Thread t2 = new Thread(task2, "t2");

        t1.start();
        t2.start();

        t1.join();
        t2.join();

        Thread t3 = new Thread(task3, "t3");
        t3.start();
        t3.join();
    }

    public static void runWithCountDownLatch(
            Runnable task1, Runnable task2, Runnable task3) throws InterruptedException {
        CountDownLatch done = new CountDownLatch(2);

        Thread t1 = new Thread(() -> {
            try {
                task1.run();
            } finally {
                done.countDown();
            }
        }, "t1");

        Thread t2 = new Thread(() -> {
            try {
                task2.run();
            } finally {
                done.countDown();
            }
        }, "t2");

        t1.start();
        t2.start();

        done.await();

        Thread t3 = new Thread(task3, "t3");
        t3.start();
        t3.join();
    }
}
```

`runWithJoin` 对“t1、t2 线程已经结束”表达最精确，因为 JDK 21 的 `join()` 定义就是等待目标线程终止。`runWithCountDownLatch` 表达的是“两个任务都已经发出完成信号”：`CountDownLatch(2)` 需要两次 `countDown()` 才会让 `await()` 返回。这里把 `countDown()` 放在 `finally`，避免任务抛出运行时异常后协调线程永久卡住；但这个版本没有把子线程异常自动传播给调用者，真实业务若需要失败传播，应再配合 `Future`、共享错误容器或结构化任务机制。

如果面试官把“同时运行”解释成“尽量同一起跑线”，可以再加一个开始闸门：先让 t1/t2 都准备好并阻塞在同一个 `CountDownLatch(1).await()`，协调线程确认双方 ready 后 `countDown()` 一次统一放行。但这仍然只是同时变为可运行状态，不能承诺物理 CPU 周期级同时执行。

## 关键细节

- **`start()` 不是顺序等待**：连续调用 `t1.start(); t2.start();` 后，两者由调度器并发推进；代码不能承诺谁先真正获得 CPU。
- **`join()` 的语义最贴近“线程结束”**：JDK 21 `Thread.join()` 等待目标线程终止。JLS 17.4.5 还规定，线程中的所有动作 happens-before 另一个线程从该线程的 `join()` 成功返回，因此随后启动 t3 时能看到此前按内存模型发布的结果。
- **Latch 表达任务完成事件**：`CountDownLatch.await()` 在计数归零前阻塞，t1/t2 各自 `countDown()` 一次。它不要求发信号的线程自己等待计数归零。
- **Latch 的可见性保证**：JDK 文档规定，在计数到 0 前，某线程 `countDown()` 之前的动作 happens-before 另一线程对应 `await()` 成功返回后的动作。
- **`countDown()` 放 `finally`**：否则 task1/task2 若抛出未检查异常，计数可能永远到不了 0；但“继续执行 t3 还是整体失败”属于业务失败策略，必须明确，不能由 latch 替你决定。
- **中断处理**：`join()`、`await()` 都可能抛 `InterruptedException`。库方法通常继续向上抛；若在不能抛出的边界捕获，应根据契约恢复中断标志或执行取消/清理，而不是空 `catch`。
- **一次性边界**：`CountDownLatch` 计数到 0 后不会重新变成 2；多轮阶段协调不能复用同一个 latch。
- **复杂度**：同步器的业务状态是常数级；真正耗时由 t1、t2、t3 的任务决定。总关键路径近似 `max(T1, T2) + T3`，而不是 `T1 + T2 + T3`，前提是 t1/t2 能实际并发。

## 原理机制

这道题本质是一个两阶段依赖图：第一阶段有两个互不依赖节点 t1、t2，第二阶段 t3 同时依赖前两个节点完成。因此正确顺序不是 `t1 -> t2 -> t3`，而是先建立两条并行边，再建立一个汇合点：

`start(t1), start(t2) -> wait(all first-stage complete) -> start(t3)`。

`join` 把汇合条件绑定在具体线程生命周期上：协调线程分别观察 t1、t2 的终止事件。`CountDownLatch` 则把汇合条件抽象成一个计数器：任意执行者只要完成一份工作就发一个信号，等待者只关心计数是否已经归零，因此更容易用于线程池任务或“完成者不是固定 Thread 对象”的场景。

内存可见性也属于同步语义的一部分，而不仅是执行先后。`join` 成功返回和 `CountDownLatch.await` 成功返回都建立相应 happens-before 关系，所以第一阶段发布的结果可以在协调点之后被安全观察；仅靠 `sleep` 或轮询普通 boolean 既不能稳定表达完成条件，也不能自动提供等价的内存模型保证。

## 项目经验版

来源没有提供真实生产项目，不能虚构“线上就是这样实现的”。工程落地时，我会先区分“等待固定线程退出”还是“等待若干任务完成”：前者小型脚本/演示代码用 `join` 最直接；后者若任务交给线程池，通常更倾向 `Future`、`CompletableFuture`、latch 或更高层任务编排，因为业务不应该依赖线程池内部具体 Thread 对象。还要明确失败、取消、超时和中断策略，避免第一阶段有一个任务挂死时整个流程无限等待。

## 常见追问

- 问：连续 `t1.start(); t2.start();` 能保证真正同时开始吗？答：不能保证同一 CPU 时刻，只能保证代码没有人为建立 t1→t2 的等待依赖；实际运行时机由 JVM/OS 调度。
- 问：为什么 `join` 两次不会把 t1、t2 串行化？答：因为两个线程都已经先 `start()` 了；主线程之后先等待 t1，再等待 t2，只是在汇合点观察完成状态，不会阻止 t2 在等待 t1 的期间继续运行。
- 问：Latch 为什么初始化为 2？答：第一阶段有两个独立完成事件，必须收到两次 `countDown()` 才能让 `await()` 通过；初始化为 1 会在第一个任务完成时过早启动 t3。
- 问：`countDown()` 为什么写在 `finally`？答：保证每个已启动任务无论正常返回还是抛运行时异常都不会漏掉自己的完成信号；至于异常是否允许 t3 继续，需要额外失败策略。
- 问：Latch 和 join 怎么选？答：固定 Thread 生命周期依赖用 join 简洁直接；完成事件来自任务、线程池或多个执行者时，latch 解耦更好。若还需要返回值和异常传播，`Future`/`CompletableFuture` 往往更自然。
- 问：如果 t1/t2 每轮都要完成后再运行 t3 呢？答：不要复用已经归零的同一个 `CountDownLatch`；每轮重建，或根据阶段模型选可重复使用的 `CyclicBarrier`/`Phaser` 等同步器。

## 易错点

- `t1.start(); t1.join(); t2.start(); t2.join();`：这会把 t1、t2 直接串行化，违背第一阶段并发要求。
- Latch 初始化成 1：任意一个线程先完成都会提前放行 t3。
- 任务抛异常时没有 `finally countDown()`：等待方可能永久阻塞。
- 先启动 t3，再在 t3 业务代码外部假设它“自然会晚一点执行”：调度顺序不是依赖关系。
- 用固定 `sleep(1000)` 猜 t1/t2 已结束：运行时间和调度不可预测，也没有可靠完成协议。
- 捕获 `InterruptedException` 后什么都不做：取消语义被吞掉，调用者也无法知道等待已被中断。
- 把“同时运行”说成“同一个时钟周期执行”：Java 线程调度不提供这种保证。
