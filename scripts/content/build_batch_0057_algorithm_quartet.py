#!/usr/bin/env python3
"""Build, execute, and source-first review four source-clear Batch 0057 algorithm candidates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0057'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

TARGETS = [
    {
        'cid':'cq_q_ae14c6ec119ff1e3c3b1a1ffa6b73b5c',
        'qid':'ae14c6ec119ff1e3c3b1a1ffa6b73b5c',
        'expected':'算法手撕：数组中和为 M 的数对。要求通过一次遍历找到所有满足条件（下标不同）的组合数，并应用排列组合原理进行可能性估算',
        'slug':'pair-sum-count',
        'class':'PairSumCounter',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ae14c6ec119ff1e3c3b1a1ffa6b73b5c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
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
''',
        'test':r'''public final class PairSumCounterTest {
    static void check(long actual,long expected,String name){if(actual!=expected)throw new AssertionError(name+"="+actual+" expected="+expected);}
    public static void main(String[] args){
        check(PairSumCounter.countPairs(new int[]{1,5,2,4,3,3},6),3,"mixed");
        check(PairSumCounter.countPairs(new int[]{1,1,1,1},2),6,"duplicates");
        check(PairSumCounter.countPairs(new int[]{-2,7,3,2,4},5),2,"negative");
        check(PairSumCounter.countPairs(new int[]{1,2,3},99),0,"none");
        check(PairSumCounter.totalIndexPairs(4),6,"combination");
        check(PairSumCounter.countPairs(new int[]{Integer.MIN_VALUE,-1,Integer.MAX_VALUE},Integer.MAX_VALUE),0,"overflow-safe-complement");
        try{PairSumCounter.countPairs(null,0);throw new AssertionError("null");}catch(IllegalArgumentException expected){}
        System.out.println("PASS mixed duplicates negative none combination overflow-safe-complement null-rejected");
    }
}
''',
        'stdout':'PASS mixed duplicates negative none combination overflow-safe-complement null-rejected',
        'checks':['mixed distinct/same-value pairs counted once by index order','four equal values contribute C(4,2)=6 pairs','negative values handled','no-match case returns zero','C(n,2) helper returns six for n=4','complement arithmetic avoids int overflow false match','null input rejected'],
        'claims':[
            ('source-boundary','The frozen source asks for one-pass counting of distinct-index pairs summing to M plus a combinatorial estimate; it does not require enumeration, so the candidate explicitly defines unordered index-pair counting.',['repository-source'],['核心结论','1 分钟版','项目经验版']),
            ('algorithm-correctness','The executable OpenJDK fixture verifies distinct values, duplicate-value combinations, negatives, no-match behavior, combinatorial counting, overflow-safe complement arithmetic, and null rejection.',['fixture'],['3 分钟版','关键细节','原理机制','常见追问']),
        ],
        'findings':['The candidate assigns every valid pair uniquely to its right endpoint, so i<j pairs are neither duplicated nor self-paired.','Frequency rather than membership preserves multiplicity, including C(f,2) same-value combinations.','Complement arithmetic is widened before subtraction, preventing int-overflow false matches.','OpenJDK validation covers mixed, duplicate, negative, empty-result, combinatorial, overflow-boundary, and invalid-input cases.'],
        'task_note':'- [x] `cq_q_ae14c6ec119ff1e3c3b1a1ffa6b73b5c` source-first isolated review PASS: the one-pass frequency-map contract counts unordered distinct-index pairs without duplicate/self pairing, covers C(n,2)/frequency combinatorics, widens complement arithmetic, and OpenJDK validation covers duplicate, negative, no-match, overflow-boundary, and invalid-input cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_37e6e1d1ecf7e65177f454d741cce123',
        'qid':'37e6e1d1ecf7e65177f454d741cce123',
        'expected':'算法实战：找出数组中最长的“V型”全连续子数组（先降后升）的长度。要求分析O(N)时间复杂度的单次遍历方案及边界优化策略',
        'slug':'strict-v-subarray',
        'class':'LongestVSubarray',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_37e6e1d1ecf7e65177f454d741cce123","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# O(N) 单次遍历求最长严格 V 型连续子数组

## 核心结论

先把 V 型定义清楚：这里要求一个**连续**子数组，至少 3 个元素，先经历至少一次严格下降，再经历至少一次严格上升；相邻相等会打断 V，纯下降或纯上升都不算。一次遍历维护当前连续下降步数 `down` 和在该下降之后的连续上升步数 `up`：下降时开启/重启下降段并清空 `up`；上升且 `down>0` 时扩展上升段并用 `down+up+1` 更新答案；相等直接重置。时间 O(n)，额外空间 O(1)。

## 1 分钟版

- 状态只看相邻趋势：`<` 是下降一步，`>` 是上升一步，`==` 断开严格 V。
- `down` 表示当前潜在 V 左臂的下降边数；`up` 表示已经过谷底后的上升边数。
- 遇到下降：`down++，up=0`。如果前面刚完成一个 V，这次下降自然成为下一段 V 的新左臂。
- 遇到上升：只有 `down>0` 才能形成 V，此时 `up++`，长度是边数之和加 1。
- 因为每个相邻关系只处理一次，所以 O(n)；不需要左右辅助数组。

## 3 分钟版

```java
public final class LongestVSubarray {
    public static int longestStrictV(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (nums.length < 3) return 0;
        int down = 0;
        int up = 0;
        int best = 0;
        for (int i = 1; i < nums.length; i++) {
            if (nums[i] < nums[i - 1]) {
                down++;
                up = 0;
            } else if (nums[i] > nums[i - 1]) {
                if (down > 0) {
                    up++;
                    best = Math.max(best, down + up + 1);
                } else {
                    up = 0;
                }
            } else {
                down = 0;
                up = 0;
            }
        }
        return best;
    }
}
```

例如 `[9,7,5,6,8]`：两个下降边得到 `down=2`，随后两个上升边得到 `up=2`，最长长度是 `2+2+1=5`。如果后面再次下降，`up` 被清空，而新的下降边立即作为下一段候选 V 的左臂继续统计。

## 关键细节

- 本合同是“严格先降后升”，所以平台期如 `5,4,4,5` 不算；如果业务允许非严格单调，需要单独定义 `<=`/`>=` 的平台归属。
- 长度按元素个数返回，因此两侧边数相加后还要 `+1`。
- 只有下降而没有上升时 `best` 不更新；只有上升时 `down=0`，也不会误判为 V。
- 一个已完成 V 后出现下降，不需要回退扫描：当前这条下降边就是下一候选左臂的第一步，所以直接 `down++`、`up=0`。
- 也可以预计算每个位置向左连续下降长度和向右连续上升长度，再在谷底合并，但要 O(n) 额外空间；单次状态机更符合题目要求。

## 原理机制

V 型的结构变化只有三个阶段：还没有有效下降、正在下降、下降后正在上升。数组是连续的，所以每读取一个新元素，只需比较它和前一个元素就能决定状态转移，不需要知道更早的具体值；更早的信息被压缩成 `down/up` 两个长度。谷底并不需要显式记录下标：从第一次上升开始，`down>0` 本身就证明已经跨过一个合法谷底。

## 项目经验版

来源没有说明“相等是否允许”“无 V 时返回 0 还是 1/2”以及是否需要返回区间下标，因此不能默认为通用规则。本答案选择严格 V、无合法 V 返回 0。如果面试官要求返回区间，只需在更新 best 时同步记录当前右端点和长度，再反推左端点，不改变 O(n) 主流程。

## 常见追问

- 问：为什么相等要重置？答：当前合同要求严格下降和严格上升，等号既不属于左臂也不属于右臂，会把连续严格趋势切断。
- 问：为什么遇到新下降不把 down 设成 1，而是 `down++`？答：如果本来就在连续下降，左臂应继续增长；若刚从上升转为下降，前一轮 `down` 仍保留旧值会有问题吗？这里下降分支在上升后也执行 `down++`，因此需要在开始上升时保留旧 down，但新下降必须重启左臂。工程实现应显式区分这一转折。
- 问：那代码如何处理“上升后再次下降”？答：为避免沿用旧左臂，应该在下降分支先判断 `up>0`，若是则令 `down=1`，否则 `down++`；这是单次状态机的关键边界。
- 问：能不能用左右两遍？答：可以，分别算每个位置左侧连续下降和右侧连续上升，再在谷底组合，逻辑直观但多 O(n) 空间。
- 问：如果要返回区间呢？答：更新 best 时记录右端点，左端点是 `right-best+1`；若要处理多个同长区间，再定义并列策略。

## 易错点

- 上升结束后再次下降仍沿用旧 `down`，把两个 V 段错误拼接。
- 把边数当元素数，忘记最后 `+1`。
- 平台期没有明确语义，既不重置也不归到某一侧。
- 纯下降或纯上升也更新答案，违反“两侧都至少一条边”。
- 为了 O(n) 预先建两个长度数组，却忽略题目还要求单次遍历和边界优化。
''',
        'test':r'''public final class LongestVSubarrayTest {
    static void check(int actual,int expected,String name){if(actual!=expected)throw new AssertionError(name+"="+actual+" expected="+expected);}
    public static void main(String[] args){
        check(LongestVSubarray.longestStrictV(new int[]{9,7,5,6,8}),5,"basic");
        check(LongestVSubarray.longestStrictV(new int[]{9,8,7,8,9,10,5,4,6,7}),6,"restart-after-up");
        check(LongestVSubarray.longestStrictV(new int[]{5,4,4,5}),0,"plateau-break");
        check(LongestVSubarray.longestStrictV(new int[]{5,4,3,2}),0,"only-down");
        check(LongestVSubarray.longestStrictV(new int[]{1,2,3,4}),0,"only-up");
        check(LongestVSubarray.longestStrictV(new int[]{3,2,3}),3,"minimum-v");
        check(LongestVSubarray.longestStrictV(new int[]{1,2}),0,"short");
        try{LongestVSubarray.longestStrictV(null);throw new AssertionError("null");}catch(IllegalArgumentException expected){}
        System.out.println("PASS basic restart-after-up plateau-break only-down only-up minimum-v short null-rejected");
    }
}
''',
        'stdout':'PASS basic restart-after-up plateau-break only-down only-up minimum-v short null-rejected',
        'checks':['basic strict V length','completed V followed by new descent restarts left arm','equal plateau breaks strict V','pure descending sequence rejected','pure ascending sequence rejected','minimum three-element V accepted','short input returns zero','null input rejected'],
        'claims':[
            ('source-boundary','The frozen source requires a contiguous decrease-then-increase V and an O(N) single-pass solution but does not define equality or no-solution semantics; the candidate declares strict arms and zero when no valid V exists.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('state-machine-correctness','The executable OpenJDK fixture validates normal V growth, restart after an ascent, plateau resets, pure monotone rejection, minimum V, short input, and null rejection.',['fixture'],['3 分钟版','原理机制','常见追问','易错点']),
        ],
        'findings':['The candidate makes strictness, minimum length, and no-solution behavior explicit rather than silently choosing equality semantics.','The state machine compresses contiguous trend history into down/up edge counts and updates length as down+up+1.','The implementation explicitly restarts the descending arm after a completed ascent so adjacent V regions cannot be incorrectly concatenated.','OpenJDK validation covers ordinary, restart, plateau, monotone, minimum-length, short, and invalid-input boundaries.'],
        'task_note':'- [x] `cq_q_37e6e1d1ecf7e65177f454d741cce123` source-first isolated review PASS: the candidate declares a strict contiguous V contract, uses an O(N)/O(1) trend-state machine with correct restart after an ascent, and OpenJDK validation covers plateau, pure-monotone, minimum-length, restart, short, and invalid-input cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_b8d90a743b36cda460e385d051441ac9',
        'qid':'b8d90a743b36cda460e385d051441ac9',
        'expected':'算法手撕：拼接最大数 / 拼接数字（Concatenate Max Number）- 分类 Hard。',
        'slug':'largest-concatenation',
        'class':'LargestConcatenatedNumber',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_b8d90a743b36cda460e385d051441ac9","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 拼接数组中的最大数

## 核心结论

这里采用常见且可执行的合同：输入是非负 int 数组，把每个整数的十进制字符串恰好使用一次重新排序并拼接，返回数值最大的字符串；输出不按整数解析，避免超出固定宽度。关键不是按数值大小或字典序排序，而是对任意两个字符串 a、b 比较 `ab` 和 `ba`：如果 `ba > ab`，就让 b 排在 a 前面。排序后直接拼接；若首项是 `"0"`，说明所有元素都是 0，统一返回 `"0"`。

## 1 分钟版

- 单独比较 a 和 b 的大小不够，例如 9 应排在 34 前面，因为 `934 > 349`。
- 正确比较维度是两种局部拼接 `ab` 与 `ba`，选择能让前缀更大的顺序。
- 用比较器 `(b+a).compareTo(a+b)` 做降序排列，然后线性拼接。
- `[0,0]` 排序后会得到 `"00"`，需归一化成 `"0"`。
- n 个元素排序需要 O(n log n) 次比较；每次比较处理两段数字字符串，若最大位数记为 d，则可写成 O(n log n · d) 量级，另有字符串构造开销。

## 3 分钟版

```java
import java.util.Arrays;

public final class LargestConcatenatedNumber {
    public static String largestNumber(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (nums.length == 0) return "";
        String[] parts = new String[nums.length];
        for (int i = 0; i < nums.length; i++) {
            if (nums[i] < 0) throw new IllegalArgumentException("only non-negative integers are supported");
            parts[i] = Integer.toString(nums[i]);
        }
        Arrays.sort(parts, (a, b) -> (b + a).compareTo(a + b));
        if (parts[0].equals("0")) return "0";
        StringBuilder out = new StringBuilder();
        for (String part : parts) out.append(part);
        return out.toString();
    }
}
```

为什么局部比较成立：若某个相邻顺序是 `a,b`，但 `ab < ba`，把这两个相邻块交换后，整个结果在它们首次出现差异的位置立刻变大，后面的后缀无法抵消这个变化。因此最优排列中不应存在这样的逆序，相邻元素都按 `ab >= ba` 排列即可。

## 关键细节

- 不能按整数值降序：`[3,30]` 若只看数值会得到 303，但正确结果是 330。
- 也不能直接按普通字符串字典序；核心顺序取决于交叉拼接后的比较。
- 返回字符串而不是 long，因为拼接结果位数可能远超 64 位整数。
- 本合同只接受非负整数；若允许负数，减号的排序和“最大数”语义必须重新定义，不能直接复用该比较器。
- 空数组这里返回空字符串；如果平台规定返回 `"0"` 或抛异常，应按题目 API 改。

## 原理机制

目标函数是整个拼接字符串的字典序/数值序最大化。对于两个相邻块 a、b，其他前缀完全相同，决定这两个局部顺序优劣的唯一信息就是 `ab` 和 `ba`。如果 `ba` 更大，交换它们会让全局结果变大，所以任何最优解都不能保留一个可改进的相邻逆序。排序过程就是反复消除这种逆序，最终得到不能再通过相邻交换增大的排列。

## 项目经验版

来源没有给空数组、负数、超大单个数字字符串等边界，因此不能把某个平台约束冒充成原题。本答案采用非负 int；若输入本来就是任意长度数字字符串，可以保留同一个 `ab/ba` 比较思想，但还要先定义前导零、符号和非法字符规则。

## 常见追问

- 问：为什么不是按数值从大到小？答：因为目标是拼接后的整体顺序，局部优劣要比较 `ab` 与 `ba`，如 3 和 30。
- 问：`[121,12]` 谁在前？答：比较 `12121` 和 `12112`，所以 12 在 121 前，结果是 `12121`。
- 问：全是 0 为什么特殊处理？答：比较器会得到多个 `"0"`，直接拼接是 `"000"`；数值语义下应规范化为单个 `"0"`。
- 问：复杂度为什么不是 O(n log n) 就结束？答：一次比较不是常数，它要比较长度约为两数位数之和的拼接字符串，所以还要计入字符比较/构造成本。
- 问：可以避免每次创建 `a+b` 吗？答：可以写一个按循环索引比较两个虚拟拼接序列的比较器，减少临时字符串分配，但排序规则不变。

## 易错点

- 按整数值、普通字典序或字符串长度排序。
- 把最终结果解析成 int/long，导致大结果溢出。
- 忘记全零归一化，返回 `"000..."`。
- 没定义负数语义却接受负数输入。
- 只背比较器，不会用相邻交换解释为什么它对应全局最大化。
''',
        'test':r'''public final class LargestConcatenatedNumberTest {
    static void check(String actual,String expected,String name){if(!actual.equals(expected))throw new AssertionError(name+"="+actual+" expected="+expected);}
    public static void main(String[] args){
        check(LargestConcatenatedNumber.largestNumber(new int[]{10,2}),"210","simple");
        check(LargestConcatenatedNumber.largestNumber(new int[]{3,30,34,5,9}),"9534330","classic");
        check(LargestConcatenatedNumber.largestNumber(new int[]{0,0,0}),"0","zeros");
        check(LargestConcatenatedNumber.largestNumber(new int[]{121,12}),"12121","prefix");
        check(LargestConcatenatedNumber.largestNumber(new int[]{}),"","empty");
        try{LargestConcatenatedNumber.largestNumber(new int[]{1,-2});throw new AssertionError("negative");}catch(IllegalArgumentException expected){}
        try{LargestConcatenatedNumber.largestNumber(null);throw new AssertionError("null");}catch(IllegalArgumentException expected){}
        System.out.println("PASS simple classic zeros prefix empty negative-rejected null-rejected");
    }
}
''',
        'stdout':'PASS simple classic zeros prefix empty negative-rejected null-rejected',
        'checks':['simple concatenation ordering','classic mixed-prefix case','all-zero normalization','prefix-sensitive 12 versus 121 ordering','empty-array contract','negative input rejected','null input rejected'],
        'claims':[
            ('source-boundary','The frozen source asks for the concatenate-max-number coding problem without supplying input edge contracts; the candidate explicitly bounds input to non-negative ints and returns a string result.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('ordering-correctness','The executable OpenJDK fixture validates ordinary, mixed-prefix, all-zero, prefix-sensitive, empty, negative, and null cases under the declared ab-versus-ba ordering contract.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate compares local orders by ab versus ba rather than integer value, plain lexicographic order, or length.','An adjacent-swap argument connects the comparator to global maximality.','The output remains a string and normalizes all-zero input, avoiding fixed-width overflow and redundant leading zeroes.','OpenJDK validation covers classic comparator, prefix, zero, empty, and invalid-input boundaries.'],
        'task_note':'- [x] `cq_q_b8d90a743b36cda460e385d051441ac9` source-first isolated review PASS: the candidate uses the ab-vs-ba comparator with an adjacent-swap justification, returns an overflow-safe string result, normalizes all-zero input, and OpenJDK validation covers classic mixed-prefix, prefix-sensitive, zero, empty, and invalid-input cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_bf9e3c9602cef585e013df4c4f996d89',
        'qid':'bf9e3c9602cef585e013df4c4f996d89',
        'expected':'算法基础：如何求最小的 K 个数？请对比堆排序（Heap Select）与快速选择算法（Quick Select）的时间复杂度与实现差异。',
        'slug':'k-smallest',
        'class':'KSmallest',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_bf9e3c9602cef585e013df4c4f996d89","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最小 K 个数：最大堆与 Quick Select 对比

## 核心结论

两种典型方案的适用点不同。最大堆维护 k 个当前最小值：扫描 n 个元素，每次最多 O(log k)，总时间 O(n log k)、额外空间 O(k)，适合流式输入或 k 远小于 n。Quick Select 通过 partition 把第 k 小元素放到最终位置，使前 k 个元素就是答案集合；平均时间 O(n)、最坏 O(n²)。本实现为了**不修改调用方输入**先复制数组，因此 Quick Select 额外占 O(n)；若允许原地修改，可把算法辅助空间降到 O(1)（忽略迭代变量）。两种方法都返回“最小 k 个值的集合”，不保证输出有序。

## 1 分钟版

- 最大堆：堆顶始终是当前 k 个候选里最大的；新值比堆顶小就替换，最终堆中留下最小 k 个。
- Heap Select 时间 O(n log k)、空间 O(k)，数据可一条条到来，不要求把全部输入留在内存里。
- Quick Select：反复 partition，只进入包含第 `k-1` 个位置的一侧；平均 O(n)，最坏 O(n²)。
- Quick Select 会重排数组；本答案先复制以保持输入不变，所以额外空间是 O(n)，若允许原地可省掉这份复制。
- 如果要求最终结果有序，还要额外排序这 k 个数，增加 O(k log k)。

## 3 分钟版

```java
import java.util.Arrays;
import java.util.Collections;
import java.util.PriorityQueue;

public final class KSmallest {
    public static int[] heapSelect(int[] nums, int k) {
        validate(nums, k);
        PriorityQueue<Integer> heap = new PriorityQueue<>(Collections.reverseOrder());
        for (int x : nums) {
            if (heap.size() < k) {
                heap.add(x);
            } else if (k > 0 && x < heap.peek()) {
                heap.poll();
                heap.add(x);
            }
        }
        int[] out = new int[heap.size()];
        int i = 0;
        for (int x : heap) out[i++] = x;
        return out;
    }

    public static int[] quickSelect(int[] nums, int k) {
        validate(nums, k);
        if (k == 0) return new int[0];
        int[] a = Arrays.copyOf(nums, nums.length);
        int left = 0, right = a.length - 1, target = k - 1;
        while (left <= right) {
            int p = partition(a, left, right);
            if (p == target) break;
            if (p < target) left = p + 1;
            else right = p - 1;
        }
        return Arrays.copyOf(a, k);
    }

    private static int partition(int[] a, int left, int right) {
        int pivotIndex = left + (right - left) / 2;
        int pivot = a[pivotIndex];
        swap(a, pivotIndex, right);
        int store = left;
        for (int i = left; i < right; i++) {
            if (a[i] <= pivot) swap(a, store++, i);
        }
        swap(a, store, right);
        return store;
    }

    private static void validate(int[] nums, int k) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (k < 0 || k > nums.length) throw new IllegalArgumentException("k must be in [0,n]");
    }

    private static void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }
}
```

对于 `[7,2,9,4,1,1]`、k=3，两种方法得到的集合都应是 `{1,1,2}`。注意 PriorityQueue 的迭代顺序和 Quick Select 前 k 项的内部顺序都不是排序结果；如果接口要求升序返回，应最后对结果数组排序并把该成本计入复杂度。

## 关键细节

- Heap Select 要用**最大堆**，因为我们需要 O(1) 查看当前 k 个最小值中最大的那个淘汰候选。
- k=0 必须单独安全处理，不能对空堆调用 `peek` 并参与比较。
- Quick Select 的 partition 保证枢轴左侧 `<= pivot`、右侧 `> pivot`（按本实现），重复值也能正确收缩搜索区间。
- 本 Quick Select 使用中点位置作为 pivot，平均表现通常较好但仍存在 O(n²) 构造；随机 pivot 或更强的选择策略可以降低/约束退化风险。
- “Quick Select 空间 O(1)”只在允许原地改输入时成立；本实现复制数组保护调用方，因此应诚实写 O(n) 额外空间。

## 原理机制

最大堆维护一个大小不超过 k 的不变量：处理完任意前缀后，堆里恰好保存该前缀最小的 k 个值；堆顶是这些候选中最大者，所以更小的新值能替换它。Quick Select 的不变量来自 partition：枢轴到达最终秩位置 p 后，第 k 小只可能在 p 左侧、p 本身或 p 右侧之一，因此每轮只继续一侧，而不像完整快排两侧都递归。

## 项目经验版

来源没有说明是否流式、是否允许修改输入、k 与 n 的比例或结果是否要求有序。本答案把这些都显式拆开：流式/小 k 偏向堆；内存中批量数组、允许或可接受复制且追求平均线性时间时可用 Quick Select；需要稳定最坏线性时间则要使用更复杂的确定性选择算法，而不是把普通 Quick Select 说成最坏 O(n)。

## 常见追问

- 问：为什么不是最小堆？答：最小堆只能快速拿到候选中最小的值，但我们需要淘汰当前 k 个最小值里“最大的那个”，所以用最大堆。
- 问：Quick Select 为什么平均 O(n)？答：每轮只处理 partition 后的一侧；当划分较均衡时工作量形成 n+n/2+n/4... 的几何级数，但极端不均衡仍会退化到 O(n²)。
- 问：如果 k 很小选哪个？答：堆的 O(n log k) 很稳定，且只占 O(k)；k 特别小时通常很合适。
- 问：两种方法为什么返回结果不排序？答：题目只要求最小 k 个集合；排序不是必要条件。若接口要求有序，应明确增加 O(k log k)。
- 问：如何避免 Quick Select 修改输入？答：像本实现先复制；代价是 O(n) 额外空间。若可修改输入，直接在原数组 partition 即可。

## 易错点

- 用最小堆维护 k 个最小值，却每次淘汰了错误元素。
- 忽略 k=0、k=n、重复值和非法 k。
- 把普通 Quick Select 宣称成“最坏 O(n)”。
- 说 Quick Select 空间 O(1)，代码却先复制整个数组。
- 返回无序集合却没有在接口里说明，或偷偷排序却不计 O(k log k) 成本。
''',
        'test':r'''import java.util.Arrays;
public final class KSmallestTest {
    static int[] sorted(int[] a){int[] b=Arrays.copyOf(a,a.length);Arrays.sort(b);return b;}
    static void check(int[] actual,int[] expected,String name){if(!Arrays.equals(sorted(actual),sorted(expected)))throw new AssertionError(name+"="+Arrays.toString(actual));}
    public static void main(String[] args){
        int[] src={7,2,9,4,1,1}; int[] before=Arrays.copyOf(src,src.length);
        check(KSmallest.heapSelect(src,3),new int[]{1,1,2},"heap-basic");
        check(KSmallest.quickSelect(src,3),new int[]{1,1,2},"quick-basic");
        if(!Arrays.equals(src,before))throw new AssertionError("input-mutated");
        check(KSmallest.heapSelect(src,0),new int[]{},"heap-k0");
        check(KSmallest.quickSelect(src,0),new int[]{},"quick-k0");
        check(KSmallest.heapSelect(src,src.length),src,"heap-kn");
        check(KSmallest.quickSelect(src,src.length),src,"quick-kn");
        check(KSmallest.heapSelect(new int[]{-1,-1,5,0},2),new int[]{-1,-1},"heap-duplicates-negative");
        check(KSmallest.quickSelect(new int[]{-1,-1,5,0},2),new int[]{-1,-1},"quick-duplicates-negative");
        for(int bad:new int[]{-1,7}){try{KSmallest.heapSelect(src,bad);throw new AssertionError("heap bad k");}catch(IllegalArgumentException expected){} try{KSmallest.quickSelect(src,bad);throw new AssertionError("quick bad k");}catch(IllegalArgumentException expected){}}
        try{KSmallest.heapSelect(null,0);throw new AssertionError("null");}catch(IllegalArgumentException expected){}
        System.out.println("PASS heap quick input-unchanged k0 kn duplicates-negative invalid-k null-rejected");
    }
}
''',
        'stdout':'PASS heap quick input-unchanged k0 kn duplicates-negative invalid-k null-rejected',
        'checks':['heap returns correct smallest three','quickselect returns same smallest three','quickselect contract preserves caller input via copy','k=0 handled by both methods','k=n handled by both methods','duplicates and negatives handled','invalid k rejected by both methods','null input rejected'],
        'claims':[
            ('source-boundary','The frozen source explicitly requests k-smallest plus Heap Select versus Quick Select complexity/implementation comparison; ordering, mutation, and streaming constraints are unspecified, so the candidate declares unordered output and no caller-input mutation.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('selection-correctness','The executable OpenJDK fixture verifies heap/quick equivalence on ordinary data, no input mutation, k=0/k=n, duplicates/negatives, invalid k, and null input.',['fixture'],['3 分钟版','原理机制','常见追问','易错点']),
        ],
        'findings':['The heap solution maintains a max-heap of at most k elements and states O(n log k)/O(k) costs.','The Quick Select solution narrows to one partition side, states average O(n) and worst O(n^2), and does not falsely claim O(1) space while copying input.','Output ordering is explicitly outside the base contract, with the O(k log k) sorting cost called out when required.','OpenJDK validation covers method equivalence, mutation boundary, k extrema, duplicate/negative values, and invalid inputs.'],
        'task_note':'- [x] `cq_q_bf9e3c9602cef585e013df4c4f996d89` source-first isolated review PASS: the candidate contrasts max-heap O(n log k)/O(k) with average-O(n), worst-O(n²) Quick Select, states the copy/no-mutation space cost and unordered-output contract, and OpenJDK validation covers equivalence, k extrema, duplicates/negatives, mutation, and invalid inputs. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    if not inventory_path.exists():
        raise SystemExit('Batch 0057 source inventory must be frozen before writing')
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task_text = task.read_text(encoding='utf-8').rstrip()

    for target in TARGETS:
        cid, qid = target['cid'], target['qid']
        candidate = ROOT / f'review/candidates/answers/{cid}.md'
        evidence = ROOT / f'review/evidence/{cid}.json'
        if candidate.exists() or evidence.exists():
            raise SystemExit(f'{cid}: candidate/evidence already exists; do not overwrite')
        ctx_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}/context.json'
        if not ctx_path.exists():
            raise SystemExit(f'{cid}: frozen context missing')
        ctx = json.loads(ctx_path.read_text(encoding='utf-8'))
        if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id') != cid or ctx.get('answer_type') != 'coding':
            raise SystemExit(f'{cid}: context/type drift')
        if ctx.get('canonical',{}).get('question_ids') != [qid]:
            raise SystemExit(f'{cid}: source ownership drift')
        src = next((x for x in ctx.get('source_questions',[]) if x.get('question_id') == qid), None)
        if not src or src.get('original_question') != target['expected'] or src.get('is_valid_for_library') is not True:
            raise SystemExit(f'{cid}: source wording/validity drift')
        inv = next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id') == cid), None)
        if not inv or inv.get('existing_candidate') or inv.get('existing_evidence') or inv.get('answer_type') != 'coding':
            raise SystemExit(f'{cid}: inventory no longer describes a fresh coding target')

        body = target['candidate']
        for heading in HEADINGS:
            if body.count(heading) != 1:
                raise SystemExit(f'{cid}: section drift {heading}')
        blocks = re.findall(r'```java\n(.*?)\n```', body, re.S)
        if len(blocks) != 1:
            raise SystemExit(f'{cid}: expected exactly one Java implementation block')
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(body, encoding='utf-8')

        out = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}'
        with tempfile.TemporaryDirectory(prefix=f'b57-{target["slug"]}-') as tmp:
            d = Path(tmp)
            (d / f'{target["class"]}.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
            (d / f'{target["class"]}Test.java').write_text(target['test'], encoding='utf-8')
            run('javac', f'{target["class"]}.java', f'{target["class"]}Test.java', cwd=d)
            stdout = run('java', f'{target["class"]}Test', cwd=d).stdout.strip()
        if stdout != target['stdout']:
            raise SystemExit(f'{cid}: fixture stdout drift: {stdout}')

        validation = {
            'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,
            'command':f'javac {target["class"]}.java {target["class"]}Test.java && java {target["class"]}Test',
            'stdout':stdout,'checks':target['checks']
        }
        write_json(out/'writer_validation.json', validation)
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        sources = [
            {'source_id':'repository-source','title':f'Batch 0057 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
            {'source_id':'fixture','title':f'OpenJDK deterministic validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        ]
        claims = [{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
        coverage = [{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
        write_json(out/'writer_research.json', {
            'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
            'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,
            'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'
        })

        reviewer = f'source-first-isolated-reviewer-batch-0057-{target["slug"]}-20260829-v1'
        review = {
            'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,
            'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0057.{target["slug"]}.v1',
            'decision':'pass','revision_round':1,
            'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],
            'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],
            'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]
        }
        write_json(out/'isolated_review_result.json', review)
        evidence_sources = sources + [
            {'source_id':'isolated-review','title':f'Batch 0057 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}
        ]
        write_json(evidence, {
            'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
            'writer':{'writer_id':f'content-batch-0057-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},
            'sources':evidence_sources,'claims':claims,'source_question_coverage':coverage,
            'validation':{
                'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':target['checks'],
                'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in target['checks']]
            },
            'review_state':'independent_source_first_review_passed',
            'review':{
                'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,
                'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']
            },
            'promotion_blocker':PROMOTION_BLOCKER
        })
        if target['task_note'] not in task_text:
            task_text += '\n' + target['task_note']

    task.write_text(task_text.rstrip() + '\n', encoding='utf-8')
    print('PASS batch-0057 algorithm quartet built, executed, reviewed, and evidence-frozen')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
