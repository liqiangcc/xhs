<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_7db820e34ee11cbf1d7d3f980d6f2de3","version":1,"status":"draft","updated_at":"2026-08-26","answer_type":"coding","quality_tier":"candidate"} -->
# 如何避免死锁？请写一个死锁案例

## 核心结论

死锁不是“线程慢”或“锁竞争严重”，而是一组线程形成了无法自行打破的循环等待。工程上最直接的预防手段是破坏死锁成立条件，尤其是：**所有代码遵守同一个全局加锁顺序**，避免 A→B 与 B→A；尽量避免持有一个锁时再等待另一个资源；确实需要多锁时，可用 `tryLock(timeout)` 获取失败后释放已持有资源并在上层重试。下面的 JDK 21 示例故意让两个线程分别持有 A/B 后再等对方的锁，用 `ThreadMXBean` 在有限时间内证明它真的形成了死锁。

## 1 分钟版

- 经典死锁需要同时具备：互斥、持有并等待、不可剥夺、循环等待；破坏其中任意一个就不会形成该类死锁。
- 最常用的代码级预防是统一锁顺序，例如所有路径都先锁账户 ID 小的对象，再锁 ID 大的对象，禁止一条路径 A→B、另一条 B→A。
- 如果无法建立静态全局顺序，可考虑 `tryLock` + 超时：第二把锁拿不到就释放第一把锁，再由上层按退避/幂等策略重试，而不是无限持有第一把锁等待。
- 缩短临界区、不要在持锁期间做网络 I/O/外部回调，也能减少“持有并等待”的窗口，但它不是统一锁顺序的替代品。
- 线上诊断要看线程 dump / `ThreadMXBean` 的等待关系；发现死锁是诊断，不能替代设计阶段的预防。

## 3 分钟版

```java
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

public final class DeadlockCase {
    private static final ReentrantLock LOCK_A = new ReentrantLock();
    private static final ReentrantLock LOCK_B = new ReentrantLock();
    private static final CountDownLatch BOTH_HOLD_ONE = new CountDownLatch(2);

    private static void await(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
    }

    private static Thread worker(
            String name, ReentrantLock first, ReentrantLock second) {
        Thread t = new Thread(() -> {
            first.lock();
            try {
                BOTH_HOLD_ONE.countDown();
                await(BOTH_HOLD_ONE);
                second.lock();
                try {
                    // 永远到不了这里：另一个线程正持有 second 并等待 first。
                } finally {
                    second.unlock();
                }
            } finally {
                first.unlock();
            }
        }, name);
        // 演示线程设为 daemon，检测到死锁后 JVM 仍能退出，不让示例/CI 永久挂住。
        t.setDaemon(true);
        return t;
    }

    public static void main(String[] args) throws Exception {
        Thread t1 = worker("A-then-B", LOCK_A, LOCK_B);
        Thread t2 = worker("B-then-A", LOCK_B, LOCK_A);
        t1.start();
        t2.start();

        ThreadMXBean bean = ManagementFactory.getThreadMXBean();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(3);
        while (System.nanoTime() < deadline) {
            long[] ids = bean.findDeadlockedThreads();
            if (ids != null && ids.length >= 2) {
                System.out.println("DEADLOCK_DETECTED threads=" + ids.length);
                return;
            }
            Thread.sleep(10);
        }
        throw new AssertionError("deadlock was not detected within deadline");
    }
}
```

这里的关键不是 `sleep` 碰运气：`CountDownLatch` 保证两个线程都已经拿到自己的第一把锁，之后才同时尝试第二把锁，所以等待图稳定为 `t1 持有 A → 等 B`、`t2 持有 B → 等 A`。`findDeadlockedThreads()` 能检测显式 ownable synchronizer 的死锁；线程设为 daemon 只是为了让演示进程在检测成功后退出，不会解除死锁本身。

## 关键细节

- **统一顺序为什么有效**：若所有线程都只能按同一严格顺序获取多把锁，就无法形成“最后一把锁又等待链路前面的锁”的有向环，从而破坏循环等待条件。
- **`tryLock` 的边界**：超时只是让“无限等待”变成可失败操作；失败后必须释放已经拿到的锁，并定义重试、退避和业务幂等，否则可能从死锁变成活锁或重试风暴。
- **释放锁**：显式锁应放在 `try/finally` 中释放。故意死锁的示例里 finally 永远不会正常执行，是因为两个 daemon 线程被设计成永久互等。
- **不要用线程优先级解决**：调度优先级不改变锁依赖图，不是死锁预防机制。
- **数据库死锁**：数据库可以检测事务等待环并主动回滚一个事务，这是“检测 + 牺牲/恢复”；应用仍要正确识别可重试错误并保证重试安全。它和 Java 线程锁的具体检测实现不是一回事。
- **四条件是分析模型**：工程回答不能只背四个名词，要具体指出当前设计破坏的是哪一个条件，以及失败路径如何收敛。

## 原理机制

可以把等待关系画成有向图：节点是线程/事务，边表示“我正在等待对方持有的资源”。在示例中有两条边 `t1 → t2` 和 `t2 → t1`，因此形成环；又因为锁不会被外部强制剥夺，两个线程都没有能继续运行到 `unlock()` 的路径。统一锁顺序相当于给资源建立一个严格偏序，所有获取边只能朝一个方向推进，等待图就不可能沿资源顺序绕回起点。`tryLock` + 回滚则是允许等待失败并主动释放已持有资源，从“持有并等待”路径上打断环。

## 项目经验版

来源没有提供真实线上事故、线程 dump 或数据库死锁日志，不能虚构“我曾经处理过某次生产死锁”。真实排障时我会先冻结证据：线程侧抓 thread dump / `ThreadMXBean`，数据库侧看引擎提供的 deadlock report；还原“谁持有什么、在等什么”的等待图，再回到代码检查锁顺序、事务访问顺序和持锁期间的外部调用。修复后用并发回归测试或故障注入复现原路径，验证等待环不再出现。

## 常见追问

- 问：只要加锁顺序一致就一定没有任何死锁吗？答：它能消除由这些按序资源锁形成的循环等待；系统如果还有不受该顺序约束的其他资源、条件等待或外部阻塞，仍要单独分析，不能把局部规则扩张成全系统保证。
- 问：为什么不用 `sleep` 构造死锁？答：`sleep` 只改变概率和时序；用 latch/barrier 先确认双方都持有第一把锁，再申请第二把锁，才能得到可重复的等待环。
- 问：`findMonitorDeadlockedThreads()` 和 `findDeadlockedThreads()` 有什么区别？答：后者还覆盖 ownable synchronizers（例如 `ReentrantLock`）；本示例使用 `ReentrantLock`，因此调用后者。
- 问：`tryLock(timeout)` 一定比阻塞 `lock()` 好吗？答：不是。它引入超时、回滚和重试策略；如果可以建立简单稳定的全局锁顺序，优先让正确性依赖更少的时序参数。
- 问：如何验证修复？答：保留原始并发触发条件，重复执行并检查线程是否能在截止时间内完成，同时确认没有等待环；若采用超时重试，还要检查错误率、重试次数和业务幂等。

## 易错点

- 两条代码路径分别 A→B、B→A，却认为每个 `synchronized`/`lock()` 单独看都正确就不会死锁。
- 用随机 `sleep` 作为“死锁测试”，测试有时过有时不过，无法作为稳定证据。
- `tryLock` 失败后忘记释放第一把锁，实际上仍保留持有并等待问题。
- 持锁期间调用未知外部代码、RPC 或回调，让锁依赖跨出本模块并难以形成统一顺序。
- 只处理线程被卡住的表象，不还原等待图，最终把长 GC、慢 I/O 或普通锁竞争误判成死锁。
