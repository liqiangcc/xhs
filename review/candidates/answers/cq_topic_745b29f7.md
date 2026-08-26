<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_745b29f7","version":2,"status":"draft","updated_at":"2026-08-26","answer_type":"coding","quality_tier":"candidate"} -->
# K 个一组翻转链表

## 核心结论

三份当前仓库来源都只保留了“K 个一组翻转链表”这一题名，其中一份明确写了 `LC 25`；来源没有保存编程语言、节点 API、`k` 的非法输入处理，也没有逐字保存“不足 k 个的尾段如何处理”。下面明确采用 **LeetCode 25 常见契约作为答案侧实现契约**：输入是无环单链表，`k >= 1`；每个完整的 k 节点组原地反转，最后不足 k 个节点保持原顺序；不修改节点值，只改 `next`，返回新头节点。若面试官现场给出不同尾段规则，以现场契约为准。

迭代实现的关键不是“会反转链表”，而是 **先探测完整组，再修改指针**。用 `dummy -> head` 和 `groupPrev` 表示待处理组的前驱；先找到第 k 个节点 `kth`，找不到就直接结束；找到后保存 `groupNext = kth.next`，只反转半开区间 `[groupPrev.next, groupNext)`，再把新组头接回前驱，并把旧组头作为下一轮 `groupPrev`。

## 1 分钟版

- `dummy` 统一处理第一组导致的头节点变化。
- 每轮先从 `groupPrev` 向后走 k 步找 `kth`；找不到说明剩余不足 k，按本答案契约保持原序并返回。
- 保存 `groupNext = kth.next`，反转时设 `prev = groupNext`、`cur = groupPrev.next`，直到 `cur == groupNext`。
- 反转后 `kth` 是新组头，旧组头变成组尾；先保存旧组头，再执行 `groupPrev.next = kth`，最后把 `groupPrev` 移到旧组头。
- 每个节点只被常数次探测/重连，时间 `O(n)`；只有若干指针变量，额外空间 `O(1)`。

## 3 分钟版

```java
public final class ReverseKGroup {
    private ReverseKGroup() {}

    public static final class ListNode {
        public final int value;
        public ListNode next;
        public ListNode(int value) { this.value = value; }
    }

    public static ListNode reverseKGroup(ListNode head, int k) {
        if (k < 1) {
            throw new IllegalArgumentException("k must be positive");
        }

        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode groupPrev = dummy;

        while (true) {
            ListNode kth = groupPrev;
            for (int i = 0; i < k && kth != null; i++) {
                kth = kth.next;
            }
            if (kth == null) {
                return dummy.next;
            }

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
    }
}
```

例如 `1→2→3→4→5`、`k=2`：第一组确认 `1,2` 完整后变成 `2→1`，第二组确认 `3,4` 完整后变成 `4→3`，最后只剩 `5`，因为不足 2 个不再改链，所以得到 `2→1→4→3→5`。`k=3` 时得到 `3→2→1→4→5`。

## 关键细节

- **来源边界**：仓库原始笔记只证明面试出现过“K 个一组翻转链表/LC25”。Java、`ListNode` 结构、异常行为和尾段规则是本候选为可执行验证显式采用的契约，不冒充来源逐字要求。
- **为什么必须先找 `kth`**：若边找边反转，最后一组不足 k 时已经破坏链表，回滚会很麻烦；先探测保证“确认完整组之前零修改”。
- **为什么 `prev = groupNext`**：这样当前组旧头在反转完成后天然指向未处理后缀，不需要额外再找组尾接线。
- **半开区间不变量**：反转过程中，`prev` 始终是已经反转前缀的头，`cur` 是尚未处理部分的头；停止于 `groupNext` 可以保证不跨进下一组。
- **节点身份**：实现只新建一个不进入结果数据集的 dummy，不新建业务节点，也不改 `value`；测试会校验输出节点对象集合与输入完全相同、无环且值未变。
- **`k=1`**：每组只有一个节点，代码仍正确；可以提前返回做微优化，但不是正确性必需。
- **复杂度**：找 `kth` 和反转各让节点参与常数次操作，总时间 `O(n)`，额外空间 `O(1)`；迭代避免递归版 `O(n/k)` 调用栈。

## 原理机制

可以把链表分成三段：`已完成前缀 | 当前候选组 | 未处理后缀`。`groupPrev` 永远停在已完成前缀的最后一个节点。探测阶段只读 `next`，确认当前候选组确实有 k 个节点后，`groupNext` 冻结了这组的右边界。随后只在 `[groupPrev.next, groupNext)` 中逐边反向；结束时旧组头变成组尾并已经指向 `groupNext`，新组头 `kth` 再接到 `groupPrev.next`。因此每轮结束后同一个不变量重新成立，可以继续处理下一组。

## 项目经验版

这是算法题，仓库来源没有真实生产项目经历，因此不虚构线上使用场景。工程上可迁移的习惯是：任何原地修改结构的算法都先定义“允许修改的闭区间/半开区间”和提交前置条件；像这里一样先确认一整组存在，再做不可逆指针写入，可以显著减少边界分支和回滚需求。

## 常见追问

- 问：为什么不足 k 个不能直接反转？答：本答案采用 LC25 常见契约，尾段不足 k 保持原序；更重要的是实现先探测再修改，所以即使尾段不完整也完全不会被碰。若现场契约要求尾段也反转，需要明确改规则。
- 问：为什么需要 dummy？答：第一组反转后链表头会变化；dummy 让“首组前驱”和“后续组前驱”统一成同一种连接操作。
- 问：怎么证明没有断链？答：反转前保存 `groupNext`，并让 `prev` 从 `groupNext` 开始；每次改 `cur.next` 前保存原 `next`。因此旧组头最终直接接上 `groupNext`，组外后缀始终可达。
- 问：递归能写吗？答：可以，先确认当前有 k 个节点，再递归处理后缀并反转当前组；但会产生 `O(n/k)` 栈深，迭代版额外空间是 `O(1)`。
- 问：如何验证不是只过几个样例？答：用独立数组 oracle 对多个长度和 k 组合生成预期节点顺序，同时校验节点 identity、值、无环、尾段和非法 k 行为。

## 易错点

- 没确认完整 k 个节点就开始改 `next`，导致残组被部分翻转。
- 反转循环写成到 `null` 才结束，跨过 `groupNext` 把下一组也卷进来。
- 反转后把 `groupPrev` 移到新组头而不是旧组头，下一轮边界错位。
- 忘记保存 `cur.next` 就覆盖 `cur.next`，直接丢失未处理后缀。
- 把本答案采用的 Java API、`k<1` 异常或尾段规则说成原始面试笔记逐字保存的条件。
