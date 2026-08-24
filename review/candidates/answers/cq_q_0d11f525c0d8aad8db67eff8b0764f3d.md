<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_0d11f525c0d8aad8db67eff8b0764f3d","version":1,"status":"draft","updated_at":"2026-08-21","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：求数组中 K 个最小元素——先锁定重复值、顺序和输入修改契约

## 核心结论

仓库恢复出的原题只有“算法：求数组中 K 个最小的元素”，没有说明结果是否去重、是否要求有序、是否允许修改原数组，也没有给 `K` 越界行为。因此候选答案先声明一个可验证契约：**按数组元素的出现次数保留重复值，返回升序的 K 个最小元素，不修改输入；要求 `0 <= K <= n`**。

在这个契约下，用大小最多为 `K` 的**大顶堆**最稳妥：遍历数组时，堆里始终保留“截至当前已经看到的 K 个最小元素”；新元素若比堆顶更小，就弹出当前候选中最大的元素并放入新元素。扫描结束后，堆中就是全局 K 个最小元素。若最终输出要求升序，再对这 K 个候选排序。

扫描阶段时间复杂度 `O(n log K)`、堆空间 `O(K)`；为了返回升序数组，再增加 `O(K log K)` 排序。如果题目只要求任意顺序的 K 个最小值，可以省掉最后排序。若允许修改输入且更看重平均时间，可讨论 Quickselect：平均 `O(n)`，但最坏 `O(n²)`（取决于 pivot 策略），且会重排输入。

## 1 分钟版

我先确认三个点：重复值算不算、结果要不要排序、能不能改原数组。这里选择“保留重复、升序返回、不改输入”。

做法是维护一个大小为 `K` 的大顶堆：

- 堆没满：直接放进去；
- 堆满后，堆顶是当前 K 个候选里最大的；
- 如果新值 `x < heap.peek()`，说明 `x` 应该进入 K 小集合，弹掉堆顶再加入 `x`；
- 否则 `x` 不可能属于当前 K 个最小值，忽略即可。

不变量：处理完任意前缀后，堆恰好保存该前缀中按出现次数计算的 K 个最小元素（当前缀长度小于 K 时保存全部）。

扫描 `O(n log K)`、额外空间 `O(K)`；如果输出必须升序，对 K 个结果再排序，总代价 `O(n log K + K log K)`。

## 3 分钟版

为什么用大顶堆而不是小顶堆？因为我们需要快速找到“当前 K 个最小候选里最不值得保留的那个”，也就是候选中的最大值。大顶堆让这个边界元素始终在堆顶，替换一次只要 `O(log K)`。

正确性可以用归纳不变量证明。处理前 `i` 个元素后，若 `i < K`，堆保存全部已见元素；若 `i >= K`，堆保存这 `i` 个元素中 K 个最小值。加入第 `i+1` 个值 `x` 时：

- 如果堆未满，加入 `x` 后仍保存全部已见元素；
- 如果堆已满且 `x >= maxCandidate`，至少已有 K 个候选不大于 `x`，所以 `x` 不可能挤进 K 小集合；
- 如果 `x < maxCandidate`，当前最大的候选不再属于新的 K 小集合，用 `x` 替换它后不变量恢复。

重复值必须按契约处理。例如 `[1,1,2]`、`K=2` 返回 `[1,1]`，而不是集合语义下的 `[1,2]`。原题没有说“去重”，所以不能擅自改成 distinct Top-K。

实现使用 `PriorityQueue<Integer>` + `Comparator.reverseOrder()`，避免手写 `b - a` 比较器造成整数溢出。最后把堆元素复制到 `int[]` 并排序，保证输出顺序确定。`K=0` 直接返回空数组；`K<0` 或 `K>n` 作为本实现的显式非法参数 fail-fast。`null` 同样是实现层契约，不伪装成原题条件。

## 关键细节

- 原题没有规定“去重”，候选契约保留重复元素的出现次数。
- 原题没有规定结果顺序，候选为了可复习、可测试，明确选择升序输出。
- 原题没有规定能否修改输入；堆方案不修改原数组。
- 大顶堆堆顶是当前 K 小候选中的最大值，正好是下一次可能被淘汰的边界。
- `K=0` 返回空数组，不应访问堆顶。
- `K=n` 时所有元素都会入堆，最后排序后等价于完整升序数组。
- 比较整数不要写 `b-a`，极值输入可能溢出；使用 `Comparator.reverseOrder()`。
- 如果只需要无序 Top-K，可以省掉最终 `K log K` 排序。
- Quickselect 是另一种重要答案：允许改输入时平均 `O(n)`、额外空间可做到较低，但需要说明 pivot 退化和最坏复杂度边界。

## 原理机制

```java
import java.util.Arrays;
import java.util.Comparator;
import java.util.Objects;
import java.util.PriorityQueue;

public final class KSmallest {
    private KSmallest() {}

    public static int[] kSmallest(int[] values, int k) {
        Objects.requireNonNull(values, "values");
        if (k < 0 || k > values.length) {
            throw new IllegalArgumentException("k must be between 0 and values.length");
        }
        if (k == 0) {
            return new int[0];
        }

        PriorityQueue<Integer> maxHeap =
                new PriorityQueue<>(k, Comparator.reverseOrder());

        for (int value : values) {
            if (maxHeap.size() < k) {
                maxHeap.add(value);
            } else if (value < maxHeap.peek()) {
                maxHeap.poll();
                maxHeap.add(value);
            }
        }

        int[] result = new int[k];
        int index = 0;
        while (!maxHeap.isEmpty()) {
            result[index++] = maxHeap.poll();
        }
        Arrays.sort(result);
        return result;
    }
}
```

仓库中的确定性测试使用一个结构不同的 oracle：复制输入、对整份副本执行升序排序，再截取前 K 个元素。固定用例覆盖 `K=0`、`K=n`、重复值、负数和 `Integer.MIN_VALUE/MAX_VALUE`；随后用固定随机种子生成 5000 组数组和 K，与排序 oracle 对照，并额外验证输入数组没有被修改。`null`、`K<0`、`K>n` 也单独验证 fail-fast。

## 项目经验版

这是算法手撕题，原始面试记录没有生产业务背景，不应虚构线上数据。工程上可以迁移的是“先把 Top-K 契约说清楚”：流式数据、不允许全量驻留内存时，大小 K 的堆很自然；如果数据全部在内存、允许原地修改且只做一次查询，Quickselect 可能更合适；如果后续还需要全序，直接排序反而更简单。

## 常见追问

- 问：为什么求 K 个最小值却用大顶堆？答：因为要 O(1) 看见当前候选里最大的那个；新元素更小时，正好淘汰这个边界元素。
- 问：为什么不是小顶堆？答：小顶堆能快速拿到全局最小值，但若只维护 K 个候选，无法 O(1) 找到“候选中最大者”来决定替换。
- 问：重复元素怎么算？答：原题没说 distinct；本契约按数组出现次数保留重复值，例如 `[1,1,2]`、K=2 返回 `[1,1]`。
- 问：能做到平均 O(n) 吗？答：允许修改输入时可用 Quickselect，把第 K 个顺序统计量放到正确分区位置；平均 O(n)，但普通随机/启发式 pivot 仍要说明最坏 O(n²)。
- 问：如果 K 很接近 n 呢？答：堆方案仍正确，但 `log K` 接近 `log n`；若还要求有序结果，直接排序可能更简单，常数也可能更好。
- 问：如何证明不是只过样例？答：用完整排序后取前 K 作为结构不同的 oracle，对大量固定种子随机数组比较，并检查重复值、整数极值、K 边界和输入不变性。

## 易错点

- 求 K 个最小值却维护小顶堆大小 K，导致无法高效淘汰当前候选最大值。
- 把“元素”擅自解释成 distinct 集合，错误丢掉重复值。
- 使用 `b-a` 构造降序比较器，在整数极值上溢出。
- `K=0` 仍访问 `heap.peek()`。
- 忘记校验 `K>n` 或负数，产生隐式异常或错误结果。
- 声称堆方案返回升序，却没有对最终 K 个元素排序。
- 只说 Quickselect `O(n)`，不注明平均复杂度、最坏退化与是否修改输入。
