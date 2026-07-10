<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_concurrent_transfer_a35181e0","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# 并发转账如何保证原子性并避免死锁？

## 核心结论

并发转账要让扣款与入账原子，并对两个账户按稳定顺序加锁防死锁；余额检查和修改必须在锁内，生产系统还需要事务、幂等流水和金额类型。

## 1 分钟版

- 按 accountId 小到大获取两把锁，所有转账路径遵守同一顺序。
- 锁内检查余额并同时更新两账户，finally 逆序释放。
- 同一账户直接返回；实际金额用 long 最小货币单位或 BigDecimal。

## 3 分钟版

不变量是任意成功转账前后两账户总额不变且余额不越过业务下限。内存锁只保护单进程对象，分布式/数据库账户必须使用数据库事务与版本约束。 先声明输入约束和不变量，再逐步推导实现；最后给出复杂度、空值/极值用例和至少一个变体。

```java
import java.util.concurrent.locks.*;
class Account { final long id; long cents; final Lock lock=new ReentrantLock(); Account(long id,long c){this.id=id;this.cents=c;} }
class Transfer {
  static boolean move(Account from, Account to, long amount){
    if(from==to) return true; if(amount<=0) throw new IllegalArgumentException();
    Account first=from.id<to.id?from:to, second=first==from?to:from;
    first.lock.lock(); second.lock.lock();
    try { if(from.cents<amount) return false; from.cents-=amount; to.cents+=amount; return true; }
    finally { second.lock.unlock(); first.lock.unlock(); }
  }
}
```

## 关键细节

- 按 accountId 小到大获取两把锁，所有转账路径遵守同一顺序。
- 锁内检查余额并同时更新两账户，finally 逆序释放。
- 同一账户直接返回；实际金额用 long 最小货币单位或 BigDecimal。
- 基础实现假设账户对象在单 JVM 内唯一，账户 ID 可全序比较。
- 复杂度：除锁等待外每次转账 O(1)，额外空间 O(1)

## 原理机制

正确性由循环/状态不变量保证；每次迭代只做保持不变量的局部更新，结束条件把局部结论扩展到完整输入。 并发转账要让扣款与入账原子，并对两个账户按稳定顺序加锁防死锁；余额检查和修改必须在锁内，生产系统还需要事务、幂等流水和金额类型。
- 复杂度：除锁等待外每次转账 O(1)，额外空间 O(1)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么按 ID 加锁？答：建立全局锁顺序，消除 A 等 B、B 等 A 的循环等待。
- 问：tryLock 有什么用？答：可加超时和退避避免长等，但失败重试仍需保证幂等。
- 问：多 JVM 怎么办？答：使用数据库事务/条件更新或一致协调，不可依赖进程内 Lock。

## 易错点

- 不要只给代码而不解释不变量。
- 不要遗漏复杂度、空输入和变体。
- 不要在锁外检查余额。
