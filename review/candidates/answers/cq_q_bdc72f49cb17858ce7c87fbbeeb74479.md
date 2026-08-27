<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_bdc72f49cb17858ce7c87fbbeeb74479","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# i=0，两个线程同时执行 i++，最终 i 可能是多少？

## 核心结论

在原题的 Java 并发上下文里，如果补齐最小前提——共享的是普通 `int i=0`，两个线程各执行一次 `i++`，没有 `synchronized`/原子类等额外同步，并且主线程在两个线程 `join` 后读取结果——**最终可能是 1 或 2**。原因不是 `int` 单次读写会“撕裂”，而是 `i++` 本身是读-加一-写回的复合读改写操作，不具备整体原子性：两个线程都先读到 0 再各自写 1 会丢失一次更新；若一个线程的写 1 被另一个线程后续读到，第二次写回 2。

## 1 分钟版

- `i++` 可以按语义拆成：读取 `i` → 计算 `old + 1` → 写回 `i`。
- 交错一：T1 读 0，T2 读 0，T1 写 1，T2 写 1，最终 **1**。
- 交错二：T1 读 0 写 1，T2 再读 1 写 2，最终 **2**。
- 两个线程对普通共享变量的冲突访问没有 happens-before 排序，程序存在 data race；不能把一次 `i++` 当成一个不可分割动作。
- 把 `i` 改成 `volatile` 仍不能保证最终 2：volatile 保证单次读写的可见性/顺序语义，不会把“读 + 加 + 写”合并成原子 RMW。
- 要保证结果 2，用 `synchronized`/`Lock` 把整个 `i++` 包起来，或用 `AtomicInteger.incrementAndGet()` 这样的原子更新。

## 3 分钟版

```java
import java.util.concurrent.atomic.AtomicInteger;

public final class IncrementRace {
    static int i;

    static void unsafeIncrement() {
        i++;
    }

    static int synchronizedTwice() throws InterruptedException {
        i = 0;
        Object lock = new Object();
        Thread t1 = new Thread(() -> { synchronized (lock) { i++; } });
        Thread t2 = new Thread(() -> { synchronized (lock) { i++; } });
        t1.start(); t2.start();
        t1.join(); t2.join();
        return i;
    }

    static int atomicTwice() throws InterruptedException {
        AtomicInteger value = new AtomicInteger(0);
        Thread t1 = new Thread(value::incrementAndGet);
        Thread t2 = new Thread(value::incrementAndGet);
        t1.start(); t2.start();
        t1.join(); t2.join();
        return value.get();
    }
}
```

对 `unsafeIncrement()` 做 `javap -c`，可以直接看到读取静态字段、常量 1、整数加法、写回静态字段是多个字节码步骤，而不是一个原子“加一”指令。字节码分解本身不等于完整的 Java 内存模型证明，但很直观地说明为什么必须把 `i++` 当复合操作分析。

## 关键细节

- **为什么不是只有 2**：两个线程都可能基于同一个旧值 0 计算 1，后一次写 1 覆盖前一次写 1，产生 lost update。
- **为什么不是 0**：在这里明确了两个线程都完成并且主线程 `join` 后再读；每个 `i++` 的写回值至少是基于它读到的整数加 1。对这个两次自增契约，典型合法结果是 1 或 2，而不是“因为有 data race 所以任何 int 都可能”。
- **`int` 单次访问与 `i++` 要分开**：问题的核心是复合 RMW 不是原子的，不能把它误讲成 32 位 `int` 写入本身会被拆成两半。
- **`volatile i++` 仍有 lost update**：两个 volatile read 都可能先读到 0，随后两个 volatile write 都写 1。volatile 解决的是可见性/排序边界，不自动给复合表达式加互斥。
- **`join` 的作用**：它保证主线程在两个 worker 结束后再观察结果；若主线程不等待完成就提前读取，那讨论的是另一个契约，可能看到初始化值或中间状态。
- **修复粒度**：锁必须覆盖整个读-改-写；只给读或写单独加锁没有意义。计数器这种单变量更新通常可以直接使用 `AtomicInteger` 的原子 RMW。

## 原理机制

并发正确性要看冲突访问之间有没有 happens-before 关系。普通共享 `i` 上，一个线程的写和另一个线程的读/写没有同步边，因此是 data race。每个线程内部仍有自己的程序顺序，但两个线程的复合 `i++` 可以互相穿插，于是“两个逻辑操作”不再等价于串行执行两次。

`synchronized` 的解法是建立互斥和 monitor 的同步边，使某个线程完成整个 `i++` 后另一个线程才能进入；`AtomicInteger.incrementAndGet()` 则直接提供单变量的原子 read-modify-write。两种方案都把“读取旧值并写入新值”变成不会丢更新的一个同步操作，只是适用的状态范围和实现机制不同。

## 项目经验版

来源没有真实线上计数器故障或性能数据，不能虚构。实际排查类似问题时，我会先确认共享变量是不是普通字段、volatile、锁保护还是原子类，再确认读取最终值前是否有 join/future/锁等完成边界；复现时用高并发循环扩大 lost update 概率，但不会把“某次压测没复现”当成线程安全证明。

## 常见追问

- 问：`volatile int i; i++` 安全吗？答：不安全。volatile read/write 有可见性和顺序语义，但 `i++` 仍是读改写复合操作，两线程仍可丢更新。
- 问：`AtomicInteger` 为什么可以？答：它提供原子更新方法，例如 `incrementAndGet()`，把单变量加一作为原子 read-modify-write 完成。
- 问：如果加 `synchronized` 最终是多少？答：两个线程各完成一次受同一把锁保护的 `i++`，并在都结束后读取，最终就是 2。
- 问：`join()` 能让 `i++` 变原子吗？答：不能。join 只给“worker 已发生的动作 → join 返回后的主线程动作”建立完成/可见性边界，不会给两个 worker 彼此之间的 `i++` 建互斥。
- 问：实际跑很多次只看到了 2，能证明安全吗？答：不能。并发 bug 的可发生性由同步语义决定，不由一次或若干次调度样本决定；测试只能作为证据补充。

## 易错点

- 直接说 `i++` 是原子操作，所以结果只能是 2。
- 把 `volatile` 当互斥锁，认为加 volatile 后复合自增就原子了。
- 只说“线程不安全”却不画出 T1/T2 读写交错，无法解释为什么会得到 1。
- 把 `int` 单次读写的原子性和 `i++` 整体原子性混为一谈。
- 忽略“最终结果何时读取”的前提；不等待线程结束时，问题已经不是原来的两次自增终态。
- 因为数据竞争存在就宣称“任何整数都有可能”，忽略表达式、每线程程序顺序和 Java 内存模型仍然对行为有约束。
