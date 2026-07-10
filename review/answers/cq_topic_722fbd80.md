<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_722fbd80","version":2,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# 算法：三数之和

## 核心结论

三数之和的标准做法是先排序，再固定一个数，用左右双指针在剩余区间找两数和。关键是剪枝和去重，时间复杂度 O(n^2)，空间复杂度通常 O(1) 或 O(log n) 取决于排序实现。

## 1 分钟版

先把数组排序。遍历下标 i，把 nums[i] 作为第一个数，然后用 left=i+1、right=n-1 找 nums[left]+nums[right] == -nums[i]。如果和太小，left 右移；太大，right 左移；命中后记录答案，并跳过重复的 left/right。外层 i 也要跳过重复值。因为排序后可以有序移动指针，所以避免了三重循环。

## 3 分钟版

算法步骤：第一，排序，方便去重和双指针。第二，外层枚举 i，若 i>0 且 nums[i]==nums[i-1]，跳过，避免重复三元组。第三，如果 nums[i]>0，可以直接结束，因为后面都不小于它，不可能凑成 0。第四，双指针查找目标 -nums[i]。命中后把三元组加入结果，同时 left 跳过相同值，right 跳过相同值，再继续收缩。整个过程中每个 i 对应的 left/right 最多线性移动，所以总复杂度是 O(n^2)。

## 关键细节

- 排序是为了双指针和去重。
- 外层去重避免第一个数重复。
- 内层命中后左右指针都要跳过重复值。
- nums[i] > 0 时可以提前 break。

## 原理机制

- 排序后，left 增大会让和变大，right 减小会让和变小。
- 双指针利用单调性，把两数和查找从 O(n^2) 降到 O(n)。
- 外层枚举 n 次，因此整体 O(n^2)。

```java
List<List<Integer>> threeSum(int[] nums) {
    Arrays.sort(nums);
    List<List<Integer>> ans = new ArrayList<>();
    for (int i = 0; i < nums.length - 2; i++) {
        if (i > 0 && nums[i] == nums[i - 1]) continue;
        if (nums[i] > 0) break;
        int left = i + 1, right = nums.length - 1;
        while (left < right) {
            long sum = (long) nums[i] + nums[left] + nums[right];
            if (sum < 0) {
                left++;
            } else if (sum > 0) {
                right--;
            } else {
                ans.add(List.of(nums[i], nums[left], nums[right]));
                int lv = nums[left], rv = nums[right];
                while (left < right && nums[left] == lv) left++;
                while (left < right && nums[right] == rv) right--;
            }
        }
    }
    return ans;
}
```

## 项目经验版

算法训练映射：这类题考察“排序 + 双指针 + 去重”。复习时应先口述不变量和三层去重，再手写代码并用空数组、全零、重复值和整型边界验证；不要虚构业务项目类比来替代算法证明。

## 常见追问

- 问：目标不是 0 怎么改？答：双指针比较值改为 `(long) target - nums[i]` 或直接比较三数 long 和与 target，排序和去重逻辑不变。
- 问：四数之和怎么做？答：再增加一层固定下标，内层仍用双指针，并对两层固定值及左右指针分别去重；复杂度通常 O(n^3)。
- 问：为什么不只用 HashSet 去重？答：集合能事后去重，但对象构造和哈希开销更大，也容易掩盖重复来源；排序后在指针层去重更直接且输出稳定。
- 问：代码为什么用 long 计算 sum？答：三个 int 相加可能溢出，使用 long 避免比较结果因溢出而错误。

## 易错点

- 命中后只移动一个指针会漏掉或重复答案。
- 外层 i 不去重会产生重复三元组。
- 不要把复杂度说成 O(n log n)，排序不是主导项。
