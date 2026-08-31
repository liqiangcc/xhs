<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_eee8e67726c9be6095301d0a4bfe4eab","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"mechanism","quality_tier":"candidate"} -->
# synchronized 和 ReentrantLock 的实现原理与区别？

## 核心结论

两者都能提供可重入的互斥和正确的内存可见性，但抽象层次不同。`synchronized` 是 Java 语言直接提供的 monitor 同步：线程进入同步方法/同步块时获取目标对象的 monitor，退出时由语言语义保证释放；同一 monitor 的一次 unlock happens-before 后续成功 lock。`ReentrantLock` 是 `java.util.concurrent.locks.Lock` 的显式锁实现，基础互斥/内存语义与内置 monitor 锁一致，同时额外提供可中断获取、非阻塞/超时 `tryLock`、可选公平策略和多个 `Condition` 等控制能力。当前 OpenJDK 主线中，`ReentrantLock` 的同步控制建立在 `AbstractQueuedSynchronizer`（AQS）之上：同步 state 表示持有次数，首次获取通过状态竞争建立 owner，重入增加计数，竞争失败时由 AQS 的 CLH-derived 同步队列协调等待线程；但这些属于当前 OpenJDK 实现层事实，不应被当作 Java 语言规范对所有 JDK/VM 的永久要求。

## 1 分钟版

- `synchronized`：锁的是对象 monitor；实例同步方法锁 `this`，静态同步方法锁声明类的 `Class` 对象，同步块锁表达式得到的对象。正常或异常退出同步区域时自动 unlock。
- `ReentrantLock`：显式 `lock()` / `unlock()`；必须用 `try/finally` 保证释放。当前线程已持有时再次获取会增加 hold count，因此同样是可重入锁。
- 内存语义：内置 monitor 的 unlock → 后续同 monitor lock 建立 happens-before；`Lock` 规范要求成功 `lock`/`unlock` 具有同等的内存同步效果。
- `ReentrantLock` 的主要额外能力：`lockInterruptibly()`、`tryLock()`、带超时的 `tryLock(...)`、可选 fair 模式、`newCondition()` 产生多个条件队列，以及若干监控方法。
- 选择与成本：只需要结构化互斥时优先 `synchronized`；明确需要可中断、超时、尝试获取、公平策略或多个条件队列时再用 `ReentrantLock`。不要背“谁一定更快”，性能和资源成本要在目标 JDK、竞争度和临界区下实测。

## 3 分钟版

### 1. synchronized 的机制

Java 语言规范规定，每个对象都关联一个 monitor，同时只能有一个线程持有该 monitor 的锁，并且同一线程可以重复获取同一 monitor。

```java
synchronized (lock) {
    // critical section
}
```

执行时先计算 `lock` 引用，然后尝试锁住它关联的 monitor；拿不到就不能继续执行块体。块体无论正常结束还是抛异常结束，都会执行对应的 unlock。同步实例方法等价于围绕 `this` 的 monitor 建立这种进入/退出语义；静态同步方法使用声明类的 `Class` 对象 monitor。

因此 `synchronized` 的关键不是“锁住了方法”这句话，而是：**哪些代码路径竞争的是同一个 monitor identity**。

### 2. ReentrantLock 的机制

典型使用方式是：

```java
import java.util.concurrent.locks.ReentrantLock;

final ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    // critical section
} finally {
    lock.unlock();
}
```

`ReentrantLock` 维护当前 owner 与重入计数。当前线程第一次成功获取后成为 owner；同一线程再次获取时 hold count 增加；每次 `unlock()` 递减，直到计数归零才真正释放给其他线程竞争。

在当前 OpenJDK 主线实现中，`ReentrantLock` 内部有一个 `Sync`，继承自 `AbstractQueuedSynchronizer`。AQS 的 `state` 表示持有次数：未持有时获取路径竞争把 state 从 0 改为 1 并记录 owner；owner 再次获取时增加 state，实现重入；释放时递减，归零后清除 owner。竞争没有立即成功的线程由 AQS 的 **CLH-derived 同步等待队列**组织，等待/唤醒和取消等细节由 AQS 统一协调。公平与非公平 `Sync` 的差别主要出现在“锁可获取时是否先尊重已有排队前驱”等策略上。

这里必须区分两层：`Lock` / `ReentrantLock` API 语义由 Java SE 文档定义；AQS、state、CAS、CLH-derived 队列和具体 parking 策略属于当前 OpenJDK 实现细节。

### 3. 为什么 ReentrantLock 能做更多事

显式锁把“获取/释放”从语法块中抽出来，所以 API 可以提供不同获取策略：

- `lockInterruptibly()`：等待锁期间可以响应中断；
- `tryLock()`：当前拿不到立即返回 `false`；
- `tryLock(timeout, unit)`：在给定时间内等待，并可响应中断；
- `new ReentrantLock(true)`：启用可选公平策略；
- `newCondition()`：为同一把 Lock 建立独立 `Condition`，可以把不同等待条件分开，而不是所有等待者都挤在一个对象 wait set 中。

这些能力是选择 `ReentrantLock` 的理由，而不是“它名字里有 Lock，所以比 synchronized 高级”。

## 关键细节

- **两者都可重入**：`synchronized` monitor 允许同一线程多次 lock；`ReentrantLock` 用 hold count 表示重入层数。
- **释放方式不同**：`synchronized` 由语言结构自动释放；`ReentrantLock` 必须显式 `unlock()`，所以要把 `unlock()` 放在 `finally` 中。
- **内存可见性不是差异点**：`Lock` 接口要求成功 lock/unlock 提供与内置 monitor lock 相同的内存同步语义。不能说 `ReentrantLock` 只有互斥、没有可见性。
- **公平不是绝对调度公平**：`new ReentrantLock(true)` 提供锁竞争的公平策略，但不保证线程调度整体公平；而且无参 `tryLock()` 即使在 fair lock 上也允许在锁可用时直接抢占。
- **Condition 是一把锁上的多个等待条件**：使用前需要持有对应 lock；它解决的是条件等待的组织方式，不是另一把互斥锁。
- **`synchronized` 的等待/通知依赖 monitor**：`wait/notify/notifyAll` 与对象 monitor 绑定；`ReentrantLock` 则通过 `Condition.await/signal/signalAll` 组织等待者。
- **资源成本需要分版本看**：`ReentrantLock` 本身是一个显式对象；当前 OpenJDK 在竞争时还要维护 AQS 同步队列/节点，Condition 也有等待结构。`synchronized` 不要求业务代码额外持有一个 Lock 对象，但竞争 monitor 同样需要 JVM 运行时状态。不能据此给出跨 JDK 的固定内存或性能大小关系。
- **不要把 HotSpot 历史优化当稳定语义**：对象头、某种锁膨胀路径、曾经存在的偏向锁等都可能随 JDK 改变；面试里应先说规范语义，再明确实现版本。
- **性能要实测**：竞争低/高、临界区长短、虚拟线程/平台线程、目标 JDK 都会影响结果。不能用十年前的“synchronized 慢、ReentrantLock 快”作为固定结论。

## 原理机制

从并发正确性的角度，两者都建立了“owner + 排他进入 + release/acquire 内存顺序”。假设线程 T1 在临界区修改共享状态，然后释放锁；T2 随后成功获取同一同步对象对应的锁，那么规范提供的 happens-before 关系使 T2 可以看到 T1 在释放前完成的写入。

差异主要在**控制面**：`synchronized` 把 lock/unlock 生命周期绑定到词法结构，降低遗漏释放的风险；`ReentrantLock` 把生命周期暴露成 API，因此可以在“怎么等待、等多久、能否被中断、是否采用公平策略、使用哪个条件队列”等方面做更细控制，但调用者也承担了正确释放和条件协议的责任。

从当前 OpenJDK 实现看，`ReentrantLock` 使用 AQS 复用同步器基础设施。第一次获取的核心状态转移是“未持有 → 当前线程持有且 hold count=1”；重入是“owner 不变、hold count+1”；释放则反向递减，直到 0 才让锁重新进入可竞争状态。没有直接获取成功的线程进入 AQS 的 CLH-derived 同步队列，由前驱/释放事件驱动后续竞争。这个实现视角解释了为什么同一套基础设施能组合非公平/公平获取、可中断/超时等待和 Condition，但仍应明确它是当前 OpenJDK 实现，而不是语言规范强制所有 JVM 必须这样实现。

资源上，两种锁都不是“零成本”：无竞争时主要成本来自同步状态检查与进入/退出；竞争发生后还可能涉及排队、调度和上下文切换。`ReentrantLock` 的显式对象与 AQS/Condition 结构换来了更丰富的控制能力；是否值得这部分复杂度，应由业务语义和实测竞争数据决定。

## 项目经验版

来源没有提供真实项目经历，不能虚构生产案例。实际选型时我会先从需求反推：如果只是保护一个短小、结构化临界区，没有超时/中断/多条件队列要求，`synchronized` 通常更简单；如果线程必须在关闭流程中取消锁等待、调用链必须在 SLA 内放弃获取、或一个共享状态上需要多个独立条件队列，就会评估 `ReentrantLock`。性能选择则在目标 JDK、真实并发度和临界区长度下用 JMH/应用指标验证，而不是按关键字做静态结论。

## 常见追问

- 问：`synchronized` 是非公平锁吗？答：语言规范没有给 monitor 获取定义一个可由程序选择的公平策略，也不应把某个 HotSpot 版本的调度行为描述成 Java 语言固定“非公平算法”。如果业务明确需要 `ReentrantLock` 提供的 fair policy，这是它的 API 能力差异。
- 问：为什么 `ReentrantLock` 必须 `finally` 解锁？答：因为释放是显式 API 调用；如果临界区抛异常而跳过 `unlock()`，锁可能一直由当前线程持有。`synchronized` 的退出语义则由语言保证 unlock。
- 问：两者的可见性一样吗？答：在成功获取/释放这一层，`Lock` 规范要求与内置 monitor lock 相同的内存同步效果；所以二者都不只是“互斥”。
- 问：什么时候必须用 `ReentrantLock`？答：典型是确实需要等待可中断、尝试获取、超时、公平策略、多个 `Condition`，或需要显式 Lock API 才能表达的控制流。
- 问：`ReentrantLock` 为什么叫 reentrant？答：持锁线程再次调用 `lock()` 可以立即成功并增加 hold count，后续需要匹配次数的 `unlock()` 才完全释放。
- 问：AQS/CAS/CLH 队列是不是 ReentrantLock 的规范？答：不是。当前 OpenJDK 的 `ReentrantLock.Sync` 基于 AQS，获取路径会使用同步 state/CAS，AQS 使用 CLH-derived 同步队列协调竞争者；Java SE 对外保证的是 `Lock` / `ReentrantLock` API 与内存语义，不强制 JVM 永远采用这一实现。
- 问：公平锁一定不会饥饿、也一定更好吗？答：API 文档说明 fair lock 倾向把访问给等待更久的线程，但线程调度仍不保证绝对公平，而且公平策略通常有吞吐代价；是否使用要看业务目标。

## 易错点

- 把 `synchronized` 简化成“锁方法”，忽略实例、`Class`、同步块表达式对应不同 monitor。
- 说 `synchronized` 不可重入；实际上 monitor 明确定义同一线程可以重复 lock。
- 写 `lock.lock(); doWork(); lock.unlock();` 而没有 `try/finally`。
- 说 `ReentrantLock` 没有 happens-before / 可见性语义。
- 把 fair lock 说成“绝对先到先得”，或忽略无参 `tryLock()` 的 barging 行为。
- 把 AQS、CAS、CLH 队列、对象头、锁升级等具体 JDK/VM 实现细节说成 Java 语言规范。
- 用“ReentrantLock 永远比 synchronized 快”或反过来的固定性能结论替代目标版本/负载下的基准验证。
