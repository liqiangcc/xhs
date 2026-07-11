<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_77ee33f1","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：反转链表

## 核心结论

反转单链表用三个指针迭代即可：prev 保存已反转前缀，current 指向未处理首节点；每轮先保存 next，再把 current.next 指向 prev，最后同时推进 prev 和 current。必须先保存 next，否则会丢失未处理后缀。

## 1 分钟版

- 输入是单链表头结点，输出是反转后的新头；null 和单节点直接返回原引用。方法原地修改 next 指针。
- 初始化 prev=null、current=head；循环不变量是 prev 指向已完整反转的前缀，current 指向尚未修改的后缀首节点。
- 每轮按 next=current.next、current.next=prev、prev=current、current=next 的顺序执行，直到 current 为 null。
- 循环结束时未处理后缀为空，prev 覆盖原链表所有节点，因此 prev 是新头。

## 3 分钟版

每个节点只访问一次。若先改 current.next 而未保存原 next，会失去后继节点引用；这是该题最常见的断链错误。迭代法不使用递归栈，适合超长链表。实现只重连已有节点，不创建替代节点，因此调用方持有的原 head 会成为反转后的尾节点。

```java
public final class ReverseLinkedList {
    private ReverseLinkedList() {}

    public static final class ListNode {
        public final int value;
        public ListNode next;

        public ListNode(int value) {
            this.value = value;
        }
    }

    public static ListNode reverse(ListNode head) {
        ListNode previous = null;
        ListNode current = head;
        while (current != null) {
            ListNode next = current.next;
            current.next = previous;
            previous = current;
            current = next;
        }
        return previous;
    }
}
```

## 关键细节

- 输入是单链表头结点，输出是反转后的新头；null 和单节点直接返回原引用。方法原地修改 next 指针。
- 初始化 prev=null、current=head；循环不变量是 prev 指向已完整反转的前缀，current 指向尚未修改的后缀首节点。
- 每轮按 next=current.next、current.next=prev、prev=current、current=next 的顺序执行，直到 current 为 null。
- 循环结束时未处理后缀为空，prev 覆盖原链表所有节点，因此 prev 是新头。
- 边界测试必须覆盖 null、单节点、两个节点、一般多节点，以及检查原 head 变成尾节点且 next 为 null。
- 时间复杂度 O(n)，额外空间 O(1)。
- 反转区间 II 要在 dummy 和区间前驱后局部头插；K 组反转要先确认每组有 k 个节点。它们不能直接复用本题从 head 走到 null 的一次循环。
- 复杂度：时间 O(n)，额外空间 O(1)

## 原理机制

状态从“已反转前缀为空、未处理后缀为全链表”开始。每次把未处理首节点移到已反转前缀头部，两个集合大小分别加一和减一；由于 next 在重连前被保存，两个集合始终覆盖全部节点且不重叠。
- 复杂度：时间 O(n)，额外空间 O(1)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么必须先保存 next？答：current.next 改为 previous 后，原后继引用会丢失；保存 next 后才能继续遍历未处理后缀。
- 问：反转后原 head 在哪里？答：它成为尾节点，next 应为 null；测试可持有原 head 验证这一点。
- 问：递归实现有什么代价？答：递归写法简短，但会使用 O(n) 调用栈；链表很长时有栈深度风险，迭代法是 O(1) 额外空间。
- 问：如何反转前 k 个节点？答：必须在第 k 个节点处保留后缀入口并把原 head 接回去；这已不是本题的“反转到 null”。

## 易错点

- 不要在保存后继前覆盖 current.next。
- 不要返回 current；循环结束时 current 为 null，新头是 previous。
- 不要误称方法不改变原链表，它会重连所有 next 指针。
