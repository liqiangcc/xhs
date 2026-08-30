<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_1d62a5e5748bc0cf6fba59fa1d4655aa","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 合并 K 个升序链表：最小堆维护 K 路归并前沿

## 核心结论

来源只要求“合并 K 个有序/升序链表”，没有规定语言、节点定义、是否复制节点或异常输入。这里声明一个可执行 Java 合同：每条输入链表按 `val` 非递减、无环，并且不同输入链表之间不共享节点；`lists == null`、空数组和数组中的 `null` 链表都允许。实现使用大小最多为 K 的最小堆，每次弹出当前最小节点并把它的后继压入堆，直接复用并重新串联原节点。若总节点数为 N，时间 O(N log K)，堆额外空间 O(K)。

## 1 分钟版

- 每条链表已经有序，所以任意时刻全局最小未输出节点一定在 K 条链表各自的“当前头节点”中。
- 把所有非空头节点放入最小堆；弹出最小节点接到答案尾部，再把这个节点原来的 `next` 入堆。
- 堆里每条链表最多保留一个前沿节点，因此大小最多 K。
- 每个节点只入堆、出堆各一次，总时间 O(N log K)，额外堆空间 O(K)。
- 比较整数时用 `Integer.compare(a.val, b.val)`，不要写 `a.val - b.val`，否则极值可能溢出并破坏堆顺序。

## 3 分钟版

```java
import java.util.PriorityQueue;

public final class MergeKSortedLists {
    private MergeKSortedLists() {}

    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode mergeKLists(ListNode[] lists) {
        if (lists == null || lists.length == 0) {
            return null;
        }

        PriorityQueue<ListNode> heap =
                new PriorityQueue<>((a, b) -> Integer.compare(a.val, b.val));
        for (ListNode head : lists) {
            if (head != null) {
                heap.offer(head);
            }
        }

        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (!heap.isEmpty()) {
            ListNode node = heap.poll();
            ListNode next = node.next;
            tail.next = node;
            tail = node;
            if (next != null) {
                heap.offer(next);
            }
        }
        tail.next = null;
        return dummy.next;
    }
}
```

关键动作是先保存 `node.next`，再把 `node` 接到结果尾部。因为这个参考实现复用原节点，最终把 `tail.next` 设为 `null`，明确终止新链表。输入链表之间必须节点互斥；如果同一个节点同时出现在两条输入链表里，复用式归并会重复遇到同一对象，必须先改变合同或改成复制值/节点的版本。

## 关键细节

- **输入排序**：合同要求每条链表按 `val` 非递减。若输入本身无序，最小堆只看到每条链表的前沿，不能保证结果全局有序。
- **节点所有权**：当前版本复用并重新链接原节点，因此调用后不应再依赖原链表结构。如果业务要求输入不可变，应创建新节点，时间复杂度不变但额外分配 O(N) 个节点。
- **节点不共享**：不同输入链表必须 node-disjoint。共享尾部、同一头节点重复传入等情况会让同一对象被重复调度；这是当前合同之外的输入。
- **重复值**：允许重复值。相同 `val` 节点的相对次序没有额外稳定性承诺，因为来源没有要求稳定归并；只保证最终值序列非递减。
- **比较器溢出**：`Integer.compare` 对 `Integer.MIN_VALUE`/`MAX_VALUE` 安全；直接相减可能溢出导致错误顺序。
- **K 与 N**：当 K=1 时只是返回并复用唯一链表；当 K 很大但多数链表为空时，实际堆大小只取决于非空前沿数量，仍不超过 K。

## 原理机制

这是标准 K 路归并。因为每条链表单调非递减，链表内部还没暴露的节点一定不小于它当前的头节点；所以要找所有未输出节点中的最小值，只需要比较每条链表的一个前沿节点。最小堆把“在最多 K 个前沿里找最小值”从 O(K) 降到 O(log K) 更新成本。

一个节点被弹出后，它所属链表的下一个节点才成为新的前沿，因此把 `next` 入堆即可维持不变量。整个过程不会把一条链表的多个未决节点同时塞进堆，所以空间与 N 无关，只有 O(K)。

## 项目经验版

来源没有真实项目背景，不能虚构线上规模或性能收益。面试手撕时我会先确认三件事：是否允许改写输入节点、链表是否保证无环且彼此不共享、返回值/节点类型是否固定。实现后除了值序列，还应验证对象层面的合同：复用版必须保证每个输入节点恰好出现一次、没有新环、尾节点 `next == null`。这里的可执行验证同时检查了这些结构约束，并用随机有序链表与“收集所有值后排序”的独立 oracle 做差分。

## 常见追问

- 问：为什么堆大小是 K 而不是 N？答：每条有序链表只需要暴露一个当前前沿；该节点弹出后才把它的后继加入，所以每条链表同时最多贡献一个堆元素。
- 问：分治两两合并可以吗？答：可以。每轮两两合并，节点经历 O(log K) 轮，总时间同样是 O(N log K)；递归/轮次管理的额外空间与实现有关。最小堆版本更直接地表达 K 路归并。
- 问：为什么不用每轮扫描 K 个头节点？答：那样每输出一个节点要 O(K) 找最小值，总时间 O(NK)；堆把选择最小前沿降到 O(log K)。
- 问：为什么比较器不能写 `a.val - b.val`？答：当一个接近 `Integer.MIN_VALUE`、另一个接近 `Integer.MAX_VALUE` 时减法会溢出，符号可能反转；`Integer.compare` 不依赖可能溢出的差值。
- 问：输入链表可以共享尾部吗？答：当前复用节点合同不允许。共享对象会被不同前沿重复调度，必须先去重/检测共享，或者改成按值复制新节点并重新定义重复语义。
- 问：要保持相同值节点的稳定顺序怎么办？答：需要在堆元素里增加明确 tie-break，例如链表编号和该链表内序号；来源没有稳定性要求，所以参考实现不额外承诺。

## 易错点

- 把每条链表的全部节点一次性放入堆，虽然也能排序，但空间退化到 O(N)，失去 K 路归并的前沿性质。
- 比较器用减法导致整数溢出，极值输入下堆顺序错误。
- 复用节点时忘记保存原 `next`，先改链再访问后继，导致丢链。
- 没有声明输入链表无环、已排序且彼此不共享，却把实现描述成对任意链表都安全。
- 题目要求输入不可变时仍直接重连原节点，破坏调用方持有的原结构。
- 只验证最终值有序，不验证节点是否重复、遗漏或形成环。
