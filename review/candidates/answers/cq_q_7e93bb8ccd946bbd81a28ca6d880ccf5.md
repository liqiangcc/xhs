<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_7e93bb8ccd946bbd81a28ca6d880ccf5","version":1,"status":"draft","updated_at":"2026-08-26","answer_type":"coding","quality_tier":"candidate"} -->
# 旋转链表（LeetCode 61）

## 核心结论

来源通过 “LeetCode 61” 标识旋转链表题。这里把可执行契约明确出来：把单链表**向右旋转非负 k 个位置**；空链表返回 `null`，`k=0` 或 `k%n=0` 返回原头；只重连原节点，不新建替代节点；负数 k 不在题目契约内，本实现显式拒绝。最简做法是先求长度 n 和原尾节点，把 k 化成 `k % n`，临时让尾节点指回头节点形成环，再走 `n-k-1` 步找到新尾并断环。时间 O(n)，额外空间 O(1)。

## 1 分钟版

- 先遍历一次得到链表长度 `n` 和原尾 `tail`。
- `shift = k % n`；如果 `shift == 0`，不需要修改任何 `next`。
- 让 `tail.next = head`，先把线性链表临时接成环。
- 向右转 `shift` 位后，新尾是原链表第 `n-shift` 个节点，即从 head 再走 `n-shift-1` 条边。
- `newHead = newTail.next`，然后 `newTail.next = null` 断环。
- 每个节点最多常数次访问，所以 O(n)；只用几个指针和整数，所以 O(1) 额外空间。

## 3 分钟版

```java
public final class RotateList {
    public static final class ListNode {
        public int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode rotateRight(ListNode head, int k) {
        if (k < 0) throw new IllegalArgumentException("k must be non-negative");
        if (head == null || head.next == null || k == 0) return head;

        int n = 1;
        ListNode tail = head;
        while (tail.next != null) {
            tail = tail.next;
            n++;
        }

        int shift = k % n;
        if (shift == 0) return head;

        tail.next = head;
        int stepsToNewTail = n - shift - 1;
        ListNode newTail = head;
        for (int i = 0; i < stepsToNewTail; i++) {
            newTail = newTail.next;
        }

        ListNode newHead = newTail.next;
        newTail.next = null;
        return newHead;
    }
}
```

例如 `1→2→3→4→5`、`k=2`：`n=5`，新尾应该是第 `5-2=3` 个节点 3。先连接 `5→1` 成环，找到 3 后令新头为 4，再断开 `3.next`，结果就是 `4→5→1→2→3`。

## 关键细节

- **先取模**：旋转 n 次等于没旋转，所以 `k % n` 能把很大的 k 收敛到 `[0,n-1]`。
- **断环位置**：右转 shift 后，新头是原来的第 `n-shift+1` 个节点（1-based），因此新尾是第 `n-shift` 个；从 head 走的边数是 `n-shift-1`。
- **`shift==0` 提前返回**：如果先成环再忘记断开，会把原本合法链表变成永久环；提前返回也避免无意义写操作。
- **节点身份**：题目是链表重排，本实现只修改 `next`，不复制节点。测试不仅要比较值顺序，也要确认所有原节点恰好出现一次且最终无环。
- **负 k**：来源没有要求左旋/负数语义；本答案选择显式拒绝，而不是让 Java `%` 的负余数悄悄产生错误下标。
- **长度为 0/1**：空链表没有取模分母，单节点旋转后身份与结构都不变，所以要在求模前处理。

## 原理机制

右旋并没有改变节点的相对循环顺序，只是改变“从哪个节点作为 head 开始看”以及“哪个位置断开”。因此把链表临时闭环后，问题就从搬动 k 次尾节点变成一次定位切口：长度是 n、右移 shift，那么新的线性序列从原下标 `n-shift`（0-based）开始，新尾正好是它前一个节点。这样避免做 k 次 O(n) 找尾操作。

## 项目经验版

来源没有真实项目或性能数据，不能虚构线上使用链表旋转的经历。实际代码里如果只是业务容器重排，通常优先使用语言标准集合而不是手写链表；这道题的价值在于验证指针不变量。工程验证应特别检查“没有丢节点、没有重复节点、没有遗留环”，而不仅是输出值看起来正确。

## 常见追问

- 问：为什么不每次把尾节点摘下来放到头部？答：一次旋转就要先找到尾及前驱，单链表是 O(n)，重复 k 次最坏 O(kn)；闭环找切口只需 O(n)。
- 问：为什么需要 `k % n`？答：完整旋转 n 次结构回到原样，模运算消掉整圈；也避免 k 很大时做无意义工作。
- 问：怎么证明没有丢节点？答：成环前链表的每个原节点都在唯一 next 链上；成环只新增一条 `tail→head` 边，最后只删除新尾的一条出边，因此节点集合不变，只改变线性起点。
- 问：如何检测忘记断环？答：测试遍历时限制最多 n 个节点并要求第 n 个节点的 next 为 null，或者用快慢指针检查最终结果无环。
- 问：能不能用快慢指针？答：可以在得到 n 和 shift 后让快指针先走 shift，再快慢一起到尾，此时慢指针定位新尾；本质仍是在找同一个切口。

## 易错点

- 空链表时就执行 `k % n`，触发除零。
- 把新尾位置写成 `n-shift` 条边而多走一步。
- `shift==0` 时仍成环却没有正确断开。
- 只比较输出值，没检查原节点身份、节点数量和是否产生环。
- 把负 k 交给 `%` 后继续执行，却没有定义左旋或负数契约。
