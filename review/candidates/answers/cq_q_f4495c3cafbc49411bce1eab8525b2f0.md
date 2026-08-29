<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f4495c3cafbc49411bce1eab8525b2f0","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 多线程交替打印 abc 和 123

## 核心结论

来源只保留“多线程交替打印 abc 和 123”，没有保存线程数、重复轮数、先打印哪一组、是逐字符交替还是整组交替、是否允许忙等。这里声明最小 Java 合同：两个线程分别负责完整字符串 `abc` 和 `123`，以**组为单位**交替，`abc` 先打印，重复 `rounds` 轮，结果为 `abc123abc123...`；`rounds >= 0`，零轮输出空串。实现用一把 `ReentrantLock`、两个 `Condition` 和一个 `abcTurn` 状态，不依赖线程启动/调度顺序，也不忙等。

每个线程进入自己的循环后，只有轮到自己时才能追加；否则在对应 Condition 上 `await`，原子释放锁。追加完成后切换 turn 并 signal 对方。判断 turn 必须放在 `while` 中重检，避免虚假唤醒或重新竞争锁后状态已变化。测试为了可重复验证把“打印”写入同一个 `StringBuilder`；替换为 `System.out.print` 不改变同步协议。

## 1 分钟版

- 状态只有一个：`abcTurn=true` 表示轮到 abc 线程，否则轮到 123 线程。
- 两个线程共享同一把锁，保证“检查轮次 → 输出一组 → 切换轮次 → 唤醒对方”是一个原子协议片段。
- abc 线程：`while (!abcTurn) abcCondition.await()`；输出后设 false，再 signal numberCondition。
- 123 线程镜像执行：`while (abcTurn) numberCondition.await()`；输出后设 true，再 signal abcCondition。
- `await` 会释放锁，所以对方能进入推进状态；不能持锁自旋。
- 先启动哪个 Java Thread 不重要；协议规定第一合法状态是 abcTurn=true。
- 总输出工作 O(rounds)，同步状态 O(1)，结果缓冲本身占 O(rounds) 字符空间。

## 3 分钟版

```java
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public final class AlternatingPrinter {
    public static String render(int rounds) throws InterruptedException {
        if (rounds < 0) throw new IllegalArgumentException("rounds must be non-negative");

        ReentrantLock lock = new ReentrantLock();
        Condition abcCondition = lock.newCondition();
        Condition numberCondition = lock.newCondition();
        StringBuilder out = new StringBuilder(rounds * 6);
        boolean[] abcTurn = {true};

        Thread abc = new Thread(() -> {
            try {
                for (int i = 0; i < rounds; i++) {
                    lock.lockInterruptibly();
                    try {
                        while (!abcTurn[0]) abcCondition.await();
                        out.append("abc");
                        abcTurn[0] = false;
                        numberCondition.signal();
                    } finally {
                        lock.unlock();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException(e);
            }
        }, "abc-printer");

        Thread numbers = new Thread(() -> {
            try {
                for (int i = 0; i < rounds; i++) {
                    lock.lockInterruptibly();
                    try {
                        while (abcTurn[0]) numberCondition.await();
                        out.append("123");
                        abcTurn[0] = true;
                        abcCondition.signal();
                    } finally {
                        lock.unlock();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException(e);
            }
        }, "123-printer");

        numbers.start(); // 故意先启动 123，结果仍由 turn 状态决定
        abc.start();
        abc.join();
        numbers.join();
        return out.toString();
    }

    private AlternatingPrinter() {}
}
```

这里故意先 `start()` 数字线程：它拿到锁也会发现 `abcTurn=true`，于是进入等待并释放锁；abc 线程输出后切换状态并唤醒它。因此正确性来自共享状态机，而不是“我猜 abc 线程会先被 CPU 调度”。

## 关键细节

- **来源歧义必须显式收口**：当前选择“整组 abc 与整组 123 交替”。如果面试官想要 `a1b2c3`，那是另一份状态机合同，不能假装等价。
- **为什么不用 `sleep`**：sleep 只能延迟线程，不能建立谁在什么状态下有权输出的同步条件；负载变化会破坏时序假设。
- **为什么不用自旋**：`while (!turn) {}` 会持续占 CPU；Condition 等待会释放锁并挂起。
- **为什么 while 重检**：虚假唤醒或竞争都意味着被唤醒不等于条件必然成立。
- **共享 StringBuilder 为什么安全**：它本身不是线程安全容器，但所有 append 都在同一把锁的临界区内，没有并发写。
- **启动顺序不等于输出顺序**：测试和实现故意先启动 `123` 线程，仍由 `abcTurn` 决定首组。
- **异常边界**：示例关注正常交替协议；生产级组件若允许外部中断某一工作线程，还要设计取消传播，避免另一线程永久等待。

## 原理机制

这本质上是一个两状态有限状态机：`ABC_TURN -> NUMBER_TURN -> ABC_TURN ...`。锁保护状态迁移和对应输出的原子性；Condition 把“不属于当前状态”的线程挂起。signal 不是“直接把执行权交给对方”，而只是把等待者变成可竞争锁；所以等待者重新获得锁后仍必须检查状态谓词。

线程启动、操作系统调度和锁竞争都可以是不确定的，但只要所有输出都必须经过受锁保护的状态机，不确定调度就不会改变可观察的输出顺序。这也是并发题里比 sleep 时间猜测更可靠的设计原则。

## 项目经验版

来源没有真实生产场景，不能虚构。实际业务一般不会为了拼接两个固定字符串创建线程；这道题的价值在于证明能把顺序约束建模成同步状态。生产系统里若是流水线阶段协作，应优先考虑 BlockingQueue、Semaphore、Phaser、CompletableFuture 等更贴合业务语义的并发原语，并明确取消/超时协议。

## 常见追问

- 问：如果数字线程先启动，会不会先打印 123？答：不会。它检查到 `abcTurn=true` 会 await，输出权限由共享状态而非调度顺序决定。
- 问：为什么不用 `synchronized + wait/notify`？答：也能实现；这里用两个 Condition 分离两个等待集合，让状态与等待原因更明确。无论哪种写法，谓词都应 while 重检。
- 问：为什么 signal 后自己还持有锁？答：Condition signal 只让对方进入可竞争状态；当前线程退出临界区 unlock 后，对方才可能重新获得锁。
- 问：如果题意其实是 a1b2c3 呢？答：那需要把状态粒度从“组”改成“字符步骤”，当前候选不会把未保存的题意强行补全。
- 问：能用 Semaphore 吗？答：可以，两只初值 1/0 的 semaphore 能直接表示令牌交接；Condition 版本更直观展示“共享状态 + 条件谓词”的机制。

## 易错点

- 用 `Thread.sleep` 猜调度顺序。
- 用 volatile turn 忙等，功能可能对但持续浪费 CPU。
- `await` 前用 if 而不是 while 检查状态。
- 把线程 start 顺序当作输出顺序保证。
- signal 后忘记切换共享状态，导致同一方重复打印或双方等待。
- 没澄清“abc 和 123 交替”究竟是按组还是按字符，就把某一种解释当成来源事实。
