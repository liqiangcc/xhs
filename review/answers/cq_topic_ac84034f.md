<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_ac84034f","version":2,"status":"ready","updated_at":"2026-07-10"} -->
# 算法：最长递增子序列 (LIS)

## 核心结论

LIS 常见两种做法：动态规划 O(n^2)，以及贪心加二分 O(n log n)。面试中要能讲清楚 dp[i] 表示以 i 结尾的最长递增子序列长度，优化版 tails[k] 表示长度为 k+1 的递增子序列的最小结尾值。

## 1 分钟版

O(n^2) 做法是：dp[i]=1，遍历 j<i，如果 nums[j]<nums[i]，则 dp[i]=max(dp[i], dp[j]+1)，答案是 max(dp)。O(n log n) 做法维护 tails 数组，对每个 num，用二分找到第一个大于等于 num 的位置替换它；如果 num 比所有尾部都大，就追加。tails 长度就是 LIS 长度。

## 3 分钟版

动态规划直观但复杂度高。它枚举每个位置作为结尾，看前面哪些更小的数可以接上。贪心二分的核心思想是：同样长度的递增子序列，结尾越小，未来越有机会接更大的数。因此 tails[len] 保存长度 len+1 的递增子序列能达到的最小结尾。遍历新数时，用 lower_bound 替换第一个 >= num 的位置，保持 tails 单调递增。注意 tails 不一定是真实 LIS 序列，但长度一定正确。

## 关键细节

- 严格递增用第一个 >= num 的位置替换。
- 非严格递增要调整为第一个 > num。
- tails 数组表示最优结尾，不一定是最终序列。
- 如果要输出具体序列，需要额外记录前驱。
- 二分解法时间复杂度 O(n log n)，额外空间 O(n)；朴素 DP 时间 O(n²)、空间 O(n)。

## 原理机制

- DP 利用最优子结构：以 i 结尾依赖更早且更小的元素。
- 贪心利用“同长度小尾部更优”的支配关系。
- 二分来自 tails 的单调性。

```java
int lengthOfLIS(int[] nums) {
    int[] tails = new int[nums.length];
    int size = 0;
    for (int num : nums) {
        int left = 0, right = size;
        while (left < right) {
            int mid = left + (right - left) / 2;
            if (tails[mid] < num) left = mid + 1;
            else right = mid;
        }
        tails[left] = num;
        if (left == size) size++;
    }
    return size;
}
```

## 项目经验版

算法训练映射：复习时要能解释 tails 的语义并手写 lower_bound。迁移到俄罗斯套娃信封时，先按宽度升序、同宽高度降序，再对高度做严格 LIS；这是算法变体，不应虚构为项目经历。

## 常见追问

- 问：如何输出 LIS 序列？答：除 tails 值外记录每个长度对应的下标和每个元素的前驱，最后从最长序列末尾沿前驱回溯。
- 问：严格递增和非递减有什么区别？答：严格递增替换第一个 `>= num` 的位置；非递减替换第一个 `> num` 的位置，二分边界不同。
- 问：俄罗斯套娃信封怎么转成 LIS？答：宽度升序、同宽高度降序后，对高度求严格 LIS；同宽降序防止同宽信封被错误嵌套。
- 问：tails 是不是最终 LIS？答：不一定。替换操作只保证每个长度的最小尾值和正确长度，若要恢复真实序列必须记录下标与前驱。

## 易错点

- 把 tails 当成真实答案序列。
- 二分边界写错导致重复元素处理错误。
- 忘记 DP 初始值是 1。
