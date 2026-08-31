<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ad98fcd2a28e860ad42d11065af2caea","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 双向链表版 LRU 缓存

## 核心结论

“双向链表版 LRU”不能只靠链表完成：链表负责维护最近使用顺序，`HashMap` 负责按 key 在期望 `O(1)` 时间定位节点。这里声明一个可执行 Java 契约：`capacity > 0`；`get(int key)` 命中时返回 `Integer` 并把节点移动到 MRU 端，未命中返回 `null`；`put(int key, int value)` 插入或更新并刷新 recency；容量超限时淘汰 LRU 端节点。链表使用 `head/tail` 两个哨兵，真实节点始终满足“每个缓存项恰好一个 Map 条目 + 一个链表节点”，从 `head.next` 到 `tail.prev` 是 MRU → LRU。

## 1 分钟版

- `HashMap<Integer, Node>` 解决 key 定位，双向链表解决 recency 排序；两者缺一不可。
- 约定头部是 MRU、尾部是 LRU；`get` 命中和 `put` 更新都要把节点摘下再插到头部。
- `put` 新 key 后若超容量，就删除 `tail.prev`，并同步从 Map 删除同一个 key。
- 双向链表能在已知节点时直接利用 `prev/next` 做 `O(1)` 摘链；单链表通常还要找前驱。
- 哨兵节点把首尾插入、删除统一成固定的指针重连，减少边界分支和空指针错误。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

public final class LRUCache {
    private static final class Node {
        final int key;
        int value;
        Node prev;
        Node next;

        Node(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }

    private final int capacity;
    private final Map<Integer, Node> index = new HashMap<>();
    private final Node head = new Node(0, 0);
    private final Node tail = new Node(0, 0);

    public LRUCache(int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("capacity must be positive");
        }
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public Integer get(int key) {
        Node node = index.get(key);
        if (node == null) return null;
        touch(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node node = index.get(key);
        if (node != null) {
            node.value = value;
            touch(node);
            return;
        }

        Node created = new Node(key, value);
        index.put(key, created);
        linkAfterHead(created);

        if (index.size() > capacity) {
            Node victim = tail.prev;
            unlink(victim);
            index.remove(victim.key);
        }
    }

    public int size() {
        return index.size();
    }

    private void touch(Node node) {
        unlink(node);
        linkAfterHead(node);
    }

    private void linkAfterHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private static void unlink(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
        node.prev = null;
        node.next = null;
    }
}
```

以容量 2 为例：`put(1, 10)`、`put(2, 20)` 后链表是 `[2, 1]`；`get(1)` 后变成 `[1, 2]`；再 `put(3, 30)` 时淘汰 `2`。这里最关键的不是记代码，而是每次操作都维持 Map 与链表的一致性，以及 MRU → LRU 的顺序不变量。

## 关键细节

- **摘链顺序**：`unlink` 要同时改前驱的 `next` 和后继的 `prev`；漏一边会让链表正向、反向视图不一致。
- **重新插头部**：节点先从原位置摘掉，再 `linkAfterHead`；如果直接重复插入，会出现同一节点被两段链路引用。
- **更新已有 key**：只改 value 不够，更新也代表一次使用，因此还要刷新到 MRU；元素数量不能增加。
- **淘汰同步性**：`tail.prev` 是 LRU victim。摘链后必须从 Map 删除同一个 key，否则后续 `get` 会拿到已脱链节点。
- **容量 1**：哨兵让“删除唯一真实节点 + 插入新节点”仍走同一套指针操作，不需要单独写首尾分支。
- **复杂度口径**：链表摘插是严格 `O(1)` 指针操作；Map 查找/写入按 Java `HashMap` 的常见期望 `O(1)` 讨论，所以整体常见情况下 `get/put` 为期望 `O(1)`，空间 `O(capacity)`。

## 原理机制

LRU 实际维护的是一个“最近使用有序集合”。Map 给出 `key -> Node`，因此命中后可以直接拿到链表节点；双向链表则把每个节点的前后邻居显式保存下来，所以已知节点时可以不扫描前驱就完成摘链。每次命中或更新都执行 `unlink -> linkAfterHead`，把该节点提升到 MRU；新增后若超容量，`tail.prev` 天然就是最久未使用节点。

两个数据结构之间的核心不变量是：Map 的 key 集合与链表真实节点的 key 集合完全相同，而且每个 key 只出现一次。任何 `get/put/evict` 路径都必须同时保持“集合一致性”和“顺序正确性”。一旦只更新其中一个结构，后续操作就会出现幽灵索引、重复节点或错误淘汰。

## 项目经验版

来源没有给真实项目里的并发模型、TTL、容量单位、淘汰回调或命中率数据，所以不能虚构线上经验。工程落地时还要先明确这些语义：如果多个线程共享结构，需要额外同步；如果容量按字节或权重而不是条目数计算，需要把“超容量”判定改成权重累计；若还带 TTL，则“过期”和“LRU 淘汰”是两个不同维度。这里严格保留为单线程、按条目数容量的手撕算法契约。

## 常见追问

- 问：为什么双向链表比单链表更适合？答：Map 已经定位到目标节点，双向链表有 `prev`，可以直接在 `O(1)` 摘掉；单链表通常还需要找到前驱。
- 问：为什么要两个哨兵节点？答：它把空链表、首节点、尾节点的插入删除统一成同一组指针重连，减少特殊分支。
- 问：`get` 为什么也要改链表？答：LRU 的“最近使用”包含读取命中；如果读取不刷新，淘汰顺序就不再是 LRU。
- 问：更新已有 key 为什么不增加 size？答：它仍是同一个缓存项，只替换 value 并刷新 recency；创建第二个节点会破坏一 key 一节点不变量。
- 问：为什么淘汰时 Map 也必须删除？答：链表和 Map 表示同一组缓存项；只摘链不删 Map 会留下指向脱链节点的失效索引。
- 问：这个实现线程安全吗？答：不是。来源只要求手撕双向链表版 LRU；并发共享时必须额外定义锁粒度或使用经过验证的并发缓存实现。

## 易错点

- `unlink` 只修改一个方向的指针，导致双向链表结构损坏。
- `touch` 前不摘掉旧位置，造成一个节点在链表中重复出现。
- `get` 命中不刷新 recency，实际行为退化成接近 FIFO。
- 更新已有 key 时误增 size 或新建第二个节点。
- 淘汰时只删链表或只删 Map，破坏两个结构的集合一致性。
- 容量 1、空链表等边界单独拼大量 if 分支，而不是用哨兵统一操作。
