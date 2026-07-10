<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_linked_list_cycle_2b5bb46d","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# 算法：判断链表是否有环

## 核心结论

Floyd 快慢指针判断环：slow 每次一步、fast 每次两步；有环时二者必在环内相遇，无环时 fast 先到 null。

## 1 分钟版

- 循环条件检查 fast 和 fast.next，避免空指针。
- 相遇后若要求入口，把一个指针移回 head，两者每次一步，再次相遇即入口。
- 若要求环长，从相遇点走一圈计数。

## 3 分钟版

设入环前长度 a、相遇点距入口 b、环长 c，可由快慢路程关系推出 head 与相遇点同步前进会在入口相遇。 先声明输入约束和不变量，再逐步推导实现；最后给出复杂度、空值/极值用例和至少一个变体。

```java
class Solution {
  public boolean hasCycle(ListNode head){
    ListNode slow=head, fast=head;
    while(fast!=null && fast.next!=null){
      slow=slow.next; fast=fast.next.next;
      if(slow==fast) return true;
    }
    return false;
  }
}
```

## 关键细节

- 循环条件检查 fast 和 fast.next，避免空指针。
- 相遇后若要求入口，把一个指针移回 head，两者每次一步，再次相遇即入口。
- 若要求环长，从相遇点走一圈计数。
- 空链表、单节点无环和单节点自环都需覆盖。
- 复杂度：时间 O(n)，额外空间 O(1)

## 原理机制

正确性由循环/状态不变量保证；每次迭代只做保持不变量的局部更新，结束条件把局部结论扩展到完整输入。 Floyd 快慢指针判断环：slow 每次一步、fast 每次两步；有环时二者必在环内相遇，无环时 fast 先到 null。
- 复杂度：时间 O(n)，额外空间 O(1)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么一定相遇？答：进入环后快指针每轮相对慢指针多走一步，会在有限环长内追上。
- 问：如何找入口？答：相遇后一个回 head，同速前进，再次相遇就是入口。
- 问：HashSet 解法呢？答：也能判断并找首个重复节点，但需要 O(n) 额外空间。

## 易错点

- 不要只给代码而不解释不变量。
- 不要遗漏复杂度、空输入和变体。
- 不要比较节点值，必须比较节点引用。
