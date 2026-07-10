<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_lru_cache_0ef78597","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"coding","quality_tier":"candidate"} -->
# 算法：实现 LRU Cache

## 核心结论

用 `HashMap<Integer, Node>` 做 key 到节点的 O(1) 定位，用带哨兵的双向链表维护访问顺序：`head.next` 是最近使用（MRU），`tail.prev` 是最久未使用（LRU）。每次 `get` 或命中后的 `put` 都把节点移到头部；插入后超出容量就删除尾部节点，因此 `get` 与 `put` 均为 O(1)。

## 1 分钟版

- 约束：容量 `capacity >= 0`；`get` 未命中返回 `-1`；容量为 0 时 `put` 不保存任何键。
- 不变量：Map 中的每个 key 恰好对应链表中的一个真实节点；哨兵 `head`、`tail` 不进 Map；从头到尾按“新到旧”排列。
- `get(key)`：Map 找不到返回 `-1`，找到则摘下再插到头部，并返回 value。
- `put(key, value)`：已存在时更新 value 并移到头部；不存在时新建并插头，若超容量则淘汰 `tail.prev` 并同步从 Map 删除。

## 3 分钟版

先把双向链表的职责限定为“顺序”，把 HashMap 的职责限定为“定位”。两个哨兵让插入头部、删除任意节点、删除尾部都不需要为首尾节点写分支。

正确性依赖两个不变量：第一，Map 与真实链表节点一一对应；第二，任一节点被访问后都移动到头部，所以尾部节点一定是自上次访问以来最久未使用的节点。`get` 只改变顺序而不改变键集合；已有键的 `put` 也只更新值与顺序；新键 `put` 先同时加入 Map 和头部，超过容量时只删除尾部真实节点及其 Map 条目，因此不变量持续成立。

下面实现刻意不使用 `LinkedHashMap`，以展示淘汰节点、Map 与链表同步更新的细节；它不是线程安全缓存，多个线程并发调用时要由调用方加锁，或改用有明确并发与淘汰语义的缓存组件。

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
    private final Map<Integer, Node> byKey = new HashMap<>();
    private final Node head = new Node(0, 0);
    private final Node tail = new Node(0, 0);

    public LRUCache(int capacity) {
        if (capacity < 0) {
            throw new IllegalArgumentException("capacity must be non-negative");
        }
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        Node node = byKey.get(key);
        if (node == null) {
            return -1;
        }
        moveToFront(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node existing = byKey.get(key);
        if (existing != null) {
            existing.value = value;
            moveToFront(existing);
            return;
        }
        if (capacity == 0) {
            return;
        }
        Node created = new Node(key, value);
        byKey.put(key, created);
        addFirst(created);
        if (byKey.size() > capacity) {
            Node lru = tail.prev;
            unlink(lru);
            byKey.remove(lru.key);
        }
    }

    private void moveToFront(Node node) {
        unlink(node);
        addFirst(node);
    }

    private void addFirst(Node node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }

    private void unlink(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
}
```

## 关键细节

- 时间复杂度：`get`、`put` 都是 O(1) 平均时间；空间为 O(capacity)。这里的 O(1) 依赖 HashMap 的平均查找成本，不能表述为所有哈希实现与所有攻击模型下的绝对最坏界。
- 容量为 0 是必须单独处理的边界；否则新节点会被插入再淘汰，虽然最终正确，但不必要地修改结构。
- 更新已有 key 时不能只改 value；它也属于一次访问，必须刷新为 MRU。
- 淘汰时必须同时断开链表节点并从 Map 删除，否则会产生陈旧索引或容量错误。
- 已声明的边界测试覆盖：容量为 1 的淘汰、`get` 刷新顺序、更新已有键、容量为 0，以及负容量拒绝。

## 原理机制

状态从“Map + 链表按新到旧排序”开始。命中读或命中写会执行 `unlink(node)` 再 `addFirst(node)`，键集合不变但访问顺序更新。插入新键会让键集合增加一个；如果超过容量，`tail.prev` 是唯一需要淘汰的最旧节点，删除它的两个指针连接并删除对应 Map 条目，状态回到容量约束内。哨兵保证这些局部操作在空缓存、单节点和多节点时具有同一种指针形状。

## 项目经验版

算法训练时可先口述 Map 与链表的一一对应关系，再手写 `get`、已有键 `put`、新键淘汰三条路径，并用容量 0 和容量 1 走查。面试若追问生产缓存，应先澄清并发、过期、大小计量和持久化需求；这份实现只解决固定条目数的 LRU 淘汰。

## 常见追问

- 问：为什么单链表加 HashMap 不够？答：命中节点后需要在 O(1) 时间从任意位置删除并移到头部；单链表通常找不到前驱，删除会退化。
- 问：`get` 为什么也要移动节点？答：LRU 的“最近使用”包括读取；不移动会把刚读取的节点错误地保留在淘汰端。
- 问：已有 key 的 `put` 为什么不能让 size 增加？答：它只更新已有节点的 value 和访问时间，Map 与链表的一一对应关系不应新增节点。
- 问：能否用 `LinkedHashMap`？答：可以将其设为 access-order 并在超过容量时淘汰最旧项，代码更短；手撕题通常要求展示双向链表与 HashMap 的同步不变量。
- 问：这段代码能直接用于多线程缓存吗？答：不能。复合的“查找—移动/插入—淘汰”操作必须整体同步；还要单独定义过期、容量计量和高并发下的淘汰策略。

## 易错点

- 不要把 Map 当作顺序结构；它只负责按 key 定位节点。
- 不要遗漏更新已有键后的移头操作。
- 不要删除链表节点却忘记删除 Map 条目，或反过来只删 Map。
- 不要把这份固定容量、非线程安全的手撕实现描述成完整生产缓存方案。
