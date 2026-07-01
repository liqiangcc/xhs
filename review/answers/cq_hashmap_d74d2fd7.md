<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_hashmap_d74d2fd7","version":1,"status":"ready","updated_at":"2026-07-01"} -->
# ConcurrentHashMap原理

## 核心结论

ConcurrentHashMap 是线程安全的高并发 Map。JDK 8 主要通过 CAS、synchronized 锁桶头节点、volatile 可见性、分段计数和协助扩容来降低锁粒度，保证并发读写性能。

## 1 分钟版

JDK 8 的 ConcurrentHashMap 底层也是数组加链表或红黑树。读操作大多不加锁，依赖 volatile 保证可见性。写入时如果桶为空，用 CAS 放入节点；如果桶不为空，锁住桶头节点后在链表或树中插入。扩容时会放置 ForwardingNode 标记迁移，其他线程遇到后可以一起帮忙迁移，减少单线程扩容阻塞。

## 3 分钟版

JDK 7 的 ConcurrentHashMap 使用 Segment 分段锁，JDK 8 取消固定 Segment，改为更细粒度的桶级同步。put 流程先计算 hash，初始化 table 后定位桶位，空桶走 CAS，非空桶进入 synchronized。链表过长会树化，提升极端冲突下的查找效率。size 统计不是简单全局锁，而是 baseCount 加 CounterCell 的方式，类似 LongAdder，降低高并发计数竞争。扩容过程中每个线程可以领取一段桶迁移任务，迁移完成后切换到新表。

## 关键细节

- get 通常不加锁。
- put 不是全表锁，而是桶级别锁。
- JDK 8 不再使用 JDK 7 那种 Segment 分段锁作为核心结构。
- key 和 value 都不允许为 null，避免并发语义歧义。

## 原理机制

- CAS 处理空桶写入和计数更新。
- synchronized 锁住桶头节点，控制局部写冲突。
- volatile 保证 table、节点 value 和 next 的可见性。
- ForwardingNode 标识扩容迁移状态。

## 项目经验版

项目里 ConcurrentHashMap 适合本地缓存、并发状态表、幂等处理记录等场景。但它只保证单次 Map 操作线程安全，如果是“先查再改”的复合逻辑，要用 compute、putIfAbsent、merge 等原子方法，或者在业务层额外加锁。

## 常见追问

- ConcurrentHashMap 和 Hashtable 有什么区别？
- JDK 7 和 JDK 8 的实现差异是什么？
- 为什么 ConcurrentHashMap 不允许 null？
- size 为什么不是强一致的简单计数？

## 易错点

- 不要说 JDK 8 仍主要靠 Segment 分段锁。
- 不要把线程安全 Map 误认为业务复合操作天然安全。
- 不要忽略 CAS 失败重试和扩容协助机制。
