<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_cb77c8ecb05522dcbfb90ee83e023ca9","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 两个线程交替打印 1a2b3c4d5e

## 核心结论

这题的核心不是“让两个线程碰巧轮流运行”，而是把**轮到谁打印**建模成受同步机制保护的共享状态。原始面经只要求两个线程把 `A=[1,2,3,4,5]`、`B=[a,b,c,d,e]` 打成 `1a2b3c4d5e`，没有指定必须用 `wait/notify`、`LockSupport` 或某一种 JUC API。下面给一个明确的 Java 参考契约：两个输入数组非 `null`、等长且元素非 `null`；空数组返回空串；线程 A 先打印第 i 个数字，线程 B 再打印第 i 个字母。实现使用 `ReentrantLock + Condition + turn`，并且故意先启动 B 线程，证明正确性依赖状态谓词而不是启动时序。

## 1 分钟版

- 用一个共享 `turn` 表示当前轮到 A 还是 B；读取、判断、打印和切换 `turn` 都放在同一把锁保护下。
- A 线程只有在 `turn=A` 时打印 `A[i]`，然后把状态切到 B；B 线程对称执行，因此输出顺序由状态机决定。
- `Condition.await()` 必须放在 `while` 里反复检查 `turn`，因为条件等待允许虚假唤醒；真正决定能否继续的是共享谓词。
- 切换状态后再 `signalAll()`；即使通知发生在对方正式等待之前，对方随后拿到锁也会先检查 `turn`，不会靠“记住一次通知”维持正确性。
- 每个元素只打印一次，时间 O(n)；除输出缓冲区外同步状态 O(1)。也可以用 `synchronized + wait/notifyAll`、两个 `Semaphore` 或 `LockSupport`，但都必须维护同一个“谁能继续”的顺序不变量。

## 3 分钟版

参考实现把两个数组长度要求为相同；题目给出的两个数组都是 5 个元素，因此这个契约覆盖原题。为了让测试能直接断言结果，示例把打印内容写入 `StringBuilder`，真实面试现场换成 `System.out.print` 不改变同步逻辑。

```java
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public final class AlternatingPrinter {
    public static String alternate(String[] a, String[] b) throws InterruptedException {
        if (a == null || b == null) {
            throw new IllegalArgumentException("inputs must not be null");
        }
        if (a.length != b.length) {
            throw new IllegalArgumentException("inputs must have equal length");
        }
        for (String s : a) {
            if (s == null) throw new IllegalArgumentException("A element must not be null");
        }
        for (String s : b) {
            if (s == null) throw new IllegalArgumentException("B element must not be null");
        }

        ReentrantLock lock = new ReentrantLock();
        Condition turnChanged = lock.newCondition();
        StringBuilder out = new StringBuilder();
        boolean[] aTurn = {true};

        Runnable printA = () -> {
            try {
                for (String value : a) {
                    lock.lockInterruptibly();
                    try {
                        while (!aTurn[0]) {
                            turnChanged.await();
                        }
                        out.append(value);
                        aTurn[0] = false;
                        turnChanged.signalAll();
                    } finally {
                        lock.unlock();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        Runnable printB = () -> {
            try {
                for (String value : b) {
                    lock.lockInterruptibly();
                    try {
                        while (aTurn[0]) {
                            turnChanged.await();
                        }
                        out.append(value);
                        aTurn[0] = true;
                        turnChanged.signalAll();
                    } finally {
                        lock.unlock();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        Thread ta = new Thread(printA, "printer-A");
        Thread tb = new Thread(printB, "printer-B");

        // 故意先启动 B，验证输出不依赖“必须先启动 A”。
        tb.start();
        ta.start();

        try {
            ta.join();
            tb.join();
        } catch (InterruptedException e) {
            ta.interrupt();
            tb.interrupt();
            throw e;
        }
        return out.toString();
    }
}
```

在 `B` 先启动的情况下，它拿到锁后看到 `aTurn=true`，于是进入等待；A 随后打印 `1`、切换为 B 并通知。之后状态依次是 `A -> B -> A -> B ...`，因此任意线程调度交错都不能把 `2` 打到 `a` 前面。

## 关键细节

- **来源边界**：原始面经只保存“两个线程交互打印”和目标输出，没有指定同步原语。结构化实体里的 `wait/notify`、`LockSupport` 只能作为候选方案线索，不能冒充原题要求。
- **状态谓词是核心**：通知只负责让等待线程有机会重新竞争锁，`turn` 才决定线程此刻能不能打印。
- **为什么用 `while`**：Java `Condition` 官方文档明确允许 spurious wakeup，并建议在循环里重新检查等待条件；用 `if` 会在虚假唤醒后绕过顺序约束。
- **先改状态再通知**：打印、切换 `turn`、通知都在锁内完成，对方从 `await()` 返回前必须重新获得关联的锁，因此看到的是受同一同步协议保护的状态。
- **不依赖启动顺序**：B 可以先启动；只要 `turn` 初始为 A，B 就不能越权打印。这样避免把线程启动时间当成同步手段。
- **等长契约**：原题两个数组等长。若业务要支持不等长，要先定义剩余元素怎么处理；不能让一边退出后另一边永久等待。
- **中断边界**：外层调用者在 `join()` 时被中断，会中断两个工作线程并把 `InterruptedException` 继续抛出。这个最小示例不把“部分输出”当成成功结果。
- **输出缓冲**：`StringBuilder` 本身不是线程安全容器，但这里每次 `append` 都发生在同一把锁内，因此不需要额外同步；若把输出动作移出锁，必须重新证明顺序与可见性。
- **复杂度**：每边各处理 n 个元素，工作量 O(n)；不计最终输出字符串，同步辅助状态 O(1)。

## 原理机制

可以把程序看成只有两个状态的状态机：

`A_TURN --A打印并切换--> B_TURN --B打印并切换--> A_TURN`

锁保证同一时刻只有一个线程检查和修改这个状态。线程拿到锁后，如果状态不属于自己，就在 `Condition` 上等待；`await()` 会释放关联的锁，返回前重新获得它。另一个线程完成打印后修改状态并发出通知，等待线程醒来后仍要再次检查谓词，所以虚假唤醒、调度延迟或“通知早于正式等待”都不会直接破坏顺序。

为什么通知不会丢成死锁？因为正确性不是“收到一个通知才能打印”，而是“拿到锁后发现 `turn` 属于自己就能打印”。如果 A 在 B 调用 `await()` 之前已经把 `turn` 切成 B 并通知了，那么 B 后续获得锁时会直接看到 `turn=B`，根本不进入等待。这就是“状态 + 条件通知”比把通知本身当状态更可靠的地方。

## 项目经验版

来源没有真实项目经历，不能虚构线上并发事故。项目映射时，我会把这题对应到“多个执行者按协议推进一个共享状态”的场景：先定义状态和允许的转换，再选锁、条件变量、信号量或消息队列实现。工程里还要额外处理超时、中断、任务失败、参与者提前退出和可观测性；不能把一道等长数组的面试题直接扩张成生产级协调器。

## 常见追问

- 问：为什么不能只靠 `sleep` 控制顺序？答：`sleep` 只延迟线程，不建立“轮到谁”的同步条件；机器负载或调度变化后仍可能乱序。
- 问：为什么 `await()` 外面要用 `while` 而不是 `if`？答：条件等待允许虚假唤醒，而且线程醒来后状态也可能已经被其他线程改变；循环重新检查谓词才安全。
- 问：`signal()` 和 `signalAll()` 选哪个？答：这个两线程、单条件队列模型用 `signalAll()` 更直观，醒来的线程仍由 `turn` 筛选；若拆成 A/B 两个 Condition，可以精确 signal 对方，减少无效唤醒。
- 问：用 `wait/notifyAll` 可以吗？答：可以，核心不变量不变：在同一个 monitor 内循环检查 `turn`，打印后切换状态并通知。API 不同，状态机相同。
- 问：用 `LockSupport` 呢？答：也可以用两个线程互相 `unpark`，但仍要定义初始许可、启动时序和中断/退出边界；不能只写一串 `park/unpark` 而不解释状态。
- 问：如果 A、B 长度不一样怎么办？答：原题没有这个场景。工程实现必须先定义剩余元素是直接输出、丢弃还是报错；当前参考契约选择 fail-fast 要求等长，避免一边结束后另一边永久等待。

## 易错点

- 用 `sleep` 或线程启动先后来“保证”交替顺序。
- 把 `await()` 写在 `if` 下，没有防御虚假唤醒。
- 先通知再改变 `turn`，或者把打印放到锁外，却没有重新证明状态和输出的原子关系。
- 只记 `wait/notify`、`Condition`、`LockSupport` 的 API 名称，没有明确共享状态和转换不变量。
- 两边长度不一致时仍按等长循环，导致越界或永久等待。
- 捕获 `InterruptedException` 后完全吞掉中断语义，却把部分输出当成正常成功。
