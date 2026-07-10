<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_stringbuffer_8b8caf0d","version":3,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_failure":"missing_evidence"} -->
# StringBuilder和StringBuffer的区别

## 核心结论

StringBuilder 和 StringBuffer 都是可变字符序列，主要区别是 StringBuffer 的关键方法加了 synchronized，线程安全但性能开销更高；StringBuilder 不保证线程安全，单线程字符串拼接更常用。

## 1 分钟版

String 是不可变对象，频繁拼接会产生新对象。StringBuilder 和 StringBuffer 内部维护可扩容字符数组，append 时尽量复用同一个对象。StringBuffer 的 append、insert 等方法带同步，适合多线程共享同一个缓冲区的场景。StringBuilder 没有同步开销，适合方法内部局部变量拼接，也是日常最常用选择。

## 3 分钟版

二者都继承自 AbstractStringBuilder，底层核心都是数组加长度计数，容量不足时扩容并复制旧内容。区别集中在同步语义：StringBuffer 对公开方法做 synchronized，保证多个线程同时操作同一实例时内部结构不会被破坏；StringBuilder 不加锁，所以吞吐更高。实际业务中，多线程通常不会共享同一个字符串构建器，而是每个线程自己构造，因此 StringBuilder 更常见。

## 关键细节

- String 不可变，Builder 和 Buffer 可变。
- StringBuffer 线程安全，StringBuilder 非线程安全。
- 单线程优先 StringBuilder。
- 编译器会把简单字符串加号优化为 StringBuilder。

## 原理机制

- 可变数组减少中间字符串对象创建。
- 扩容时会申请更大数组并复制旧字符。
- synchronized 保证互斥访问，但带来锁开销。

## 项目经验版

项目映射提示：方法内日志、SQL 片段或导出文本通常使用 StringBuilder；若真实存在共享拼接，先说明为什么不能线程隔离，再评估外层锁或 StringBuffer。不能把单个方法同步等同于一整段业务拼接原子。

## 常见追问

- 问：String 为什么不可变？答：字符内容创建后不能修改，便于常量池复用、hash 缓存、安全传递和并发共享；拼接会创建新对象或由编译器优化。
- 问：字符串加号和 StringBuilder 什么关系？答：编译器可能把同一表达式拼接优化为 StringBuilder 或 `invokedynamic`，循环中跨迭代拼接仍需检查对象分配。
- 问：StringBuffer 线程安全就保证业务安全吗？答：只保证单次方法同步，多个调用组合仍可能被其他线程插入。
- 问：StringBuilder 如何扩容？答：AbstractStringBuilder 会按增长策略申请更大数组并复制，具体实现需绑定 JDK 版本；预估容量可减少复制。

## 易错点

- 不要说 StringBuffer 一定比 StringBuilder 好。
- 不要把对象内部线程安全等同于业务整体线程安全。
- 不要忽略 String 不可变带来的中间对象成本。
