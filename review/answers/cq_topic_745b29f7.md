<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_745b29f7","version":2,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# 算法：k个一组翻转链表

## 核心结论

k 个一组翻转链表的核心是按组检查长度，长度足够才反转，不足 k 的尾段保持原样。实现上用 dummy、groupPrev、kth 和 groupNext 管理每组边界。

## 1 分钟版

先用 dummy 指向 head，groupPrev 指向每组前驱。每轮从 groupPrev 开始向后找第 k 个节点 kth，找不到说明剩余不足 k，直接结束。记录 groupNext=kth.next，然后把 groupPrev.next 到 kth 这一段反转。反转后原组头变成组尾，要连接到 groupNext，并把 groupPrev 移到这个组尾，继续下一组。

## 3 分钟版

这题最容易错在组边界。反转一组前先保存 groupNext，反转循环可以用 prev=groupNext、cur=groupPrev.next，直到 cur 等于 groupNext 为止。这样反转结束后，kth 会变成组头，原来的 groupPrev.next 会变成组尾。最后设置 groupPrev.next=kth，再把 groupPrev 移到旧组头。整个链表每个节点访问常数次，时间 O(n)，空间 O(1)。

```java
class Solution {
    public ListNode reverseKGroup(ListNode head, int k) {
        if (head == null || k <= 1) return head;
        ListNode dummy = new ListNode(0, head);
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = groupPrev;
            for (int i = 0; i < k && kth != null; i++) kth = kth.next;
            if (kth == null) break;
            ListNode groupNext = kth.next;
            ListNode prev = groupNext, cur = groupPrev.next;
            while (cur != groupNext) {
                ListNode next = cur.next;
                cur.next = prev;
                prev = cur;
                cur = next;
            }
            ListNode oldHead = groupPrev.next;
            groupPrev.next = kth;
            groupPrev = oldHead;
        }
        return dummy.next;
    }
}
```

## 关键细节

- 剩余节点不足 k 时不能反转。
- 反转前要保存下一组起点 groupNext。
- 反转后旧组头会变成组尾。
- dummy 可以简化头节点变化。
- 输入约束通常要求 `k >= 1`；防御式实现可对非正 k 抛异常。
- 时间 O(n)，每个节点参与有限次查找/反转；迭代额外空间 O(1)。

## 原理机制

- 每组内部做标准链表反转。
- 通过前驱节点和后继节点把局部反转段接回全链表。
- kth 用来判断当前组是否完整。

## 项目经验版

算法训练映射：先明确“只有完整 k 个节点才反转”，再分别验证 `k=1`、`length=k`、`length<k` 和非整倍数尾段。这里只记录训练流程，不包装成项目经历。

## 常见追问

- 问：剩余不足 k 为什么不反转？答：题目明确要求尾段保持原顺序，所以必须先找到 kth 再开始修改。
- 问：如何保证不断链？答：反转前保存 groupNext，并让组内初始 `prev=groupNext`，反转后再把前驱连到 kth。
- 问：递归和迭代如何取舍？答：递归表达清晰但需要 O(n/k) 栈；迭代 O(1) 额外空间且更适合长链表。
- 问：有什么变体？答：每 k 个交替反转时增加组号开关；从尾部不足 k 也反转则取消完整组检查但要重新定义边界。

## 易错点

- 不要在未确认足够 k 个节点时先反转。
- 不要忘记把组尾连接到 groupNext。
- 不要把 groupPrev 移到错误节点。
