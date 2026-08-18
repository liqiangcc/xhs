<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_synchronized_lock_2886cc94","version":1,"status":"draft","updated_at":"2026-08-18","answer_type":"mechanism","quality_tier":"candidate"} -->
# synchronized 和 Lock 的区别

## 核心结论

`synchronized` 是 Java 语言内置的 monitor 同步机制，进入同步方法或代码块时自动获取对象监视器，正常返回或异常退出时自动释放；`Lock` 是 `java.util.concurrent.locks` 的显式锁接口，成功 `lock/unlock` 与 monitor 具有同等级的内存同步语义，但把获取、释放和等待策略交给 API 与具体实现。面试里常拿 `ReentrantLock` 对比 `synchronized`：两者都能做可重入互斥，但 `ReentrantLock` 额外提供可中断获取、立即/超时尝试、公平策略以及多个 `Condition`；代价是必须显式 `unlock`，并且这些扩展能力不能笼统推广到所有 `Lock` 实现。

## 1 分钟版

- **共同点**：都可以保护共享状态；`synchronized` 的 monitor unlock→后续 lock，以及成功的 `Lock.unlock()`→后续 `Lock.lock()`，都建立相应的内存同步关系。
- **生命周期**：`synchronized` 是块结构，退出同步块时 JVM 语义保证释放；显式 `Lock` 通常要 `lock(); try { ... } finally { unlock(); }`。
- **获取方式**：`synchronized` 语法没有 try/超时/可中断的获取 API；`Lock` 接口提供 `tryLock()`、定时 `tryLock`、`lockInterruptibly()`，但具体能力要看实现文档。
- **等待条件**：monitor 使用 `Object.wait/notify/notifyAll`；`Lock` 可通过 `Condition` 提供独立条件队列，常见 `ReentrantLock` 可以创建多个 `Condition`。
- **选型**：只需词法作用域内互斥时优先简单的 `synchronized`；确实需要超时、取消、公平策略、多个条件队列或跨作用域锁编排时，再选合适的 `Lock` 实现。

## 3 分钟版

先把比较对象说准确：`synchronized` 是语言规范定义的 monitor 操作；`Lock` 是一个接口，不等于 `ReentrantLock`，也不等于 AQS。`Lock` 允许实现具有不同属性，甚至可以不是可重入互斥锁。因此，面试中所谓“synchronized 和 Lock 的区别”，若讨论公平锁、可重入和 `Condition`，通常实际是在比较 `synchronized` 与 `ReentrantLock`。

`synchronized` 的入口是同步方法或 `synchronized(obj)`。线程先对目标 monitor 执行 lock，成功后进入临界区；代码块无论正常结束还是异常结束，都会对同一 monitor 自动 unlock。Java 内存模型规定，同一 monitor 上一次 unlock synchronizes-with 后续 lock，因此临界区前后的共享状态可以按 happens-before 推理。单线程也可以重复获取同一 monitor，所以它本身是可重入的。

显式 `Lock` 把流程改成方法调用：获取锁、进入临界区、在 `finally` 中释放。`Lock` 接口要求成功的 lock/unlock 具备与内置 monitor 相同的内存同步效果，同时开放了非阻塞尝试、定时尝试和可中断获取等扩展入口。它的灵活性也意味着资源管理责任落到调用方：漏掉 `unlock()` 会让后续线程持续无法进入，所以官方 API 推荐 `lock` 后立即进入 `try/finally`。

等待协作也不同。内置 monitor 的条件等待依赖对象自己的 wait set 和 `wait/notify/notifyAll`；`Condition` 把这类等待从对象 monitor 中拆出来并绑定到一个 `Lock`，一个支持条件的锁可以创建多个 `Condition`，例如把“队列非空”和“队列未满”分开等待。`Condition.await()` 会原子地释放关联锁并挂起，返回前重新获取锁。

若具体到 `ReentrantLock`，它与内置 monitor 有相同的基本互斥与可重入语义，但提供可选公平策略。Java SE 21 文档说明公平模式在竞争下倾向最长等待线程，但可能降低总体吞吐，而且线程调度公平并不因此被保证；无参 `tryLock()` 即使在公平锁上也允许直接抢占可用锁。因此“Lock 一定公平”或“公平锁绝不会饥饿/插队”都说得过头。

资源与性能上不要背“synchronized 一定慢、Lock 一定快”。语言/JDK 实现、竞争程度、临界区长度、等待方式都会改变结果。真正可稳定比较的是语义和能力：monitor 的块结构更易于正确释放，显式 `Lock` 的状态机和 API 更灵活；性能必须基于目标 JDK 与实际负载测量。

## 关键细节

- Java SE 21/JLS 规定：`synchronized` 在同步块正常或异常结束时都会自动解锁；同一线程可以重复取得同一 monitor。
- JMM 规定同一 monitor 的 unlock synchronizes-with 后续 lock；`Lock` 接口要求成功 lock/unlock 提供与 monitor 对应的内存同步效果。
- `Lock` 是接口。`lockInterruptibly()`、定时 `tryLock()` 等语义由接口定义，但某些实现对中断能力、性能和排序保证可能不同，必须查看具体实现。
- `ReentrantLock` 默认构造是非公平模式；可选公平模式只描述锁获取策略，不保证操作系统/线程调度也公平；无参 `tryLock()` 不遵守公平排队。
- `Condition` 可以让一个锁拥有多个条件等待集合；这比把所有条件都放到同一个 monitor wait set 更容易精确唤醒不同类别的等待者。
- 不要用“JDK 某代的锁升级/偏向锁细节”回答所有版本。这里核对的是 Java SE 21 语言与 API 契约；具体 HotSpot 优化属于实现层，需要另按目标 JDK 源码和测量讨论。

## 原理机制

两者的共同不变量是：访问同一份受保护共享状态的线程必须遵守同一把锁的协议。成功获取锁后进入临界区，释放锁形成同步边；后续成功获取同一同步对象的线程因此能按内存模型看到此前受保护写入。锁本身不会阻止“不遵守协议”的普通字段访问，所以只有所有相关访问都经过同一同步协议，互斥与可见性推理才成立。

`synchronized` 把“获取→执行→释放”绑定到词法块，异常路径也由语言语义释放。显式 `Lock` 则把这些状态转换暴露成 API，因此可以在获取阶段选择失败返回、超时或响应中断，也可以把释放放到不同词法作用域；这种自由度就是它能力更强同时更容易误用的原因。

条件等待是在互斥之上的第二层状态机：等待线程必须先持有锁，`wait`/`Condition.await` 在挂起时释放对应锁，让修改条件的线程可以进入；被唤醒后还要重新获得锁并重新检查谓词。多个 `Condition` 的价值不是“锁更多”，而是把不同业务谓词的等待集合分开管理。

## 项目经验版

项目映射提示：先写清共享状态、临界区和取消需求，再决定锁。若只是单对象内一个短临界区，没有超时、公平或多条件等待要求，可以优先使用 `synchronized` 降低释放遗漏风险；若请求有截止时间、任务可取消、需要两个独立条件队列，或锁获取与释放确实要跨作用域，则评估 `ReentrantLock`/其他 `Lock` 实现。上线前用目标 JDK 做竞争压测，观察吞吐、等待时间、超时/中断数和线程阻塞，而不是引用“某种锁天然更快”的旧结论。

## 常见追问

- 问：`synchronized` 和 `ReentrantLock` 都可重入吗？答：是。JLS 允许同一线程重复获取同一 monitor；`ReentrantLock` 也维护当前线程的 hold count，重复 `lock()` 会增加持有计数。
- 问：为什么显式 `Lock` 必须配 `finally`？答：`unlock()` 不是词法块自动动作；临界区抛异常时若没有 `finally`，锁可能一直保持。`synchronized` 则由语言语义在正常或异常退出时自动释放 monitor。
- 问：公平 `ReentrantLock` 是否保证严格 FIFO？答：不能这么说。文档描述的是竞争时倾向最长等待线程，且不保证线程调度公平；无参 `tryLock()` 还会忽略公平设置直接尝试获取。
- 问：什么时候 `Condition` 比 `wait/notifyAll` 更合适？答：当同一锁保护多个不同条件谓词时，可以为每类条件建立独立 `Condition`，减少把无关等待者都唤醒的需要；仍然要在锁内用循环重新检查条件。
- 问：`Lock` 是否一定基于 AQS？答：不是。`Lock` 只是接口，规范没有要求 AQS；某个具体实现是否使用 AQS 属于实现细节，应查看对应 JDK 源码。

## 易错点

- 不要把 `Lock` 接口和 `ReentrantLock`、AQS 当成同一个概念；公平、可重入、条件支持等都要落到具体实现。
- 不要说 `synchronized` 只能保证原子性、`Lock` 才保证可见性；两者正确获取/释放都具有内存同步语义。
- 不要说 `Lock` 一定比 `synchronized` 快。当前性能结论必须限定 JDK、竞争模型和临界区负载。
- 不要说公平锁等于线程调度公平，也不要忽略公平 `ReentrantLock` 的无参 `tryLock()` 可以 barging。
- 不要只列 API 差异而漏掉最关键的责任边界：`synchronized` 自动释放，显式 `Lock` 的释放正确性由调用方保证。
