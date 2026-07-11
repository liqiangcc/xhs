<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_3f61dd36","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：反转链表 II（LeetCode 92）

## 核心结论

反转链表 II 的关键是只修改第 left 到 right 个节点的 next 指针。给头结点加 dummy 后先走到区间前驱 pre，再把区间首节点之后的节点逐个头插到 pre 后；这样无需分别处理 left=1，时间 O(n)、额外空间 O(1)。

## 1 分钟版

- 约束按经典题意：位置从 1 开始，1 ≤ left ≤ right ≤ 链表长度；head 为 null 时返回 null。若接口不保证位置合法，应显式报错，而不是悄悄反转到链表尾。
- dummy.next=head，pre 前进 left-1 步后指向待反转区间的前驱；segmentHead=pre.next 在整个循环中始终是反转后区间的尾部。
- 每轮取 moving=segmentHead.next，把 segmentHead.next 跳过 moving，再让 moving.next 指向 pre.next，最后 pre.next=moving；总共执行 right-left 次。
- 循环不变量：pre 后已形成当前已反转前缀，segmentHead 后仍是尚未移动的原顺序后缀，二者之外的链表连接保持不变。

## 3 分钟版

dummy 统一了 left=1 与 left>1：pre 永远存在。头插法不会丢节点，因为每轮先保存 segmentHead.next，再先把 segmentHead 跨过 moving，最后把 moving 接到已反转前缀。若 left==right，循环次数为 0，原链表保持不变。该实现原地修改节点连接，不新建业务节点；调用方若需要保留原链表，应先复制节点而不是假设本方法非破坏性。

```java
public final class ReverseLinkedListII {
    private ReverseLinkedListII() {}

    public static final class ListNode {
        public final int value;
        public ListNode next;

        public ListNode(int value) {
            this.value = value;
        }
    }

    public static ListNode reverseBetween(ListNode head, int left, int right) {
        if (head == null) {
            return null;
        }
        if (left < 1 || right < left) {
            throw new IllegalArgumentException("invalid range");
        }
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode pre = dummy;
        for (int position = 1; position < left; position++) {
            if (pre.next == null) {
                throw new IllegalArgumentException("left exceeds list length");
            }
            pre = pre.next;
        }
        ListNode segmentHead = pre.next;
        if (segmentHead == null) {
            throw new IllegalArgumentException("left exceeds list length");
        }
        for (int moved = 0; moved < right - left; moved++) {
            ListNode moving = segmentHead.next;
            if (moving == null) {
                throw new IllegalArgumentException("right exceeds list length");
            }
            segmentHead.next = moving.next;
            moving.next = pre.next;
            pre.next = moving;
        }
        return dummy.next;
    }
}
```

## 关键细节

- 约束按经典题意：位置从 1 开始，1 ≤ left ≤ right ≤ 链表长度；head 为 null 时返回 null。若接口不保证位置合法，应显式报错，而不是悄悄反转到链表尾。
- dummy.next=head，pre 前进 left-1 步后指向待反转区间的前驱；segmentHead=pre.next 在整个循环中始终是反转后区间的尾部。
- 每轮取 moving=segmentHead.next，把 segmentHead.next 跳过 moving，再让 moving.next 指向 pre.next，最后 pre.next=moving；总共执行 right-left 次。
- 循环不变量：pre 后已形成当前已反转前缀，segmentHead 后仍是尚未移动的原顺序后缀，二者之外的链表连接保持不变。
- 边界用例：left=1 的头部反转、left=right 的无变化、left=1/right=n 的全链表反转、区间在中部、空链表。
- 时间复杂度 O(n)：到 pre 最多 O(n)，区间头插 O(right-left)；额外空间 O(1)。
- 普通反转链表只需持续翻转到 null；K 组反转则需要先确认每组长度足够并循环处理多个区间，不能复用本题的一次固定 right 逻辑。
- 复杂度：时间 O(n)，额外空间 O(1)

## 原理机制

状态按“未处理前缀 → 已定位 pre → 已反转区间前缀 + 未处理区间后缀 → 接回尾部”推进。segmentHead 不移动，因此它自然成为区间尾；moving 每次被插入 pre 后，已反转部分向右扩展一个节点。dummy 消除头结点变化这一特殊分支。
- 复杂度：时间 O(n)，额外空间 O(1)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么要 dummy 节点？答：当 left=1 时原 head 会变化；dummy 让 pre 始终指向一个真实前驱，主循环无需分支。
- 问：为什么 segmentHead 在循环中不移动？答：它是原区间第一个节点，首个节点被不断跨过后成为已反转区间的尾部；固定它才能从未处理后缀持续取 moving。
- 问：left 和 right 相同怎么办？答：right-left 为 0，不执行头插，返回原连接；这也是应覆盖的边界测试。
- 问：K 组反转和这里有什么差别？答：K 组需要反复确认剩余节点是否够 k 个并维护每组尾部，本题只有一个已给定的连续区间。

## 易错点

- 不要从 head 直接找 pre 而遗漏 left=1 时的新头结点。
- 不要在保存 moving 前覆盖 segmentHead.next，否则会丢失未处理后缀。
- 不要把位置从 1 开始和数组下标从 0 开始混用。
