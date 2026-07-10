<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_arraylist_9d3444a1","version":2,"status":"ready","updated_at":"2026-07-10"} -->
# ArrayList 和 LinkedList 的区别

## 核心结论

ArrayList 底层是动态数组，随机访问快，尾部追加性能好，但中间插入删除需要搬移元素。LinkedList 底层是双向链表，理论上已定位节点后插入删除快，但随机访问慢，节点对象额外内存开销大，实际业务中 ArrayList 更常用。

## 1 分钟版

ArrayList 支持 O(1) 下标访问，扩容时会申请新数组并复制旧元素。中间插入或删除平均 O(n)，因为要移动后续元素。LinkedList 每个节点保存前驱、后继和元素，按下标访问需要遍历，复杂度 O(n)；如果已经拿到节点，插入删除是 O(1)。但 Java 的 LinkedList 缓存局部性差、对象开销大，所以除非频繁在头尾操作，否则通常优先用 ArrayList。

## 3 分钟版

对比可以从结构、访问、增删、内存和场景回答。ArrayList 是连续内存逻辑结构，CPU 缓存友好，按 index 访问快；扩容一般按比例扩容，会有数组复制成本。LinkedList 是链式结构，每个节点额外保存 prev/next 指针，内存占用更高，GC 压力也更大。很多人以为 LinkedList 插入删除一定快，但如果要先按下标找到位置，定位就是 O(n)，整体不一定优于 ArrayList。队列场景也更推荐 ArrayDeque。

## 关键细节

- ArrayList 查询快，插入删除可能搬移元素。
- LinkedList 定位慢，节点额外内存多。
- ArrayList 扩容有复制成本，但摊还追加复杂度仍接近 O(1)。
- 多线程场景二者都不是线程安全集合。

## 原理机制

- ArrayList 使用 Object[] 存储。
- LinkedList 使用 Node 链接前后节点。
- CPU 缓存局部性让数组结构在实际运行中通常更快。

## 项目经验版

项目映射时优先说明真实访问模式：业务列表、分页结果、批处理集合通常选 ArrayList；队列语义优先 ArrayDeque。只有确认需要频繁在两端操作、无需随机访问，并通过压测证明合适时才考虑 LinkedList，不要虚构实际使用经历。

## 常见追问

- 问：ArrayList 扩容机制是什么？答：首次真正添加元素时分配数组；容量不足时创建更大的数组并复制元素。常见 JDK 实现按约 1.5 倍增长，具体细节要结合版本说明。
- 问：为什么 LinkedList 插入删除不一定快？答：只有已经定位到节点时改指针才是 O(1)；按下标查找节点仍需 O(n)，再加上对象分配和缓存局部性差，实际可能更慢。
- 问：ArrayList 和 Vector 的区别是什么？答：Vector 的多数方法带同步，单次调用线程安全但组合操作仍需额外同步；现代代码通常按场景选 ArrayList、并发集合或外部同步。
- 问：队列场景为什么推荐 ArrayDeque？答：它用循环数组实现双端操作，通常比 LinkedList 更省内存、缓存更友好，也不允许 null，能减少语义歧义。

## 易错点

- 不要简单背“LinkedList 增删快”，要说明定位成本。
- 不要忽略内存占用和缓存局部性。
- 不要说 ArrayList 线程安全。
- 复习反馈：回答复杂度时必须拆成“按下标访问”和“先定位再增删”；LinkedList 已知节点后的修改可 O(1)，按索引定位仍是 O(n)。
