<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ea27d2a647ad7ed19a5fb6f9ab5b76d8","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 在有序数组中快速查找所有值为 M 的元素下标

## 核心结论

来源明确要求“长度为 N 的有序数组中，快速查找所有值为 M 的元素下标”，但没有保存升序/降序、返回容器和空结果语义。这里声明最小可执行合同：数组按**非递减升序**排列，返回所有等于 `target` 的 0-based 下标；不存在时返回空数组。

因为相同值在有序数组中一定形成一个连续区间，所以不需要先二分找到一个命中点再向两边线性扩散。直接做两次边界二分：`lowerBound(target)` 找第一个 `>= target` 的位置，`upperBound(target)` 找第一个 `> target` 的位置。若 `lower` 处不是 target，则无结果；否则答案就是连续区间 `[lower, upper)`。查边界 O(log N)，输出 K 个下标本身至少要 O(K)，所以总时间 O(log N + K)，额外搜索空间 O(1)（返回结果不计）。

## 1 分钟版

- 有序数组里所有 M 必然连续，因此目标是找这个连续段的左右边界。
- 第一次二分找第一个 `>= M` 的位置 `left`。
- 第二次二分找第一个 `> M` 的位置 `right`。
- 如果 `left == N` 或 `a[left] != M`，说明 M 不存在，返回空数组。
- 否则所有答案恰好是 `left, left+1, ..., right-1`。
- 两次二分是 O(log N)，生成 K 个下标要 O(K)，总计 O(log N + K)。“返回所有下标”不可能比 O(K) 更快，因为结果本身就有 K 个元素。

## 3 分钟版

```java
public final class SortedArrayTargetIndices {
    public static int[] findAll(int[] nums, int target) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }

        int left = lowerBound(nums, target);
        if (left == nums.length || nums[left] != target) {
            return new int[0];
        }
        int right = upperBound(nums, target);

        int[] result = new int[right - left];
        for (int i = 0; i < result.length; i++) {
            result[i] = left + i;
        }
        return result;
    }

    private static int lowerBound(int[] nums, int target) {
        int lo = 0, hi = nums.length; // 搜索半开区间 [lo, hi)
        while (lo < hi) {
            int mid = lo + ((hi - lo) >>> 1);
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    private static int upperBound(int[] nums, int target) {
        int lo = 0, hi = nums.length;
        while (lo < hi) {
            int mid = lo + ((hi - lo) >>> 1);
            if (nums[mid] <= target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    private SortedArrayTargetIndices() {}
}
```

例如数组 `[1,2,2,2,4,5]`，M=2。`lowerBound(2)=1`，`upperBound(2)=4`，所以结果是 `[1,2,3]`。

## 关键细节

- **连续区间性质**：升序数组中等于 M 的元素不可能分散在多个区间，否则中间元素会破坏有序性。
- **半开区间写法**：二分始终维护 `[lo, hi)`，结束时 `lo == hi`，减少 `mid±1` 和边界越界错误。
- **lower 与 upper 的差别**：lower 在 `nums[mid] >= target` 时收缩右边；upper 只有 `nums[mid] > target` 才收缩右边。
- **不存在 target**：不能只看两个边界差值，先检查 `left < N && nums[left] == target` 最直接。
- **复杂度口径**：边界搜索 O(log N)，构造返回数组 O(K)。如果只要求返回 `[left,right]` 两个边界，可以保持纯 O(log N)。
- **排序方向**：来源只写“有序”，候选选择非递减升序；若实际是降序，需要反转二分比较方向。
- **输入校验**：代码信任“有序”这一来源前置条件。完整验证数组是否有序要 O(N)，若每次查询都验证，会破坏“快速查找”的查询复杂度。

## 原理机制

二分边界不是在找“某一个等于 target 的元素”，而是在找一个单调谓词的分界点。

对 lower bound，谓词 `nums[i] >= target` 在升序数组上形如 `false...false true...true`，二分返回第一个 true。对 upper bound，谓词 `nums[i] > target` 同样是单调的，返回第一个严格大于 target 的位置。两条分界之间恰好满足：

```text
left <= i < right  => nums[i] == target
```

因此不用从一个随机命中点向两边扫描，也不会在 target 不存在时陷入复杂的边界补丁。

## 项目经验版

来源没有真实数组规模、查询频率和存储介质信息，不能虚构业务场景。如果同一个静态数组要执行大量查询，我会保留有序结构并复用这套边界查询；如果数据持续插入/删除，数组维护有序性的成本可能成为瓶颈，此时应根据更新/查询比例考虑树、索引或数据库结构，而不是只优化单次二分。

## 常见追问

- 问：为什么不先二分找到一个 M，再向左右扫？答：最坏情况下数组全是 M，找到一个点后仍要左右扫描 O(N)。两次边界二分能在 O(log N) 内直接确定完整区间，之后只为真实输出支付 O(K)。
- 问：为什么总复杂度不是 O(log N)？答：如果要求返回 K 个具体下标，写出 K 个结果至少就要 O(K)。只有返回左右边界时才是 O(log N)。
- 问：target 不存在怎么办？答：lower bound 仍会返回插入位置；检查该位置是否真的等于 target，不等就返回空数组。
- 问：数组是降序怎么办？答：把比较谓词改成与降序一致的单调条件；当前实现明确只针对非递减升序合同。
- 问：怎么避免 `mid=(lo+hi)/2` 溢出？答：用 `lo + ((hi-lo) >>> 1)`。
- 问：如果只想知道出现次数？答：直接返回 `upperBound - lowerBound`，存在性检查后无需构造 K 个下标。

## 易错点

- 普通二分命中任意一个 M 后就返回，漏掉重复元素。
- 命中后双向扫描，却仍声称最坏时间 O(log N)。
- lower/upper 的 `>=`、`>` 条件写反，造成 off-by-one。
- target 不存在时直接构造 `[left,right)`，没有验证真实命中。
- 题目只说“有序”却不声明升序/降序假设。
- 为了证明有序先完整扫描 O(N)，然后忽略这部分成本继续宣称查询 O(log N + K)。
