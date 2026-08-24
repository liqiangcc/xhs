<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_5a5db0e8391add20113a1ffec9c1e41b","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# 有序链表去除重复元素：给出1→2→3→3→4→4→5，返回1→2→5

## 核心结论

这是“**删除所有出现重复的值**”而不是“每个值只保留一个”的有序链表题。利用有序性，相同值一定连续：用虚拟头 `dummy` 处理头部被整段删除的情况，`prev` 永远指向已确认保留部分的最后一个节点，`cur` 扫描当前分组；一旦发现 `cur` 与后继值相同，就跳过这一整段并令 `prev.next = cur`。样例 `1→2→3→3→4→4→5` 因此得到 `1→2→5`。

## 1 分钟版

- 输入：按非递减顺序排列的单链表；输出：只保留在输入中出现 **恰好一次** 的节点。
- `dummy.next = head`，`prev = dummy`，`cur = head`。
- 若 `cur.next != null && cur.val == cur.next.val`，记住该值并把 `cur` 移到这一整段之后，然后 `prev.next = cur`。
- 否则当前值只出现一次，可以保留：`prev = cur`，`cur = cur.next`。
- 每个节点最多被扫描常数次，时间 `O(n)`；只改 `next` 指针，额外空间 `O(1)`。

## 3 分钟版

题目样例已经消除了“去重到底是保留一个还是全部删除”的歧义：`3`、`4` 都在结果中完全消失，所以响应契约是保留唯一值节点。因为链表有序，相同值构成连续分组，可以在一次线性扫描里决定每组的去留。

关键不变量是：每轮开始时，`dummy.next ... prev` 表示已经处理完且最终确定保留的前缀，`prev.next` 指向尚未处理区域的第一个节点 `cur`。若 `cur` 的值与下一节点相同，这个分组不能保留任何节点；把 `cur` 一直推进到不同值，再让 `prev.next` 越过整组即可。若下一节点不同，则当前节点是该值唯一出现的位置，可以把 `prev` 前进一格。

```java
public final class RemoveAllDuplicates {
    public static final class ListNode {
        final int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    public static ListNode deleteDuplicates(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy;
        ListNode cur = head;

        while (cur != null) {
            if (cur.next != null && cur.val == cur.next.val) {
                int duplicateValue = cur.val;
                while (cur != null && cur.val == duplicateValue) {
                    cur = cur.next;
                }
                prev.next = cur;
            } else {
                prev = cur;
                cur = cur.next;
            }
        }
        return dummy.next;
    }

    private RemoveAllDuplicates() {}
}
```

## 关键细节

- **不要混淆两个题型**：`1→1→2` 若“保留一个”会得到 `1→2`；本题的契约是“重复值全部删除”，因此得到 `2`。
- **为什么要 dummy**：若头部就是重复段，例如 `1→1→2`，最终头节点会改变；虚拟头让删除头部和删除中间段使用同一条 `prev.next = cur` 逻辑。
- **为什么利用有序性**：相同值连续，看到相邻两个值相等后，只需跳过这一连续分组；无序链表不能仅靠这个局部判断。
- **节点复用**：实现原地重连已有节点，不创建结果链表；虚拟头只是常数级辅助节点。
- **复杂度**：外层和内层推进共享同一个 `cur`，节点不会反复回退，所以总扫描仍为 `O(n)`，额外空间 `O(1)`。
- **边界**：空链表、单节点、无重复、全重复、头部重复、中间重复、尾部重复都应覆盖。

## 原理机制

有序条件把“全局出现次数”问题降成连续分组问题。对每一组只有两种状态：长度为 1 则保留，长度大于 1 则整组删除。算法并不需要哈希表统计次数；它通过相邻节点判断是否进入重复组，再通过值相等循环找到该组右边界。`prev` 只在确认当前组长度为 1 时前进，因此它不会落在一个稍后要删除的重复组里。

虚拟头保证返回头始终是 `dummy.next`。当重复组在链表头、中间或尾部时，最终动作都是把“最后一个已保留节点”的 `next` 指向下一未处理节点；尾部重复时这个目标自然为 `null`。

## 项目经验版

来源只给出算法题与样例，没有真实项目经历，不能编造线上故事。若把机制映射到项目代码审查，重点是先明确“去重”业务语义究竟是保留一个、保留最新一个，还是重复记录全部判无效；这三种契约会对应不同实现。本题由样例明确选择第三种。

## 常见追问

- 问：`1→1→2→3→3` 返回什么？答：`2`，因为值 `1` 和 `3` 都出现多次，要整组删除。
- 问：为什么不能只写 `if (cur.val == cur.next.val) cur.next = cur.next.next`？答：那是“压缩重复、保留一个”的典型写法，会留下重复值中的一个节点，不符合本题样例。
- 问：为什么内层 `while` 不会把复杂度变成 `O(n²)`？答：`cur` 只向前移动且不会回退；每个节点总共只被跨过一次，所以总推进次数仍是线性的。
- 问：不使用 dummy 可以吗？答：可以，但需要单独维护新头并特殊处理头部重复段；dummy 把这些分支统一掉。
- 问：链表如果无序还能这样做吗？答：不能仅靠连续分组判断；同值可能分散在不同位置，需要额外统计或排序等不同策略。

## 易错点

- 把题目误做成“每个重复值保留一个”。
- 发现重复后只删除一个节点，没有跳过整段相同值。
- 重复段删除后错误推进 `prev`，使它指向本应被删除的节点。
- 没有虚拟头又遗漏头部连续重复的返回头更新。
- 看到双层循环就误判为 `O(n²)`，忽略两个循环共享单调前进的游标。
