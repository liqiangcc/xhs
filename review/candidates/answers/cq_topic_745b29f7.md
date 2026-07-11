<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_745b29f7","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：k个一组翻转链表

## 核心结论

K 个一组翻转的关键是每轮先从 groupPrev 后探测 k 个节点；不足 k 个立即返回，保留尾部原序。凑足后把该组原地反转并接回下一组，时间 O(n)、额外空间 O(1)。

## 1 分钟版

- 输入无环单链表和 k≥1；k=1 或 head 为 null 不改变链表。尾部不足 k 个节点按题意不反转。
- dummy 统一首组与后续组；groupPrev 始终指向待处理组的前驱，groupNext 是本组反转后应接回的首节点。
- 先走 k 步找到 kth；找不到 kth 就返回 dummy.next。反转区间 [groupPrev.next, groupNext) 时，每轮把 current.next 指向 previous。
- 不变量：groupPrev 之前的组均已正确反转并连接，groupPrev 之后尚未处理；反转完成后旧组头成为新尾并作为新的 groupPrev。

## 3 分钟版

不能像普通反转一样一路反到 null：每组必须先确认长度，否则会错误翻转尾部不足 k 个节点。以 groupNext 作为半开区间终点可防止跨组；反转后要保存旧组头作为下一轮前驱。

```java
public final class ReverseKGroup {
    private ReverseKGroup() {}
    public static final class ListNode {
        public final int value; public ListNode next;
        public ListNode(int value) { this.value = value; }
    }
    public static ListNode reverseKGroup(ListNode head, int k) {
        if (k < 1) throw new IllegalArgumentException("k must be positive");
        ListNode dummy = new ListNode(0); dummy.next = head;
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = groupPrev;
            for (int step = 0; step < k && kth != null; step++) kth = kth.next;
            if (kth == null) return dummy.next;
            ListNode groupNext = kth.next;
            ListNode previous = groupNext;
            ListNode current = groupPrev.next;
            while (current != groupNext) {
                ListNode next = current.next; current.next = previous; previous = current; current = next;
            }
            ListNode oldHead = groupPrev.next;
            groupPrev.next = kth;
            groupPrev = oldHead;
        }
    }
}
```

## 关键细节

- 输入无环单链表和 k≥1；k=1 或 head 为 null 不改变链表。尾部不足 k 个节点按题意不反转。
- dummy 统一首组与后续组；groupPrev 始终指向待处理组的前驱，groupNext 是本组反转后应接回的首节点。
- 先走 k 步找到 kth；找不到 kth 就返回 dummy.next。反转区间 [groupPrev.next, groupNext) 时，每轮把 current.next 指向 previous。
- 不变量：groupPrev 之前的组均已正确反转并连接，groupPrev 之后尚未处理；反转完成后旧组头成为新尾并作为新的 groupPrev。
- 测试覆盖 k=1、长度恰为 k、多个完整组、尾部不足 k、空链表。
- 时间 O(n)，额外空间 O(1)。
- 普通反转没有组长度探测；区间反转只有一个固定区间，K 组反转需要循环处理多个半开区间。
- 复杂度：时间 O(n)，额外空间 O(1)

## 原理机制

状态为已完成组、当前完整组和未处理后缀。探测阶段不改链；只有确认 kth 存在后才在 [groupHead,groupNext) 内重连，因此尾部残组不会被部分修改。
- 复杂度：时间 O(n)，额外空间 O(1)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么先找 kth？答：先确认完整组，才能保证尾部不足 k 个节点不被修改。
- 问：为什么 previous 初始为 groupNext？答：反转后旧组头必须直接接回未处理后缀，groupNext 正是该后缀首节点。
- 问：k=1 会怎样？答：每个组原地反转一次但连接不变；可直接提前返回优化，语义仍正确。
- 问：递归版代价？答：递归可先处理后缀再翻当前组，但调用栈 O(n/k)，迭代版额外空间 O(1)。

## 易错点

- 不要未探测完整组就开始反转。
- 不要把 groupNext 纳入当前组反转。
- 不要丢失旧组头；它是下一轮 groupPrev。
