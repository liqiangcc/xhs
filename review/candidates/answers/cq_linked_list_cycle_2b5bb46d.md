<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_linked_list_cycle_2b5bb46d","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：判断链表是否有环

## 核心结论

判断单链表是否有环用 Floyd 快慢指针：slow 每次走一步、fast 每次走两步；无环时 fast 或 fast.next 为 null，有环时二者必在环内相遇。时间 O(n)、额外空间 O(1)。

## 1 分钟版

- 输入为可能带环的单链表，返回布尔值；不修改 next 指针。
- 循环条件必须同时检查 fast 和 fast.next，避免 fast 两步移动时空指针。
- 若 slow==fast 说明两指针在环中相遇；循环正常结束说明已到 null，无环。
- 不变量是 slow、fast 都沿原 next 链推进；进入环后两者相对距离每轮缩短一，有限环长内必相遇。

## 3 分钟版

fast 每轮比 slow 多走一步。两者都进入长度为 L 的环后，相对位置按模 L 每轮加一，因此至多 L 轮重合。自环、两节点环同样成立；HashSet 方案易解释但额外空间 O(n)，本题通常要求 O(1) 空间。

```java
public final class LinkedListCycle {
    private LinkedListCycle() {}
    public static final class ListNode {
        public final int value; public ListNode next;
        public ListNode(int value) { this.value = value; }
    }
    public static boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }
}
```

## 关键细节

- 输入为可能带环的单链表，返回布尔值；不修改 next 指针。
- 循环条件必须同时检查 fast 和 fast.next，避免 fast 两步移动时空指针。
- 若 slow==fast 说明两指针在环中相遇；循环正常结束说明已到 null，无环。
- 不变量是 slow、fast 都沿原 next 链推进；进入环后两者相对距离每轮缩短一，有限环长内必相遇。
- 测试覆盖 null、单节点无环、自环、两节点环和中部入环。
- 时间 O(n)，额外空间 O(1)。
- 若追问入环点，在相遇后让一个指针回 head、两个都每次一步，再次相遇即入环点；该步骤不是本题主实现。
- 复杂度：时间 O(n)，额外空间 O(1)

## 原理机制

状态是两个只读游标。无环链表的快指针先触达 null；有环链表则在进入环后形成有限状态并以固定相对速度追及。
- 复杂度：时间 O(n)，额外空间 O(1)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么 fast.next 也要检查？答：fast 每轮访问 next.next；只检查 fast 会在单节点尾部空指针。
- 问：自环会相遇吗？答：第一轮 slow 和 fast 都回到同一节点，会返回 true。
- 问：如何找入环点？答：相遇后一个指针回 head，二者同步一步走，再次相遇处是入口。
- 问：HashSet 有何取舍？答：代码直观但需 O(n) 空间；Floyd 空间 O(1)。

## 易错点

- 不要比较节点值，应比较节点引用。
- 不要修改 next 断链来判环。
- 不要遗漏 fast.next 的空检查。
