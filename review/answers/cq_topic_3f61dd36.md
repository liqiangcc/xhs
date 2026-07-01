<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_3f61dd36","version":1,"status":"ready","updated_at":"2026-07-01"} -->
# 算法手撕：反转链表 II（Reverse Linked List II）。

## 核心结论

反转链表 II 是只反转链表中 left 到 right 的一段。常用做法是使用 dummy 节点，找到反转段前一个节点，然后用头插法把区间内节点逐个插到区间头部。

## 1 分钟版

先创建 dummy 指向 head，移动 pre 到 left 前一个节点。cur 指向 pre.next。接着循环 right-left 次，每次取出 cur.next 这个节点 next，把它从原位置摘下，再插到 pre 后面。循环结束后，dummy.next 就是新头。这个方法一次遍历即可完成，时间 O(n)，额外空间 O(1)。

## 3 分钟版

头插法的关键是不移动 pre，pre 始终指向反转区间前驱；cur 始终指向反转后区间的尾部。每轮把 cur 后面的节点拿出来，插到 pre 后面，相当于不断把后续节点提前。例如 1->2->3->4->5，反转 2 到 4，pre 是 1，cur 是 2；先把 3 插到 1 后面，再把 4 插到 1 后面，得到 1->4->3->2->5。dummy 可以统一处理 left 为 1 的情况。

## 关键细节

- dummy 节点用于处理反转从头节点开始的情况。
- pre 固定在反转区间前一个节点。
- 循环次数是 right-left。
- 每次操作都要先保存 cur.next，避免断链。

## 原理机制

- 局部头插改变区间内节点顺序。
- 区间前驱和区间尾节点保持对外连接。
- 单链表只能通过前驱节点修改 next 指针。

## 项目经验版

链表题面试时我会先画 3 到 4 个节点的小例子，再写指针更新顺序。写完后用 left=1、left=right、right=链表长度三个边界手动过一遍，能快速发现断链问题。

## 常见追问

- 为什么需要 dummy 节点？
- 能不能用递归反转？
- 头插法中 cur 为什么不往后移动？
- left 等于 right 怎么处理？

## 易错点

- 不要忘记处理 left 为 1。
- 不要把循环次数写成 right-left+1。
- 不要在修改 next 前丢失后续节点引用。
