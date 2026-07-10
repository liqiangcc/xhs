<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_hashmap_d74d2fd7","version":3,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_failure":"missing_evidence"} -->
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

项目映射提示：并发缓存或状态表要说明 key 数量、热点分布、更新模式和一致性要求。单次 Map 操作线程安全不等于“先查再改”整体原子；应优先使用 `compute`、`putIfAbsent`、`merge` 等原子组合，并避免在计算函数中执行阻塞远程调用。

## 常见追问

- 问：ConcurrentHashMap 和 Hashtable 有什么区别？答：Hashtable 主要以整表同步保护操作；CHM 采用更细粒度的 CAS、桶锁和协作扩容，提高并发度。
- 问：JDK 7 和 JDK 8 实现差异？答：JDK 7 以 Segment 分段，JDK 8 改为数组、CAS、桶头 synchronized 和红黑树，不再以 Segment 为核心。
- 问：为什么不允许 null？答：并发场景下 `get` 返回 null 无法区分不存在与值为 null，后续检查又可能发生竞态。
- 问：size 为什么复杂？答：并发更新分散计数，统计需要汇总 baseCount/CounterCell，读取期间仍可能变化，不是业务强一致快照。

## 易错点

- 不要说 JDK 8 仍主要靠 Segment 分段锁。
- 不要把线程安全 Map 误认为业务复合操作天然安全。
- 不要忽略 CAS 失败重试和扩容协助机制。
