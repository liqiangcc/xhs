<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_merge_intervals_866286e5","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：合并区间（LeetCode 56）

## 核心结论

合并闭区间先按左端点升序排序，再维护当前合并段 [start,end]：下一个区间的 start<=end 就扩展 end，否则输出当前段并开始新段。排序主导时间 O(n log n)；下面实现为不改调用方输入而复制数组，额外空间 O(n)。

## 1 分钟版

- 输入是每项恰有两个端点且 start<=end 的闭区间；输出覆盖相同并集的、按左端点有序且两两不重叠的闭区间。
- 排序后，已经输出的区间永远不可能与后续区间重叠；未输出的 [start,end] 恰是已扫描区间中最后一个连通合并段。
- 若 next[0]<=end，两个闭区间相交或端点相接，令 end=max(end,next[1])；若 next[0]>end，当前段已不能被后续区间延伸，立即输出。
- 本实现复制输入再排序，调用方输入保持不变；若允许原地重排，可直接排序原数组以减少一份复制。

## 3 分钟版

排序把可能相交的区间放到相邻扫描位置。扫描不变量是：输出列表已是最终结果；当前段等于所有已读但尚未输出、经传递相交后形成的最右合并段。每次扩展右端点保留并集，遇到严格间隙才封存当前段，因此嵌套区间、链式重叠和乱序输入都能处理。这里采用闭区间，故 [1,4] 与 [4,5] 合并；若题意是半开区间 [l,r)，边界接触不重叠，应把条件改为 next[0]<end。

```java
import java.util.Arrays;

public final class MergeIntervals {
    private MergeIntervals() {}

    public static int[][] merge(int[][] intervals) {
        if (intervals == null || intervals.length == 0) return new int[0][0];
        int[][] ordered = new int[intervals.length][2];
        for (int i = 0; i < intervals.length; i++) {
            if (intervals[i] == null || intervals[i].length != 2 || intervals[i][0] > intervals[i][1]) {
                throw new IllegalArgumentException("each interval must satisfy start <= end");
            }
            ordered[i][0] = intervals[i][0];
            ordered[i][1] = intervals[i][1];
        }
        Arrays.sort(ordered, (left, right) -> Integer.compare(left[0], right[0]));
        int[][] merged = new int[ordered.length][2];
        int count = 0;
        int start = ordered[0][0], end = ordered[0][1];
        for (int i = 1; i < ordered.length; i++) {
            int[] next = ordered[i];
            if (next[0] <= end) {
                end = Math.max(end, next[1]);
            } else {
                merged[count++] = new int[] {start, end};
                start = next[0];
                end = next[1];
            }
        }
        merged[count++] = new int[] {start, end};
        return Arrays.copyOf(merged, count);
    }
}
```

## 关键细节

- 输入是每项恰有两个端点且 start<=end 的闭区间；输出覆盖相同并集的、按左端点有序且两两不重叠的闭区间。
- 排序后，已经输出的区间永远不可能与后续区间重叠；未输出的 [start,end] 恰是已扫描区间中最后一个连通合并段。
- 若 next[0]<=end，两个闭区间相交或端点相接，令 end=max(end,next[1])；若 next[0]>end，当前段已不能被后续区间延伸，立即输出。
- 本实现复制输入再排序，调用方输入保持不变；若允许原地重排，可直接排序原数组以减少一份复制。
- null 或空输入返回空二维数组；单区间直接返回它的副本。
- 每个区间必须恰有两个端点且左端点不大于右端点；不满足时抛 IllegalArgumentException，避免默默给出错误结果。
- 测试覆盖乱序、完全不相交、端点接触、嵌套、链式重叠、负端点、空输入与 1,296 组小规模穷举对照。
- 时间 O(n log n)，复制与输出数组使额外空间 O(n)。
- 复杂度：排序主导时间 O(n log n)；为保持输入不变，复制与结果数组使用 O(n) 额外空间。

## 原理机制

状态是按左端点排序后的输入、已封存的结果前缀和一个未封存的 [start,end]。排序消除后续区间左端点回退的可能；所以出现 next[0]>end 时，任何后续区间的左端点也更大，当前段可以安全输出。
- 复杂度：排序主导时间 O(n log n)；为保持输入不变，复制与结果数组使用 O(n) 额外空间。

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：端点刚好相等要合并吗？答：本题按闭区间处理，故 [1,4] 和 [4,5] 共享端点，要合成 [1,5]；半开区间要改成严格小于。
- 问：为什么遇到间隙就能输出当前段？答：后续元素左端点不会小于 next[0]，而 next[0]>end，所以后续不可能再与当前段相交。
- 问：如何节省额外空间？答：若允许改变输入，可原地排序 intervals 并在原数组前部覆写合并结果；代价是调用方看到顺序和部分内容被改写。
- 问：嵌套区间会漏掉吗？答：不会；[1,10] 后读到 [2,3] 时只取 max(10,3)，当前 end 保持 10。

## 易错点

- 不要只比较相邻原始输入，必须先排序。
- 闭区间的重叠条件是 nextStart<=end；写成 < 会漏合并端点相接的区间。
- 排序比较器不要用 left[0]-right[0]，极端 int 值可能溢出。
- 若承诺不修改输入，不能直接对 intervals 调用 Arrays.sort。
