<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_arraylist_9d3444a1","version":1,"status":"ready","updated_at":"2026-06-30"} -->
# ArrayList和linkedList的区别

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

业务列表、分页结果、批处理集合通常用 ArrayList。需要队列语义时优先 ArrayDeque。很少直接选择 LinkedList，除非明确需要频繁在链表两端操作且不关心随机访问。

## 常见追问

- ArrayList 扩容机制是什么？
- 为什么 LinkedList 插入删除不一定快？
- ArrayList 和 Vector 区别是什么？
- 队列场景为什么推荐 ArrayDeque？

## 易错点

- 不要简单背“LinkedList 增删快”，要说明定位成本。
- 不要忽略内存占用和缓存局部性。
- 不要说 ArrayList 线程安全。
