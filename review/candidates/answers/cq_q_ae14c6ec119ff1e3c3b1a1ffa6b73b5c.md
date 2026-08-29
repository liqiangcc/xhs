<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ae14c6ec119ff1e3c3b1a1ffa6b73b5c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 一次遍历统计数组中和为 M 的下标数对

## 核心结论

这里把“组合数”明确为满足 `i < j` 且 `nums[i] + nums[j] = M` 的**下标对数量**，同值但下标不同也分别计数。一次遍历时维护“已经看过的值 -> 出现次数”：当前值为 `x` 时，之前每一个值为 `M-x` 的元素都能和当前下标组成一个新数对，因此先把 `seen[M-x]` 加到答案，再把 `x` 的频次加一。这样每个合法下标对只在右端点到来时计算一次，期望时间 O(n)，额外空间 O(u)，u 是不同值个数。

## 1 分钟版

- 只统计 `i < j`，所以天然满足“下标不同”，也不会把同一对算两次。
- `seen` 保存当前下标左侧每个值出现了几次，而不是只保存“出现过/没出现过”。
- 处理 `x` 时，答案增加 `seen[M-x]`；之后再 `seen[x]++`，这一步顺序能正确处理 `M=2x` 的重复值。
- 总候选下标对数是 `C(n,2)=n(n-1)/2`；若某个值 v 出现 f(v) 次，则同值配对在 `2v=M` 时贡献 `C(f(v),2)`，不同值 v,w 且 v+w=M 时贡献 `f(v)f(w)`。
- 如果题目要求“列出所有下标对”而不是只计数，输出本身可能达到 O(n²)，不能再声称总成本只有 O(n)。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

public final class PairSumCounter {
    public static long countPairs(int[] nums, int target) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        Map<Integer, Integer> seen = new HashMap<>();
        long count = 0L;
        for (int x : nums) {
            long needLong = (long) target - x;
            if (needLong >= Integer.MIN_VALUE && needLong <= Integer.MAX_VALUE) {
                count += seen.getOrDefault((int) needLong, 0);
            }
            seen.merge(x, 1, Integer::sum);
        }
        return count;
    }

    public static long totalIndexPairs(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be non-negative");
        return (long) n * (n - 1L) / 2L;
    }
}
```

例如 `[1,5,2,4,3,3]`、`M=6`：处理到 5 时命中之前的 1；处理到 4 时命中之前的 2；第二个 3 到来时命中之前的第一个 3，所以结果是 3。这里统计的是下标组合，不会因为两个 3 的值相同就去重。

## 关键细节

- `seen` 必须存频次。若只存一个下标或布尔值，`[1,1,1,1]`、`M=2` 应有 `C(4,2)=6` 对却会被少算。
- “先查补数、后加入当前值”确保当前元素不会和自己配对；第二个相同值开始才会命中前面的相同值。
- `target - x` 用 `long` 计算，避免 int 减法先溢出后错误命中另一个值。
- Java 数组长度受 int 限制，最大可能下标对数量 `C(Integer.MAX_VALUE,2)` 仍小于 `Long.MAX_VALUE`，因此本合同用 `long` 保存计数。
- 哈希表操作是平均/期望 O(1)；若要求确定性最坏界，可以改用排序 + 双指针，但会变成 O(n log n) 且不再是原顺序的一次扫描。

## 原理机制

把每个合法数对按“右端点 j”唯一归属。遍历到 j 时，左侧所有满足 `nums[i]=M-nums[j]` 的 i 已经被压缩成 `seen` 中的一个频次，所以一次查询就得到以 j 为右端点的新数对数量。把所有 j 的贡献相加，正好覆盖全部 `i<j` 组合且不重不漏。排列组合视角下，总搜索空间是 `C(n,2)`，而频次法把同值组合直接压缩成计数运算。

## 项目经验版

来源没有给数组规模、是否要返回具体下标或是否允许修改输入，不能虚构额外约束。面试时我会先确认“组合数”是计数还是枚举；如果只计数，频次哈希最直接；如果必须输出所有下标对，需要保存每个值对应的历史下标列表，并明确输出规模 k 带来的 O(k) 额外成本。

## 常见追问

- 问：为什么不能用 `Set`？答：Set 只能知道补数是否存在，不能知道出现了几次，会少算重复值形成的多个下标组合。
- 问：`[3,3,3]`、M=6 怎么算？答：三个不同下标两两组合，共 `C(3,2)=3` 对；一次遍历贡献依次是 0、1、2。
- 问：为什么不会重复计数？答：每一对只在较大的那个下标被扫描到时计入，左端点已经在 seen 中，反向顺序不会再出现。
- 问：能不能 O(1) 额外空间？答：若值域很小可用定长频次数组；通用整数值域下想保持一次扫描通常要保存已见信息，否则可排序后双指针换取 O(n log n) 时间并可能修改/复制输入。
- 问：如果要返回所有下标对呢？答：需要把历史下标保留下来并逐个输出，算法内部扫描仍可一次完成，但总时间至少是 O(n+k)，k 为输出对数。

## 易错点

- 只判断补数“出现过”，忽略重复值的频次。
- 先把当前值放进 seen，再查补数，导致 `M=2x` 时把自己计入。
- 用 int 直接算 `target-x`，极值输入发生溢出后误命中。
- 把值对去重和下标对计数混为一谈。
- 明明输出所有组合，却仍声称整体复杂度严格 O(n)。
