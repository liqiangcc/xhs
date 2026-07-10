<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_synchronized_volatile_2801d05c","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# synchronized 和 volatile 的区别

## 核心结论

volatile 保证单个变量读写的可见性与规定的有序性，但不保证读改写复合操作原子；synchronized 还提供互斥和临界区原子性，并在解锁/加锁间建立 happens-before。

## 1 分钟版

- volatile 适合状态标志、单写多读或独立原子赋值，不适合 `count++`。
- synchronized 同一 monitor 下保护多个变量的不变量，并自动释放锁。
- volatile 读写通过内存语义限制重排序；不等于把所有工作内存立即清空。

## 3 分钟版

双重检查单例的 instance 需要 volatile 防止发布重排序，但构造和复合状态仍依赖正确同步。性能按竞争与临界区测试。 回答时先统一比较维度，再给选择条件与反例；定义本身不是终点，必须说明代价和不适用边界。

## 关键细节

- volatile 适合状态标志、单写多读或独立原子赋值，不适合 `count++`。
- synchronized 同一 monitor 下保护多个变量的不变量，并自动释放锁。
- volatile 读写通过内存语义限制重排序；不等于把所有工作内存立即清空。

## 原理机制

从参与对象、状态变化和主流程展开，再补充并发/故障保证与资源开销。 volatile 保证单个变量读写的可见性与规定的有序性，但不保证读改写复合操作原子；synchronized 还提供互斥和临界区原子性，并在解锁/加锁间建立 happens-before。

## 项目经验版

项目映射提示：从真实代码或架构中选择一个使用点，补齐选择条件、替代方案和验证指标；没有事实时不虚构收益。

## 常见追问

- 问：volatile 能保证 long 原子吗？答：现代 Java 对 long 单次读写已有原子保证，volatile 的重点是可见性/有序性；复合操作仍不原子。
- 问：count++ 为什么不安全？答：它包含读、加、写，多线程会丢失更新。
- 问：何时用 AtomicInteger？答：单变量原子更新且冲突可控时，复杂跨变量不变量仍需锁。

## 易错点

- 不要只背定义而不说明选择条件。
- 不要把常见实现说成跨版本唯一结论。
- 不要把可见性等同于业务线程安全。
