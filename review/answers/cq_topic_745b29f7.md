<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_745b29f7","version":1,"status":"ready","updated_at":"2026-07-01"} -->
# 算法：k个一组翻转链表

## 核心结论

k 个一组翻转链表的核心是按组检查长度，长度足够才反转，不足 k 的尾段保持原样。实现上用 dummy、groupPrev、kth 和 groupNext 管理每组边界。

## 1 分钟版

先用 dummy 指向 head，groupPrev 指向每组前驱。每轮从 groupPrev 开始向后找第 k 个节点 kth，找不到说明剩余不足 k，直接结束。记录 groupNext=kth.next，然后把 groupPrev.next 到 kth 这一段反转。反转后原组头变成组尾，要连接到 groupNext，并把 groupPrev 移到这个组尾，继续下一组。

## 3 分钟版

这题最容易错在组边界。反转一组前先保存 groupNext，反转循环可以用 prev=groupNext、cur=groupPrev.next，直到 cur 等于 groupNext 为止。这样反转结束后，kth 会变成组头，原来的 groupPrev.next 会变成组尾。最后设置 groupPrev.next=kth，再把 groupPrev 移到旧组头。整个链表每个节点访问常数次，时间 O(n)，空间 O(1)。

## 关键细节

- 剩余节点不足 k 时不能反转。
- 反转前要保存下一组起点 groupNext。
- 反转后旧组头会变成组尾。
- dummy 可以简化头节点变化。

## 原理机制

- 每组内部做标准链表反转。
- 通过前驱节点和后继节点把局部反转段接回全链表。
- kth 用来判断当前组是否完整。

## 项目经验版

手写时我会先写一个找第 k 个节点的辅助逻辑，再写组内反转。代码完成后用 k=1、链表长度等于 k、长度不是 k 的倍数三种用例验证边界。

## 常见追问

- 剩余不足 k 为什么不反转？
- 如何保证反转后不断链？
- 递归和迭代有什么区别？
- k=1 时结果是什么？

## 易错点

- 不要在未确认足够 k 个节点时先反转。
- 不要忘记把组尾连接到 groupNext。
- 不要把 groupPrev 移到错误节点。
