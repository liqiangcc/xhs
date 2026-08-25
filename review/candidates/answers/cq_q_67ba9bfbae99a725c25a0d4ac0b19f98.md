<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_67ba9bfbae99a725c25a0d4ac0b19f98","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# 和为 K 的倍数的连续子数组：前缀余数 + 哈希

## 核心结论

当前来源只保留了“和为 K 的倍数的连续子数组（Good Subarrays，利用前缀和与哈希优化）”，并把业务上下文写成 `LeetCode 523/974`。这两个题号对应的常见任务并不完全相同：一类问“是否存在长度至少为 2 的连续子数组”，另一类问“这样的连续子数组有多少个”。因此不能擅自把来源收窄成其中一个。本答案保留这个歧义，给出同一个前缀余数不变量下的两个可执行入口：`existsLengthAtLeastTwoMultipleOfK` 判断存在性，`countSubarraysMultipleOfK` 统计数量。

共同机制是：若两个前缀和 `prefix[j]` 与 `prefix[i]` 对 `|k|` 的余数相同，则 `prefix[j] - prefix[i]` 能被 `k` 整除，对应区间和就是 `k` 的倍数。存在性只需记“某余数第一次出现的位置”；计数则要记“某余数之前出现了多少次”。

## 1 分钟版

- 来源明确给了“前缀和 + 哈希”，但没有保存到底要返回 boolean 还是数量；`LeetCode 523/974` 反而说明两种变体都要区分。
- 设模数 `m = |k|`，示例契约要求 `k != 0`；对负数元素，用 `floorMod` 把余数规范到 `[0, m)`。
- 对计数版：哈希表 `freq[r]` 保存此前前缀余数 `r` 出现次数，初始 `freq[0]=1` 代表空前缀。当前余数为 `r` 时，之前每一个同余前缀都形成一个合法连续子数组，所以答案增加 `freq[r]`，再将它加一。
- 对存在版：哈希表保存余数第一次出现的前缀位置，初始 `remainder 0 -> index -1`。再次看到同余数且下标差至少 2，就存在长度至少 2 的合法子数组。
- 两个方法都只保留前缀余数，不需要保存完整前缀和数组；平均时间 O(n)，额外空间最多 O(min(n, |k|)) 个余数桶。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

final class SubarrayMultipleOfK {
    static long countSubarraysMultipleOfK(int[] nums, int k) {
        requireInput(nums, k);
        long mod = Math.abs((long) k);
        Map<Long, Long> freq = new HashMap<>();
        freq.put(0L, 1L);
        long remainder = 0;
        long count = 0;
        for (int x : nums) {
            remainder = Math.floorMod(remainder + x, mod);
            long previous = freq.getOrDefault(remainder, 0L);
            count += previous;
            freq.put(remainder, previous + 1);
        }
        return count;
    }

    static boolean existsLengthAtLeastTwoMultipleOfK(int[] nums, int k) {
        requireInput(nums, k);
        long mod = Math.abs((long) k);
        Map<Long, Integer> firstIndex = new HashMap<>();
        firstIndex.put(0L, -1);
        long remainder = 0;
        for (int i = 0; i < nums.length; i++) {
            remainder = Math.floorMod(remainder + nums[i], mod);
            Integer first = firstIndex.get(remainder);
            if (first != null) {
                if (i - first >= 2) return true;
            } else {
                firstIndex.put(remainder, i);
            }
        }
        return false;
    }

    private static void requireInput(int[] nums, int k) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (k == 0) throw new IllegalArgumentException("this candidate defines the modulo contract only for k != 0");
    }
}
```

计数版的不变量是：处理到当前位置之前，`freq[r]` 精确等于“已经见过的前缀中，规范化余数为 `r` 的个数”；所以当前前缀余数 `r` 与这 `freq[r]` 个旧前缀分别配对，恰好得到所有以当前位置为右端点的合法子数组。

存在版只需要判断有没有一个足够早的同余前缀，所以对每个余数保留最早下标最有利：它最大化区间长度，也避免后来的同余位置覆盖掉一个能满足“长度至少 2”的证据。

## 关键细节

- **为什么同余就能判定**：区间 `(i, j]` 的和是 `prefix[j] - prefix[i]`。若两者模 `m` 余数相同，差值模 `m` 为 0。
- **空前缀为什么重要**：计数版 `freq[0]=1` 能统计“从数组开头到当前位置”的合法区间；存在版 `0 -> -1` 能正确计算这类区间的长度。
- **为什么存在版保存最早下标**：同一余数越早出现，和当前下标形成的区间越长。覆盖成较新的下标可能把原本长度 >= 2 的证据丢掉。
- **负数元素**：Java `%` 对负数可能返回负余数，所以示例使用 `Math.floorMod` 统一余数类别；否则数学上同一个余数类可能被拆成正负两个键。
- **负 `k`**：是否允许负 `k` 没有保存在来源中；本候选把 `k` 与 `-k` 视为相同“倍数”关系，所以取 `abs((long) k)`，同时规避 `Math.abs(Integer.MIN_VALUE)` 的 int 溢出。
- **`k == 0`**：来源说的是“K 的倍数/取模”但没有定义 `k=0`。本候选选择显式拒绝，而不是偷偷改成“寻找和为 0 的子数组”；如果面试官定义了 `k=0` 语义，应单独实现该契约。
- **答案类型**：计数最坏可达到 `n(n+1)/2`，因此返回 `long`。

## 原理机制

前缀和把任意连续区间和转换为两个前缀状态之差。进一步对 `k` 取模后，真正需要保存的不是前缀和本身，而是它属于哪个余数等价类：两个前缀落在同一个余数类，当且仅当它们的差能被 `k` 整除。

这使“连续子数组”问题从 O(n²) 的区间枚举变成单次扫描的状态聚合。计数版需要知道一个等价类里已有多少前缀，因此哈希值是频次；存在版还附带长度约束，只需知道同余类最早什么时候出现，因此哈希值是最早下标。两者共享数学不变量，但状态语义不同，不能把两个哈希表机械互换。

## 项目经验版

来源没有提供真实项目、线上规模或性能指标，不能虚构。工程上需要先确定接口到底要求“存在性”还是“数量”，以及 `k=0`、负数、超大 `n` 的契约。如果 `|k|` 很小且稳定，可以用数组代替哈希表降低常数；如果 `|k|` 很大或输入稀疏，哈希表只为实际出现的余数分配状态更合适。是否切换数据结构应由真实约束决定。

## 常见追问

- 问：为什么来源里同时写 523/974 不能直接当成同一道题？答：它们常见的输出目标不同，一个强调是否存在并带长度约束，一个强调计数；当前来源没有保存具体输出，所以答案必须显式区分两种状态语义。
- 问：为什么计数版要先把 `0` 的频次设成 1？答：它代表下标 `-1` 之前的空前缀，让从数组第 0 个元素开始、前缀和本身就是 `k` 倍数的区间也能被同余配对统计。
- 问：存在版为什么不能每次覆盖余数对应的下标？答：需要长度至少 2 时，越早的下标越有价值；覆盖成更晚位置可能把可行长区间缩短成长度 1，从而产生漏判。
- 问：有负数元素会失效吗？答：数学不变量不会失效，但实现必须把余数规范化。这里用 `floorMod`，使例如 `-1 mod 5` 与 `4 mod 5` 落入同一等价类。
- 问：`k=0` 怎么办？答：当前来源没有定义“0 的倍数/取模”语义，本候选显式拒绝。若面试官改成“寻找和为 0 的子数组”，那是另一个可定义的前缀和契约，应单独实现而不是混在取模代码里。
- 问：空间为什么不是一定 O(k)？答：哈希表只存实际出现的余数，最多受前缀个数 `n+1` 和余数类别数 `|k|` 两者较小者限制；若直接用长度 `|k|` 的数组才是固定 O(|k|)。

## 易错点

- 把“是否存在”和“统计数量”混成一个接口，导致哈希值到底该存最早下标还是频次说不清。
- 忘记空前缀种子，漏掉从数组开头开始的合法子数组。
- 存在版覆盖最早下标，导致长度限制下漏判。
- 直接使用 Java 负余数作为哈希键，没有做规范化。
- 对 `Integer.MIN_VALUE` 直接做 int `Math.abs(k)` 导致仍为负数。
- 来源没有定义 `k=0`，却默默套用 `% 0` 或擅自改题。
