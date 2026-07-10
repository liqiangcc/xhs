<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_merge_intervals_866286e5","version":2,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# 算法：合并区间（LeetCode 56）

## 核心结论

合并区间的核心是先按区间起点排序，再线性扫描维护当前已合并区间。若下一个区间起点不超过当前终点，就合并；否则把当前区间放入结果并开启新区间。

## 1 分钟版

先把 intervals 按 start 升序排序。遍历时维护结果列表最后一个区间。如果当前区间 start 小于等于结果最后区间 end，说明有重叠，把 end 更新为两者最大值；否则当前区间直接加入结果。时间复杂度主要来自排序，是 O(n log n)，额外空间看是否原地存结果，一般是 O(n)。

## 3 分钟版

排序后有一个关键性质：如果当前区间和结果中最后一个区间都不重叠，那么它也不可能和更早的区间重叠，因为更早区间的 end 已经被合并到了最后结果里。判断重叠通常使用 `current.start <= last.end`，如果题目把相邻区间也视为可合并，这个条件正好覆盖端点相等。合并时只需要更新右边界，因为左边界已经由排序保证是较小值。

```java
import java.util.*;

class Solution {
    public int[][] merge(int[][] intervals) {
        if (intervals == null || intervals.length == 0) return new int[0][0];
        Arrays.sort(intervals, Comparator.comparingInt(a -> a[0]));
        List<int[]> merged = new ArrayList<>();
        int start = intervals[0][0], end = intervals[0][1];
        for (int i = 1; i < intervals.length; i++) {
            if (intervals[i][0] <= end) {
                end = Math.max(end, intervals[i][1]);
            } else {
                merged.add(new int[]{start, end});
                start = intervals[i][0];
                end = intervals[i][1];
            }
        }
        merged.add(new int[]{start, end});
        return merged.toArray(new int[merged.size()][]);
    }
}
```

## 关键细节

- 必须先排序，否则无法只扫描一次。
- 重叠条件一般是当前 start 小于等于 last end。
- 合并后 end 取最大值。
- 空数组或单个区间要直接返回。
- 输入若可能出现 `start > end`，要先明确是拒绝还是规范化；基础题通常保证合法闭区间。
- 时间复杂度 O(n log n)，扫描 O(n)；除排序与输出外工作空间取决于排序实现，结果需要 O(n)。

## 原理机制

- 排序把可能重叠的区间放到相邻位置。
- 线性扫描维护一个已合并的右边界。
- 贪心策略保证每次都把当前能合并的区间扩到最大。

## 项目经验版

算法训练映射：类似思路可用于时间段、会议室占用、活动生效区间和 IP 段合并。业务映射前必须明确闭区间/半开区间、时区以及端点相等是否冲突，不能把算法题包装成未发生的项目经历。

## 常见追问

- 问：为什么只看结果最后一个区间？答：结果区间按起点有序且彼此不重叠；当前起点若已大于最后终点，也必然大于更早区间终点。
- 问：端点相等算重叠吗？答：闭区间算，所以用 `<=`；半开区间通常不算，应改为 `<`，以题目语义为准。
- 问：能做到 O(n) 吗？答：若输入已按起点有序可以；一般无序输入的比较排序下总复杂度 O(n log n)。
- 问：有什么常见变体？答：插入新区间可先复制左侧不重叠段、合并重叠段再复制右侧；会议室数量则需扫描端点或最小堆。

## 易错点

- 不要漏掉排序。
- 不要在合并时错误覆盖左边界。
- 不要把 `<` 和 `<=` 的边界语义混淆。
- 复习反馈：复杂度先说无序输入排序 O(n log n)，再说扫描 O(n)；判断 `<`/`<=` 前先确认闭区间还是半开区间。
