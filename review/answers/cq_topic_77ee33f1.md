<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_77ee33f1","version":2,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# 算法：反转链表

## 核心结论

反转链表的标准做法是迭代维护 prev、curr、next 三个指针，每次把 curr.next 指向 prev，再整体后移。时间复杂度 O(n)，空间复杂度 O(1)。

## 1 分钟版

初始 prev=null，curr=head。循环中先保存 next=curr.next，防止链表断掉；然后 curr.next=prev 完成反转；最后 prev=curr，curr=next。循环结束时 curr 为 null，prev 指向新的头节点，返回 prev。

## 3 分钟版

链表反转的关键是处理指针方向变化时不要丢失后续节点。每轮操作前，curr 指向当前要反转的节点，prev 指向已经反转好的前半部分。先用 next 保存未处理链表头，再让 curr 指向 prev，把当前节点接到已反转链表前面。然后 prev 和 curr 同时向后推进。这个循环不需要额外数组或递归栈，所以空间复杂度 O(1)。递归写法也可以，但要注意栈深度。

## 关键细节

- 必须先保存 next，再改 curr.next。
- 返回的是 prev，不是 curr。
- 空链表和单节点链表天然适配。
- 递归写法空间复杂度是 O(n)。

## 原理机制

- prev 表示已经反转完成的链表头。
- curr 表示当前待处理节点。
- next 保存剩余未处理链表入口。

```java
ListNode reverseList(ListNode head) {
    ListNode prev = null;
    ListNode curr = head;
    while (curr != null) {
        ListNode next = curr.next;
        curr.next = prev;
        prev = curr;
        curr = next;
    }
    return prev;
}
```

## 项目经验版

算法训练映射：复习时先画 prev、curr、next 三个指针，口述“保存后继、反转当前、整体前进”不变量，再手写代码并验证空链表、单节点和多节点。该章节是训练提示，不应包装成项目经历。

## 常见追问

- 问：如何递归反转？答：递归反转 `head.next` 后令 `head.next.next = head`，再把 `head.next` 置空；时间 O(n)，递归栈 O(n)。
- 问：如何反转一段链表？答：先找到区间前驱和后继，仅反转 `[left,right]`，再把前驱接新头、旧头接后继；dummy 节点能统一处理从头开始的区间。
- 问：如何 K 个一组反转？答：每轮先确认剩余节点不少于 K 个，再反转闭开区间并连接前后组；不足 K 个保持原顺序。
- 问：反转为什么不会成环？答：每次只把当前节点指向已经反转且最终以 null 结尾的前缀，同时保存原后继；遗漏旧头置向或错误重连才可能成环。

## 易错点

- 不保存 next 会丢失后续链表。
- 返回 head 会得到旧头节点。
- 多节点情况下要避免形成环。
