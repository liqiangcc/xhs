<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_concurrent_transfer_a35181e0","version":1,"status":"draft","updated_at":"2026-08-18","answer_type":"coding","quality_tier":"candidate"} -->
# 并发转账如何保证原子性并避免死锁？

## 核心结论

单 JVM 内的手撕实现可以给每个账户一把 `ReentrantLock`，并让所有转账都按唯一 `accountId` 的固定全序获取两把锁。余额校验、溢出校验、扣款和入账全部放在两把锁都持有之后执行；成功转账在临界区内一次提交两个余额，失败则两个余额都不变。固定锁序消除了“线程 A 持有账户 1 等账户 2、线程 B 持有账户 2 等账户 1”的循环等待条件。

## 1 分钟版

- 前提：不同逻辑账户必须有不同的稳定 `accountId`；余额和金额都用最小货币单位 `long`，且余额不允许为负。
- 同一账户转给自己直接返回成功且不修改余额；`amount <= 0` 拒绝。
- 两个不同账户按较小 `accountId` 先加锁、较大 `accountId` 后加锁，所有代码路径必须遵守同一顺序。
- 两把锁都拿到后再检查余额和目标余额是否溢出，确认后才同时写两个余额。
- `finally` 中逆序释放锁；异常或余额不足都不能留下半次转账。

## 3 分钟版

先定义两个正确性不变量：第一，任意成功转账前后 `from + to` 的总额保持不变；第二，任何失败返回或异常都不能只改一边。要让并发下仍满足这两个不变量，余额检查与两边写入必须被同一个临界区覆盖，不能在锁外先读余额再决定。

如果两个转账方向可能相反，仅仅“先锁 from 再锁 to”会形成经典死锁：A→B 拿 A 等 B，B→A 拿 B 等 A。解决方式不是依赖线程时序，而是建立全局锁顺序，例如始终先锁较小 accountId。这样所有线程对同一对账户的获取顺序一致，不会形成这类两锁循环等待。

下面的实现还处理两个经常被漏掉的边界：不同账户若错误地使用同一个 accountId，会破坏全序，所以直接拒绝；目标余额加法用 `Math.addExact`，并在真正写入任一余额之前完成溢出检查，避免异常造成半更新。

```java
import java.util.Objects;
import java.util.concurrent.locks.ReentrantLock;

public final class TransferService {
    public static final class Account {
        private final long id;
        private long balanceCents;
        private final ReentrantLock lock = new ReentrantLock();

        public Account(long id, long balanceCents) {
            if (balanceCents < 0) {
                throw new IllegalArgumentException("balance must be non-negative");
            }
            this.id = id;
            this.balanceCents = balanceCents;
        }

        public long id() {
            return id;
        }

        public long balanceCents() {
            lock.lock();
            try {
                return balanceCents;
            } finally {
                lock.unlock();
            }
        }
    }

    public static boolean transfer(Account from, Account to, long amountCents) {
        Objects.requireNonNull(from, "from");
        Objects.requireNonNull(to, "to");
        if (amountCents <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
        if (from == to) {
            return true;
        }
        if (from.id == to.id) {
            throw new IllegalArgumentException("distinct accounts must have distinct ids");
        }

        Account first = from.id < to.id ? from : to;
        Account second = from.id < to.id ? to : from;

        first.lock.lock();
        second.lock.lock();
        try {
            if (from.balanceCents < amountCents) {
                return false;
            }

            long newFrom = from.balanceCents - amountCents;
            long newTo = Math.addExact(to.balanceCents, amountCents);

            from.balanceCents = newFrom;
            to.balanceCents = newTo;
            return true;
        } finally {
            second.lock.unlock();
            first.lock.unlock();
        }
    }

    private TransferService() {}
}
```

## 关键细节

- **原子性范围**：这段代码只保证单 JVM、同一组 `Account` 对象上的内存原子性；数据库账户、跨 JVM 或跨服务转账必须把业务事实放进数据库事务、条件更新/版本约束和幂等流水中，不能把进程内锁当成分布式事务。
- **锁顺序是协议**：固定顺序只有在所有会同时锁多个账户的路径都遵守时才成立；另一个路径若反向加锁，仍可能重新引入死锁。
- **失败不修改**：余额不足直接 `false`；目标余额溢出会在两边赋值前抛出 `ArithmeticException`，源账户不会先被扣款。
- **可见性**：账户余额的读取和修改都通过同一把锁保护；`Lock` 的成功加锁/解锁具有与内置 monitor 对应的内存同步语义。
- **复杂度**：不计锁等待，每次转账做常数次查验和赋值，时间 O(1)、额外空间 O(1)；在竞争下实际延迟取决于锁等待与调度。
- **金额类型**：示例使用最小货币单位 `long`；若业务需要小数比例、利息或跨币种舍入，应使用明确 scale/rounding 规则的 `BigDecimal` 或专门 Money 类型。

## 原理机制

两把锁都持有时，其他遵守同一锁协议的线程无法同时修改这两个账户，所以检查和写入形成一个受保护状态转换。固定 accountId 顺序把“我要哪把锁”从调用方向中解耦：无论 A→B 还是 B→A，对账户 A/B 的物理加锁顺序都相同，因此不会出现相反顺序造成的环形等待。

`try/finally` 负责释放语义，而不是原子性本身；真正保证“失败不半更新”的关键是先完成所有可能失败的校验和 `Math.addExact` 计算，再执行两个赋值。这样成功路径一次跨过状态边界，失败路径保持原状态。

## 项目经验版

面试手撕时可以先声明这是“单 JVM 内存模型”的实现，再写出两个不变量和统一锁序，最后用并发反向转账、余额不足、同账户、重复 ID、加法溢出五类用例验证。若追问生产账务，应主动切换到数据库事务、幂等请求号、账务流水、对账与故障恢复，而不是声称 `ReentrantLock` 能覆盖跨进程一致性。

## 常见追问

- 问：为什么“先锁 from 再锁 to”不够？答：两个线程做 A→B 和 B→A 时会分别先持有不同账户，再等待对方持有的账户，形成循环等待；固定全序让两个方向都按同一物理顺序拿锁。
- 问：为什么不能在锁外先判断余额够不够？答：判断后到真正扣款之间可能被其他线程改余额，造成超扣；检查与修改必须处于同一临界区。
- 问：`tryLock` 能替代固定锁序吗？答：可以设计超时、失败释放和退避重试以避免无限等待，但重试策略更复杂，还要处理饥饿与幂等；本题两账户固定全序更直接。
- 问：数据库里还需要这两把 JVM 锁吗？答：通常不能依赖它们保证正确性。多实例会各自持有不同锁，核心正确性应由数据库事务、行锁/条件更新、唯一流水与幂等约束保证。
- 问：为什么先算 `newTo` 再写余额？答：`Math.addExact` 可能抛出溢出异常；先完成所有可能失败的计算，再写两个字段，才能保持异常路径不半更新。

## 易错点

- 不要让相反方向的转账按调用参数顺序拿锁。
- 不要允许两个不同账户共享同一个排序 ID，否则“全序”并不成立。
- 不要先扣源账户，再做可能失败的目标余额溢出检查。
- 不要只在写余额时加锁，却把余额检查放在锁外。
- 不要把单 JVM `ReentrantLock` 的正确性外推成跨服务或数据库事务语义。
