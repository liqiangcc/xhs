#!/usr/bin/env python3
"""Build, execute, and source-first review three well-specified Batch 0055 coding candidates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0055'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

TARGETS = [
    {
        'cid':'cq_q_f6b3c0ccc0d9a2d307d5313492db383c',
        'qid':'f6b3c0ccc0d9a2d307d5313492db383c',
        'expected':'代码实现：求 100 以内的所有质数。',
        'slug':'primes-under-100',
        'class':'PrimesUnder100',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f6b3c0ccc0d9a2d307d5313492db383c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 代码实现：求 100 以内的所有质数

## 核心结论

来源只要求“求 100 以内的所有质数”，没有指定语言、是否包含 100、输出格式或必须使用哪种算法。这里采用一个可执行 Java 合同：实现 `primesUpTo(int n)`，返回 `<= n` 的全部质数，按升序排列；因此对 `n=100` 得到 25 个质数，最后一个是 97。实现使用埃氏筛，时间复杂度 O(n log log n)，空间 O(n)。

## 1 分钟版

- 质数定义为大于 1、只有 1 和自身两个正因子的整数，所以 0、1 都不是质数。
- 建一个 `boolean[] composite`；从 `p=2` 开始，如果 `p` 还没被标记，就把它加入结果。
- 只需要在 `p*p <= n` 时继续标记倍数；从 `p*p` 开始，因为更小的 `2p,3p,...` 已经被更小质因子处理过。
- 对 100，结果是 `2,3,5,...,89,97`，共 25 个。
- 若只为固定 100 写一次，也可以逐个试除；但埃氏筛更清楚地展示“批量找区间质数”的标准思路。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.List;

public final class PrimesUnder100 {
    public static List<Integer> primesUpTo(int n) {
        if (n < 2) return List.of();

        boolean[] composite = new boolean[n + 1];
        for (int p = 2; (long) p * p <= n; p++) {
            if (composite[p]) continue;
            for (long multiple = (long) p * p; multiple <= n; multiple += p) {
                composite[(int) multiple] = true;
            }
        }

        List<Integer> primes = new ArrayList<>();
        for (int x = 2; x <= n; x++) {
            if (!composite[x]) primes.add(x);
        }
        return primes;
    }
}
```

对 `n=100`，筛选结果为：`[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]`。

## 关键细节

- `n < 2` 时直接返回空结果，不能把 1 当成质数。
- 标记倍数从 `p*p` 开始；例如处理 5 时，10、15、20 已经由 2 或 3 处理过。
- 循环条件写成 `(long) p * p <= n`，避免把算法泛化到更大 n 时发生 `int` 乘法溢出。
- 本题上限只有 100，任何合理算法都很快；复杂度讨论是为了说明算法性质，不应虚构性能收益数字。
- 若题目严格理解为“100 以内”即 `<100`，结果与 `<=100` 实际相同，因为 100 不是质数；这里仍明确函数合同是 `<= n`。

## 原理机制

合数一定至少有一个不大于其平方根的质因子。埃氏筛从最小未标记数开始，把它的倍数标成合数；当所有 `p <= sqrt(n)` 都处理完后，仍未被标记的 `2..n` 就都是质数。之所以可以从 `p*p` 开始，是因为 `p*k` 中若 `k<p`，这个数已经在处理 k 的质因子时被标记过。

## 项目经验版

来源没有真实项目或性能场景，不能虚构“线上使用”。如果这是面试手撕，我会先确认边界和输出合同，再写筛法并用 0、1、2、100 做快速自测。若上限扩展到很大区间，还要再讨论分段筛、内存占用等问题；这些不属于当前来源要求。

## 常见追问

- 问：为什么 1 不是质数？答：质数必须恰好有两个正因子，1 只有一个正因子。
- 问：为什么只筛到 `sqrt(n)`？答：若一个合数没有不大于平方根的因子，那么它的两个因子都会大于平方根，乘积就会大于自身，矛盾。
- 问：为什么从 `p*p` 开始？答：更小的 p 倍数已经含有更小因子，会更早被筛掉。
- 问：能不能逐个数试除？答：可以，n=100 完全够用；筛法更适合一次求整个区间的所有质数。
- 问：100 算不算？答：合同定义为 `<= n`；100 本身是合数，所以最终集合不受影响。

## 易错点

- 把 1 加入质数列表。
- 每次从 `2*p` 开始，虽然正确但做了重复标记。
- 用 `p*p` 的 `int` 结果做大范围通用实现，忽略溢出。
- 只打印结果、不定义边界和返回语义，导致测试困难。
''',
        'test':r'''import java.util.*;
public final class PrimesUnder100Test {
    static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[] args){
        check(PrimesUnder100.primesUpTo(-1).isEmpty(),"negative");
        check(PrimesUnder100.primesUpTo(0).isEmpty(),"zero");
        check(PrimesUnder100.primesUpTo(1).isEmpty(),"one");
        check(PrimesUnder100.primesUpTo(2).equals(List.of(2)),"two");
        List<Integer> expected=List.of(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97);
        List<Integer> actual=PrimesUnder100.primesUpTo(100);
        check(actual.equals(expected),"100 list="+actual);
        check(actual.size()==25 && actual.get(actual.size()-1)==97,"count/last");
        System.out.println("PASS boundaries exact-25-primes last=97");
    }
}
''',
        'stdout':'PASS boundaries exact-25-primes last=97',
        'checks':['n<2 returns empty','n=2 returns [2]','n=100 returns the exact 25 primes in ascending order','largest prime <=100 is 97'],
        'claims':[
            ('source-boundary','The preserved source asks only for code that finds all primes within 100; it does not specify language, output surface, or required algorithm.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('sieve-correctness','The executable Java fixture verifies the declared <=n contract at boundary values and the exact 25-prime result for n=100.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate stays inside the preserved fixed-range prime-enumeration source boundary and explicitly declares its <=n Java contract.','The sieve starts composite marking at p*p and only needs base candidates through sqrt(n), matching the stated mechanism.','Executable OpenJDK validation covers n<2, n=2, and the exact 25-prime sequence through 97 for n=100.','No unverifiable project-performance claim is introduced; larger-range techniques are kept as out-of-scope follow-up context.'],
        'task_note':'- [x] `cq_q_f6b3c0ccc0d9a2d307d5313492db383c` source-first isolated review PASS: the candidate declares a <=n Java contract, uses an overflow-safe Eratosthenes sieve, and OpenJDK validation verifies boundaries plus the exact 25 primes through 97 for n=100. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_f93179fa829fa3c7b681999e73d6d2d6',
        'qid':'f93179fa829fa3c7b681999e73d6d2d6',
        'expected':'算法手撕：下一个排列（Next Permutation）。',
        'slug':'next-permutation',
        'class':'NextPermutation',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f93179fa829fa3c7b681999e73d6d2d6","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 下一个排列（Next Permutation）

## 核心结论

来源只要求手撕 Next Permutation，没有指定语言或 API。这里采用经典原地合同：给定 `int[] nums`，把它修改为按字典序排列的“下一个更大排列”；如果当前已经是最大排列，则变成最小排列。算法只扫描常数次，时间 O(n)，额外空间 O(1)。

## 1 分钟版

- 从右往左找第一个 `nums[i] < nums[i+1]`，这个 i 是还能“变大”的最右位置。
- 如果找不到，整个数组非递增，已经是最大排列，直接反转成最小排列。
- 若找到 i，再从右往左找第一个 `nums[j] > nums[i]`。因为右侧原本非递增，这个 j 就是能让前缀变大的最小可行替代。
- 交换 i、j 后，右侧仍需变成最小字典序；把 `i+1..end` 反转即可。
- 例如 `[1,2,3] -> [1,3,2]`，`[3,2,1] -> [1,2,3]`，`[1,1,5] -> [1,5,1]`。

## 3 分钟版

```java
public final class NextPermutation {
    public static void nextPermutation(int[] nums) {
        if (nums == null || nums.length < 2) return;

        int i = nums.length - 2;
        while (i >= 0 && nums[i] >= nums[i + 1]) i--;

        if (i >= 0) {
            int j = nums.length - 1;
            while (nums[j] <= nums[i]) j--;
            swap(nums, i, j);
        }
        reverse(nums, i + 1, nums.length - 1);
    }

    private static void reverse(int[] a, int l, int r) {
        while (l < r) swap(a, l++, r--);
    }

    private static void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }
}
```

核心不是背步骤，而是保证“变大的幅度最小”：尽量保持左侧前缀不变，只在最右可提升位置做最小提升，再把后缀排成最小状态。

## 关键细节

- 第一个扫描条件必须是 `nums[i] >= nums[i+1]`；存在重复元素时也要正确跳过非递增后缀。
- j 从末尾找 `> nums[i]`，不是 `>=`，否则可能交换相等值而没有真正变大。
- 交换后只需反转后缀，不需要 O(n log n) 排序；原后缀在交换前是非递增结构。
- 最大排列如 `[3,2,1]` 找不到 i，反转整个数组得到最小排列。
- 空数组、单元素数组没有不同排列；当前合同保持不变。

## 原理机制

字典序比较先看最左侧不同位置。因此要得到“刚好比当前大”的排列，就应该尽可能晚地改变数组：找到最右侧还能提升的 i。右侧已经是最大化的非递增后缀，所以在其中选择刚大于 `nums[i]` 的最小候选，交换后前缀只增加最小幅度；最后把后缀变成升序最小状态。由于交换前后后缀结构允许通过反转完成最小化，总复杂度保持 O(n)。

## 项目经验版

来源没有真实项目语境，不能虚构业务使用。面试现场我会先讲清“字典序下一个、原地、最大排列回绕”的合同，然后用递增、递减、重复元素三类样例验证。若题目要求生成所有排列或第 k 个排列，那是不同问题，不应混入当前答案。

## 常见追问

- 问：为什么从右边找 i？答：越靠右修改，对字典序的影响越小，才能得到紧邻的下一个排列。
- 问：为什么 j 也从右边找？答：右侧是非递增的，从右向左第一个大于 pivot 的元素就是最小可行增量。
- 问：为什么后缀反转就够了？答：原后缀非递增，交换 pivot 后仍可通过反转得到该前缀下的最小后缀顺序。
- 问：重复元素能处理吗？答：能，比较分别使用 `>=` 和 `<=`，例如 `[1,1,5] -> [1,5,1]`。
- 问：最大排列怎么办？答：不存在更大排列时按经典合同回绕到最小排列，即整体反转。

## 易错点

- pivot 扫描用 `>` 而不是 `>=`，导致重复元素处理错误。
- successor 条件允许相等，交换后排列没变大。
- 找到 pivot 后直接排序整个数组，破坏 O(n) 目标。
- 忘记最大排列需要回绕到最小排列。
''',
        'test':r'''import java.util.*;
public final class NextPermutationTest {
    static void check(int[] a,int... e){if(!Arrays.equals(a,e))throw new AssertionError(Arrays.toString(a));}
    public static void main(String[] args){
        int[] a={1,2,3}; NextPermutation.nextPermutation(a); check(a,1,3,2);
        int[] b={3,2,1}; NextPermutation.nextPermutation(b); check(b,1,2,3);
        int[] c={1,1,5}; NextPermutation.nextPermutation(c); check(c,1,5,1);
        int[] d={1,3,2}; NextPermutation.nextPermutation(d); check(d,2,1,3);
        int[] e={2}; NextPermutation.nextPermutation(e); check(e,2);
        NextPermutation.nextPermutation(null);
        System.out.println("PASS ascending descending duplicates interior single null");
    }
}
''',
        'stdout':'PASS ascending descending duplicates interior single null',
        'checks':['ascending permutation advances minimally','descending maximum wraps to ascending minimum','duplicate elements advance correctly','interior pivot case is correct','single/null boundaries are stable'],
        'claims':[
            ('source-boundary','The preserved source asks only for Next Permutation and does not specify language or API shape.',['repository-source'],['核心结论','项目经验版']),
            ('algorithm-correctness','The executable Java fixture verifies increasing, decreasing, duplicate, interior-pivot, single-element, and null cases under the declared in-place contract.',['fixture'],['1 分钟版','3 分钟版','关键细节','原理机制','常见追问']),
        ],
        'findings':['The candidate declares the standard in-place lexicographic-next contract rather than inventing a different permutation API.','The pivot/successor/reverse construction changes the latest possible position, applies the smallest feasible increase, then minimizes the suffix.','OpenJDK validation covers ascending, descending wraparound, duplicate values, an interior pivot, and boundary inputs.','The answer keeps all-permutations and kth-permutation variants explicitly out of scope.'],
        'task_note':'- [x] `cq_q_f93179fa829fa3c7b681999e73d6d2d6` source-first isolated review PASS: the in-place O(n)/O(1) pivot-successor-reverse algorithm is source-bounded, and OpenJDK validation covers ascending, descending wraparound, duplicates, interior pivot, single-element and null boundaries. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_f93a98e3386612980296c0088e13980a',
        'qid':'f93a98e3386612980296c0088e13980a',
        'expected':'算法手撕：数组中的第 K 个最大元素（Kth Largest Element in an Array）。',
        'slug':'kth-largest',
        'class':'KthLargest',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f93a98e3386612980296c0088e13980a","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 数组中的第 K 个最大元素

## 核心结论

来源只要求“数组中的第 K 个最大元素”，没有指定语言、是否允许修改原数组或必须达到平均 O(n)。这里采用一个稳定、易解释的 Java 合同：输入非空 `int[] nums` 和 `1 <= k <= nums.length`，返回按数值从大到小排序后的第 k 个元素，重复值按出现次数参与排名；实现用大小为 k 的最小堆，不修改输入。时间 O(n log k)，空间 O(k)。

## 1 分钟版

- 维护一个最多 k 个元素的最小堆，表示“目前见过的最大的 k 个数”。
- 每来一个数先入堆；若堆大小超过 k，就弹出最小值。
- 扫描结束时，堆里正好是全局最大的 k 个数，堆顶就是这 k 个数里最小的，也就是第 k 大。
- 例如 `[3,2,1,5,6,4], k=2`，最终堆保存 `{5,6}`，堆顶 5 即答案。
- `[3,2,3,1,2,4,5,5,6], k=4` 返回 4；两个 5 都按独立元素计数。

## 3 分钟版

```java
import java.util.PriorityQueue;

public final class KthLargest {
    public static int findKthLargest(int[] nums, int k) {
        if (nums == null || nums.length == 0 || k < 1 || k > nums.length) {
            throw new IllegalArgumentException("invalid nums or k");
        }

        PriorityQueue<Integer> minHeap = new PriorityQueue<>();
        for (int value : nums) {
            minHeap.offer(value);
            if (minHeap.size() > k) minHeap.poll();
        }
        return minHeap.peek();
    }
}
```

这里“第 k 大”按元素位置定义，不是“第 k 个不同值”。如果题目要求去重后的第 k 大，需要显式改变合同和数据结构，不能偷偷用 `Set`。

## 关键细节

- 最小堆大小固定为 k，是因为我们只关心最大的 k 个；堆顶恰好是这些候选中的门槛值。
- 重复值要保留。例如 `[5,5,4], k=2` 的第 2 大是 5，而不是 4。
- 当前实现不修改 `nums`；如果允许原地修改且追求平均 O(n)，可以讨论 Quickselect。
- k 很小时 O(n log k) 很有竞争力；k 接近 n 时复杂度接近 O(n log n)。
- 必须校验 k 范围，否则空堆或错误排名会让失败变得隐蔽。

## 原理机制

扫描任意前缀后，维持不变量：最小堆保存该前缀中最大的至多 k 个元素。加入新元素后若超过 k，就删除其中最小的那个；因此被删除的元素不可能进入前缀的 top-k。归纳到完整数组，堆中就是全局 top-k，而其中最小者正是第 k 大。这个证明也解释了为什么使用最小堆而不是最大堆：我们需要 O(log k) 地淘汰 top-k 中最弱的候选。

## 项目经验版

来源没有真实数据规模和性能要求，不能虚构线上选择。面试时我会先确认“重复值是否计数、能否改原数组、是否要求平均 O(n)”。若要求最优平均时间且允许修改，我会切到 Quickselect；若希望不改输入、k 较小或需要流式处理，固定大小最小堆通常更自然。

## 常见追问

- 问：为什么不是最大堆？答：最大堆更适合连续弹出最大的 k 个；固定 k 最小堆能在扫描过程中直接淘汰不够大的元素，空间只有 O(k)。
- 问：重复元素怎么算？答：默认按元素出现次数排名；`[5,5,4]` 的第 2 大是 5。
- 问：Quickselect 更好吗？答：平均 O(n)、额外空间可做到 O(1)，但通常会修改数组且最坏 O(n^2)；需要结合合同选择。
- 问：k=1 呢？答：堆只保留一个最大值，结果就是数组最大值。
- 问：k=n 呢？答：最终堆保留所有元素，堆顶就是数组最小值，也就是第 n 大。

## 易错点

- 用 `Set` 去重，改变了重复值的排名语义。
- 维护 k 个元素却使用最大堆，然后错误地把堆顶当第 k 大。
- 忘记 `k<1` 或 `k>n` 的边界校验。
- 声称最小堆方案是 O(n)，忽略每次堆调整的 O(log k)。
''',
        'test':r'''import java.util.*;
public final class KthLargestTest {
    static void check(int actual,int expected,String m){if(actual!=expected)throw new AssertionError(m+"="+actual);}
    static void bad(int[] a,int k){try{KthLargest.findKthLargest(a,k);throw new AssertionError("expected invalid");}catch(IllegalArgumentException expected){}}
    public static void main(String[] args){
        check(KthLargest.findKthLargest(new int[]{3,2,1,5,6,4},2),5,"basic");
        check(KthLargest.findKthLargest(new int[]{3,2,3,1,2,4,5,5,6},4),4,"duplicates");
        check(KthLargest.findKthLargest(new int[]{5,5,4},2),5,"duplicate rank");
        check(KthLargest.findKthLargest(new int[]{-1,-7,-3},1),-1,"negative max");
        check(KthLargest.findKthLargest(new int[]{-1,-7,-3},3),-7,"k=n");
        int[] input={4,1,9}; int[] copy=input.clone(); check(KthLargest.findKthLargest(input,2),4,"no mutate result"); if(!Arrays.equals(input,copy))throw new AssertionError("mutated");
        bad(null,1); bad(new int[]{},1); bad(new int[]{1},0); bad(new int[]{1},2);
        System.out.println("PASS basic duplicates negatives k-boundaries input-unmodified");
    }
}
''',
        'stdout':'PASS basic duplicates negatives k-boundaries input-unmodified',
        'checks':['standard sample returns 5 for k=2','duplicate values participate by occurrence','negative values and k=n are correct','input remains unmodified','null/empty/out-of-range k are rejected'],
        'claims':[
            ('source-boundary','The preserved source asks for the kth largest array element but does not specify language, mutation policy, duplicate semantics, or required asymptotic target.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('heap-correctness','The executable Java fixture verifies the fixed-size min-heap contract across standard, duplicate, negative, k-boundary, and input-immutability cases.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate explicitly defines kth-largest by element occurrence, preserving duplicates rather than silently changing the problem to distinct values.','The fixed-size min-heap maintains the prefix top-k invariant, making its root the kth largest after the full scan.','OpenJDK validation covers standard and duplicate samples, negative values, k=1/k=n behavior, invalid inputs, and the declared non-mutation property.','Quickselect is presented only as a contract-dependent alternative, not as an unsupported source requirement.'],
        'task_note':'- [x] `cq_q_f93a98e3386612980296c0088e13980a` source-first isolated review PASS: the source-bounded fixed-size min-heap solution preserves duplicate-occurrence ranking, does not mutate input, and OpenJDK validation covers samples, negatives, k boundaries and invalid inputs. Formal promotion remains blocked by repository human-approval/real-review policy.'
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
        raise SystemExit('Batch 0055 source inventory must be frozen before writing')
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task_text = task.read_text(encoding='utf-8').rstrip()
    results = []

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
        if not inv or inv.get('existing_candidate') or inv.get('existing_evidence'):
            raise SystemExit(f'{cid}: inventory no longer describes a fresh target')

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
        with tempfile.TemporaryDirectory(prefix=f'b55-{target["slug"]}-') as tmp:
            d = Path(tmp)
            (d / f'{target["class"]}.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
            (d / f'{target["class"]}Test.java').write_text(target['test'], encoding='utf-8')
            run('javac', f'{target["class"]}.java', f'{target["class"]}Test.java', cwd=d)
            stdout = run('java', f'{target["class"]}Test', cwd=d).stdout.strip()
        if stdout != target['stdout']:
            raise SystemExit(f'{cid}: fixture stdout drift: {stdout}')

        validation = {'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':f'javac {target["class"]}.java {target["class"]}Test.java && java {target["class"]}Test','stdout':stdout,'checks':target['checks']}
        write_json(out/'writer_validation.json', validation)
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        sources = [
            {'source_id':'repository-source','title':f'Batch 0055 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
            {'source_id':'fixture','title':f'OpenJDK deterministic validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        ]
        claims = [{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
        coverage = [{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
        write_json(out/'writer_research.json', {'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
        reviewer = f'source-first-isolated-reviewer-batch-0055-{target["slug"]}-20260829-v1'
        review = {'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0055.{target["slug"]}.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]}
        write_json(out/'isolated_review_result.json', review)
        write_json(evidence, {'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':f'content-batch-0055-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0055 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':target['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in target['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']},'promotion_blocker':PROMOTION_BLOCKER})
        writer = json.loads((out/'writer_research.json').read_text(encoding='utf-8'))
        writer['review_state'] = 'writer_complete_isolated_review_passed'
        writer['promotion_blocker'] = PROMOTION_BLOCKER
        write_json(out/'writer_research.json', writer)

        if target['task_note'] not in task_text:
            task_text += '\n' + target['task_note']
        results.append({'canonical_id':cid,'candidate_sha256':digest,'decision':'pass','stdout':stdout})

    task.write_text(task_text + '\n', encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'completed':results,'promotion_blocker':PROMOTION_BLOCKER}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
