<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_ac84034f","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：最长递增子序列 (LIS)

## 核心结论

求严格递增 LIS 长度可维护 tails：tails[len-1] 是长度为 len 的递增子序列可取得的最小结尾。遍历每个数，用 lower_bound 找第一个大于等于它的位置替换；找不到则追加。tails 长度即答案，时间 O(n log n)。

## 1 分钟版

- 空数组返回 0；这里的递增是严格递增，重复值必须替换同长度结尾，不能把长度增加。
- tails 不保证自身对应输入中的一条完整 LIS；它是用于保留更小结尾、给后续元素更多延伸机会的状态摘要。
- 对 x 找第一个 tails[pos] >= x：pos 等于当前长度时追加，否则替换 tails[pos]。
- 循环不变量：处理前缀后，每个长度的 tails 都是该长度所有严格递增子序列中的最小可达结尾。

## 3 分钟版

替换较大的结尾不会降低已有长度的可达性，反而更容易接入后续更大元素；因此最终 tails.size 是最长长度。严格递增必须用第一个 >= x 的位置；若改为第一个 > x，重复元素会被当作可延长，得到的是非递减序列问题。

```java
import java.util.Arrays;

public final class LongestIncreasingSubsequence {
    private LongestIncreasingSubsequence() {}
    public static int lengthOfLIS(int[] values) {
        if (values == null || values.length == 0) return 0;
        int[] tails = new int[values.length];
        int size = 0;
        for (int value : values) {
            int left = 0, right = size;
            while (left < right) {
                int middle = left + (right - left) / 2;
                if (tails[middle] >= value) right = middle; else left = middle + 1;
            }
            tails[left] = value;
            if (left == size) size++;
        }
        return size;
    }
}
```

## 关键细节

- 空数组返回 0；这里的递增是严格递增，重复值必须替换同长度结尾，不能把长度增加。
- tails 不保证自身对应输入中的一条完整 LIS；它是用于保留更小结尾、给后续元素更多延伸机会的状态摘要。
- 对 x 找第一个 tails[pos] >= x：pos 等于当前长度时追加，否则替换 tails[pos]。
- 循环不变量：处理前缀后，每个长度的 tails 都是该长度所有严格递增子序列中的最小可达结尾。
- 测试覆盖空、全相等、递减、典型混合和含重复值输入。
- 时间 O(n log n)，tails 额外空间 O(n)。
- 若要恢复具体序列，需另存每个元素的前驱和每个长度末尾下标；本实现只返回长度。
- 复杂度：时间 O(n log n)，额外空间 O(n)

## 原理机制

状态按子序列长度分层，tails 的值不是历史选择，而是每层的最优延伸边界。二分定位保证每个输入只修改一个层或新增一层。
- 复杂度：时间 O(n log n)，额外空间 O(n)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么 tails 不是实际 LIS？答：替换某层结尾可能来自不同前缀；它只保存最优结尾，不保存完整路径。
- 问：重复值为什么不增加长度？答：严格递增不允许相等；lower_bound 用 >= 把相等值替换在同一层。
- 问：O(n²) DP 怎么写？答：dp[i] 是以 i 结尾的最大长度，枚举 j<i 且 a[j]<a[i]；更易恢复路径但较慢。
- 问：如何求非递减 LIS？答：把二分条件改为第一个 > value，使相等值可追加；问题定义必须先确认。

## 易错点

- 不要把 tails 直接打印为 LIS。
- 不要把 >= 写成 > 而改变严格递增语义。
- 不要声称该实现能恢复序列。
