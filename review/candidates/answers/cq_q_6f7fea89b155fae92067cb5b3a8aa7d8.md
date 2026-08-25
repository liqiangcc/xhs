<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6f7fea89b155fae92067cb5b3a8aa7d8","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# 算法：链表节点 K 个一组翻转

## 核心结论

题源只保留“链表节点 K 个一组翻转”，没有给完整 API 和尾部不足 K 个节点的规则。这里明确采用最常见的标准契约：`k >= 1`；每个**完整的 K 节点分组原地反转**；最后不足 K 个节点保持原顺序；不新建业务节点，只改 `next`；空链表合法。若面试官要求“最后不足 K 个也翻转”，那是另一份契约，不能悄悄混在同一个实现里。

核心技巧是虚拟头节点 + “先确认有 K 个，再反转当前组”。每组开始时 `groupPrev` 指向组前节点；先向前找到第 K 个节点 `kth`，记录下一组起点 `groupNext = kth.next`；再把 `[groupPrev.next, kth]` 原地反转并接回前后两段。

## 1 分钟版

- 用 dummy 统一处理第一组翻转后头节点变化，`groupPrev` 始终指向待处理组前一个节点。
- **先找第 K 个节点**；找不到就直接结束，因此尾部不足 K 个保持不动。
- 反转前先保存 `groupNext = kth.next`，反转循环以 `groupNext` 为哨兵终点。
- 反转时从 `prev = groupNext` 开始，这样旧组头最终会直接连到下一组，不需要额外补尾指针。
- 一组反转后，新组头是原来的 `kth`，新 `groupPrev` 是原来的组头。
- 每个节点被常数次访问，时间 `O(n)`，除 dummy 和指针外额外空间 `O(1)`。

## 3 分钟版

假设链表是 `1 -> 2 -> 3 -> 4 -> 5`，`k = 2`。

第一轮：`groupPrev=dummy`，找到 `kth=2`，`groupNext=3`。把 `1,2` 反转后得到 `dummy -> 2 -> 1 -> 3...`，然后令 `groupPrev=1`。第二轮同理处理 `3,4`。最后只剩节点 `5`，找不到两个完整节点，停止，结果是 `2 -> 1 -> 4 -> 3 -> 5`。

```java
public final class ReverseKGroup {
    private ReverseKGroup() {}

    public static final class ListNode {
        public final int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode reverseKGroup(ListNode head, int k) {
        if (k < 1) throw new IllegalArgumentException("k must be >= 1");
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode groupPrev = dummy;

        while (true) {
            ListNode kth = kthFrom(groupPrev, k);
            if (kth == null) break;
            ListNode groupNext = kth.next;

            ListNode prev = groupNext;
            ListNode cur = groupPrev.next;
            while (cur != groupNext) {
                ListNode next = cur.next;
                cur.next = prev;
                prev = cur;
                cur = next;
            }

            ListNode oldGroupHead = groupPrev.next;
            groupPrev.next = kth;
            groupPrev = oldGroupHead;
        }
        return dummy.next;
    }

    private static ListNode kthFrom(ListNode start, int k) {
        ListNode cur = start;
        for (int i = 0; i < k; i++) {
            cur = cur.next;
            if (cur == null) return null;
        }
        return cur;
    }
}
```

这里最容易写错的是组边界：`kth` 是当前组最后一个节点，`groupNext` 是不参与当前反转的第一个节点。反转完后，原组头变成组尾，所以必须用反转前保存的 `oldGroupHead` 更新 `groupPrev`。

## 关键细节

- **尾部不足 K 个**：当前答案明确选择保持原顺序；这是答案侧契约，不冒充成题源已写明的约束。
- **k=1**：每组只有一个节点，算法仍成立，链表身份和顺序都不变。
- **k 大于链表长度**：第一次就找不到 `kth`，直接返回原链表。
- **空链表**：返回 `null`。
- **节点身份**：实现只重连 `next`，不按值复制节点；若节点还携带其它状态，身份仍保留。
- **为什么 `prev=groupNext`**：反转当前组最后一条新边时，旧组头会接到 `groupNext`，一次完成尾部拼接。
- **为什么先探测完整组**：若边走边翻转，到一半才发现不足 K 个，就需要回滚；先找 `kth` 可保持“要么完整翻一组，要么不动”的不变量。
- **输入是否可能有环**：题源没说；当前契约假设普通有限单链表。若输入可能有环，应先定义检测/拒绝策略，否则“按 K 分组直到尾部”本身没有终止语义。

## 原理机制

在每轮开始时保持不变量：`dummy` 到 `groupPrev` 之前的部分已经按 K 分组处理完且连接正确，`groupPrev.next` 是尚未处理后缀的第一个节点。只有确认后缀至少有 K 个节点才改变指针。

当前组反转时，`prev` 始终指向“已经反转好的当前组后缀”，`cur` 指向还没反转的第一个节点；保存 `next` 后执行 `cur.next = prev`，再向前推进。循环到 `cur == groupNext` 时，整个组已经倒置且旧组头自动连到下一段。把 `groupPrev.next` 指到 `kth` 后，前缀与新组重新接通，不变量恢复，进入下一轮。

因为每个节点在“找 kth”和“反转”阶段各被访问常数次，总时间仍是 `O(n)`；没有递归栈或随 n 增长的辅助结构，所以额外空间 `O(1)`。

## 项目经验版

来源只有算法题，没有真实项目中的链表结构、节点载荷或性能数据，因此不虚构线上经历。实际代码若处理的是侵入式链表或带共享引用的对象，还要先确认是否允许原地改 `next`、是否存在其它引用依赖旧顺序，以及异常时是否需要事务式回滚；这些都不属于当前题源事实。

## 常见追问

- 问：为什么需要 dummy？答：第一组反转后 `head` 会变化；dummy 让“组前节点”始终存在，第一组和后续组使用同一套接线逻辑。
- 问：为什么尾部不足 K 个不翻？答：这是当前明确采用的标准契约；关键是先探测完整组，找不到第 K 个节点时完全不改这段后缀。若题目另有要求，应改契约和测试。
- 问：为什么反转时 `prev` 初始化成 `groupNext` 而不是 `null`？答：这样旧组头在反转结束后直接指向下一组，省掉一次单独的尾连接，并让边界更清楚。
- 问：如何证明不会丢节点？答：每次覆盖 `cur.next` 之前先保存原后继 `next`；当前组外又提前保存 `groupNext`，所以遍历路径和后续链都不会丢失。
- 问：能递归写吗？答：可以，先确认剩余至少 K 个再反转并递归后缀；但递归会引入 `O(n/k)` 栈空间，迭代版更直接满足 `O(1)` 额外空间。
- 问：k=1 会不会死循环？答：不会。`kth` 就是当前首节点，反转循环执行一次，`groupPrev` 更新到该节点，下一轮从后继继续前进。

## 易错点

- 没确认完整 K 个就开始改指针，最后不足 K 时无法无损恢复。
- 反转前没保存 `groupNext`，失去当前组与后缀边界。
- 更新 `groupPrev` 时用新组头而不是旧组头，导致下一轮边界错位。
- 覆盖 `cur.next` 前没有保存 `next`，直接丢失剩余链表。
- 把“节点值分组翻转”写成重新创建节点，破坏原节点身份。
- 没说明尾部不足 K、非法 k 和环输入的契约边界。
