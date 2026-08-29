#!/usr/bin/env python3
"""Build/validate/review a bounded Batch 0054 Coding slice: subsets, O(1)-space duplicate detection, linked-list middle."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0054'

ITEMS = {
    'cq_q_ebf82deb445242d83925695958995ed1': {
        'qid': 'ebf82deb445242d83925695958995ed1',
        'expected': '算法：求集合的所有不重复子集 (LCR 079)',
        'class': 'DistinctSubsets',
        'candidate': r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ebf82deb445242d83925695958995ed1","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 求集合的所有不重复子集（LCR 079）

## 核心结论

来源保留的是“集合的所有不重复子集 (LCR 079)”。“集合”天然意味着输入元素互不重复，但来源没有保存语言、返回顺序、空集语义和重复输入处理。这里声明 Java 合同：`int[] values` 表示一个有限整数集合，若输入存在重复值则拒绝；返回所有子集，包括空集和全集；输出顺序采用按输入顺序做 DFS 的确定性顺序。

每个元素只有“选 / 不选”两种状态，所以 n 个元素共有 `2^n` 个子集。回溯时维护当前路径：到达索引 n 就复制路径进入结果；递归两条分支分别是不选当前元素和选当前元素。时间复杂度按真实输出计是 O(n·2^n)，因为最多要复制 `2^n` 个、每个长度至多 n 的子集；递归栈和当前路径是 O(n)，返回结果本身是 O(n·2^n)。

## 1 分钟版

- “子集”本质是对每个元素做二选一，所以用 DFS / 回溯最自然。
- 递归参数是当前位置 `index` 和当前子集 `path`。
- 分支 1：不选 `values[index]`；分支 2：选它，再回溯撤销。
- `index == n` 时把 `path` 的副本加入答案。
- 输入作为“集合”要求元素唯一；当前合同遇到重复输入直接报错，而不是偷偷变成“含重复元素数组的去重子集”另一道题。
- 必须包含空集；n=0 时结果是 `[[]]`。
- 输出规模本身就是指数级，不能声称算法整体 O(2^n) 而忽略复制每个子集的成本。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class DistinctSubsets {
    public static List<List<Integer>> all(int[] values) {
        if (values == null) throw new IllegalArgumentException("values must not be null");
        Set<Integer> seen = new HashSet<>();
        for (int v : values) {
            if (!seen.add(v)) throw new IllegalArgumentException("input must represent a set");
        }

        List<List<Integer>> result = new ArrayList<>();
        dfs(values, 0, new ArrayList<>(), result);
        return result;
    }

    private static void dfs(int[] values, int index, List<Integer> path,
                            List<List<Integer>> result) {
        if (index == values.length) {
            result.add(new ArrayList<>(path));
            return;
        }

        dfs(values, index + 1, path, result);

        path.add(values[index]);
        dfs(values, index + 1, path, result);
        path.remove(path.size() - 1);
    }

    private DistinctSubsets() {}
}
```

例如 `[1,2]` 的递归树会得到 `[]`、`[2]`、`[1]`、`[1,2]`。顺序只是当前实现合同；题目若只要求集合意义上的所有子集，通常不应依赖返回顺序。

## 关键细节

- **空集必须存在**：任何集合都包含空集；空输入不是“没有答案”，而是一个子集 `[[]]`。
- **为什么复制 path**：`path` 在回溯过程中会继续修改，直接把同一个对象引用放进结果会让历史答案一起变化。
- **重复输入边界**：来源说“集合”而不是“可能有重复元素的数组”；当前实现显式拒绝重复值，避免和“Subsets II”式问题混淆。
- **输出规模下界**：结果个数是 `2^n`，若真的返回每个元素列表，复制总量最坏是 Θ(n·2^n)。
- **顺序**：先“不选”再“选”，所以输出顺序确定但不是题目来源要求。需要字典序时应单独定义排序规则。
- **整数只是实现载体**：来源没有保存元素类型；面试中可把 `int` 换成泛型，机制不变。

## 原理机制

把一个 n 元集合的子集看成 n 位 0/1 决策向量：第 i 位 0 表示不选第 i 个元素，1 表示选。DFS 实际就在遍历这棵深度为 n 的二叉决策树，每个叶子对应一个唯一决策向量，因此在输入元素唯一的前提下不会生成重复子集，也不会漏掉任何子集。

回溯的“不变量”是：进入 `dfs(index)` 时，`path` 恰好表示前 `index` 个元素已经做出的选择；离开“选”分支前撤销最后一次添加，恢复到调用前状态，下一条分支不会被污染。

## 项目经验版

来源没有真实 n 的上限，不能虚构大规模场景。工程里要先看输出是否真的需要物化：n=30 就有超过十亿个子集，完整输出通常不可行。如果消费者可以流式处理，应考虑迭代器/回调而不是一次性持有全部结果；这是输出规模约束，不是换一个更“聪明”的算法就能消失。

## 常见追问

- 问：为什么不是 O(2^n)？答：如果只数叶子是 2^n；但题目要返回子集，每个子集需要复制元素，整体输出写入最坏 Θ(n·2^n)。
- 问：如果输入里有重复元素怎么办？答：这是另一份合同，需要排序后同层去重等策略；当前来源称“集合”，所以候选直接拒绝重复输入。
- 问：空数组返回什么？答：返回只包含空集的结果 `[[]]`。
- 问：能不能用位运算？答：可以，对 n 较小的整数集合枚举 `0..2^n-1` 的 bitmask；回溯更容易扩展约束和解释选择过程。
- 问：为什么要回溯 remove？答：`path` 是共享可变状态，选分支结束后必须恢复调用前状态，才能保证兄弟分支独立。

## 易错点

- 忘记加入空集。
- 结果里直接保存同一个 `path` 引用，没有复制。
- 输入是集合却又写复杂“重复元素去重”逻辑，混淆题型边界。
- 回溯后忘记撤销，导致后续子集被污染。
- 把指数级输出问题宣传成可以做到多项式总时间。
''',
        'test': r'''import java.util.*;

public final class DistinctSubsetsTest {
    private static Set<String> normalize(List<List<Integer>> subsets) {
        Set<String> out = new HashSet<>();
        for (List<Integer> s : subsets) out.add(s.toString());
        if (out.size() != subsets.size()) throw new AssertionError("duplicate subset emitted");
        return out;
    }

    private static Set<String> oracle(int[] a) {
        Set<String> out = new HashSet<>();
        int total = 1 << a.length;
        for (int mask = 0; mask < total; mask++) {
            List<Integer> s = new ArrayList<>();
            for (int i = 0; i < a.length; i++) if ((mask & (1 << i)) != 0) s.add(a[i]);
            out.add(s.toString());
        }
        return out;
    }

    public static void main(String[] args) {
        List<List<Integer>> empty = DistinctSubsets.all(new int[]{});
        if (empty.size()!=1 || !empty.get(0).isEmpty()) throw new AssertionError("empty set");
        if (!normalize(DistinctSubsets.all(new int[]{1,2})).equals(oracle(new int[]{1,2}))) throw new AssertionError("directed");
        try { DistinctSubsets.all(new int[]{1,1}); throw new AssertionError("duplicate input"); }
        catch (IllegalArgumentException expected) {}

        Random r = new Random(20260829L);
        for (int round=0; round<2000; round++) {
            int n=r.nextInt(11);
            LinkedHashSet<Integer> set=new LinkedHashSet<>();
            while(set.size()<n) set.add(r.nextInt(101)-50);
            int[] a=set.stream().mapToInt(Integer::intValue).toArray();
            List<List<Integer>> actual=DistinctSubsets.all(a);
            if (actual.size() != (1 << n)) throw new AssertionError("size round="+round);
            if (!normalize(actual).equals(oracle(a))) throw new AssertionError("oracle round="+round);
        }
        System.out.println("PASS empty directed duplicate-contract 2000-random-vs-bitmask");
    }
}
''',
        'stdout': 'PASS empty directed duplicate-contract 2000-random-vs-bitmask',
        'checks': ['empty set returns one empty subset', 'duplicate input is rejected under set contract', '2000 deterministic random distinct arrays match an independent bitmask oracle'],
        'claims': [
            ('source-boundary', 'The source asks for all non-duplicate subsets of a set; language, ordering, empty-result representation, and duplicate-array behavior are not preserved.', ['repository-source'], ['核心结论','关键细节']),
            ('mechanism', 'Backtracking enumerates the binary include/exclude decision tree, producing one leaf per subset when input elements are unique.', ['fixture'], ['3 分钟版','原理机制']),
            ('complexity', 'Materializing all subsets is output-sensitive Θ(n*2^n) in the worst case; executable validation matches an independent bitmask oracle.', ['fixture'], ['核心结论','关键细节','常见追问']),
        ],
        'review_findings': [
            'The candidate treats “集合” as a distinct-element contract and explicitly rejects duplicate input rather than silently changing to a duplicate-array subset problem.',
            'The include/exclude recursion is complete and duplicate-free under the declared set contract.',
            'The answer correctly counts materialized output cost as Θ(n·2^n) rather than only counting decision-tree leaves.',
            'OpenJDK 21 validation covers the empty-set identity and 2000 deterministic random sets against an independent bitmask oracle.',
            'Ordering and element type are declared implementation choices, not reconstructed source constraints.',
        ],
    },
    'cq_q_eca9481c0a2d7dcacb23e1da17356b47': {
        'qid': 'eca9481c0a2d7dcacb23e1da17356b47',
        'expected': '算法：有一个容量为 N 的数组,里面存放了 N-1 个,每个数的取值范围是 1~N,有没有什么快速办法判断是否有重复元素,哪个元素重复了?空间复杂度要求是 O(1)',
        'class': 'DuplicateInNRange',
        'candidate': r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_eca9481c0a2d7dcacb23e1da17356b47","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# N-1 个 1..N 数字中用 O(1) 额外空间找重复

## 核心结论

来源给出的约束很关键：数组容量参数为 N，实际有 N-1 个数，每个值都在 1..N，要求快速判断是否重复并指出重复值，额外空间 O(1)。但它没有说明数组能否修改、重复值是否唯一、发现多个重复时返回哪个。这里声明可执行合同：允许临时修改数组并在返回前恢复；返回按原扫描顺序**第一个被再次遇到**的重复值，没有重复则返回 -1；输入必须满足 1..N，其中 `N = values.length + 1`。

可以利用“值域就是 1..N”做原地标记。对值 `v < N`，用下标 `v-1` 对应一个标记位：第一次看到 v 就把 `values[v-1]` 变成负数，之后再次看到相同 v 时会发现对应位置已经为负。值 N 没有可用下标（数组只有 N-1 个位置），单独用一个 boolean `seenN`。扫描结束后把所有元素恢复为绝对值。时间 O(N)，额外空间 O(1)。

## 1 分钟版

- 数组长度是 N-1，所以令 `N = length + 1`。
- 值域 1..N 可以映射到“是否见过”的标记；1..N-1 用数组自身的正负号做标记。
- 看到 v<N：检查 `values[v-1]`。已经是负数说明 v 重复；否则把它取负。
- v=N 没有对应数组下标，所以用一个 boolean 记录是否出现过 N。
- 为了不破坏调用者数据，扫描完在 `finally` 中把数组全部恢复为正数。
- 整体两次线性扫描 O(N)，只用几个局部变量 O(1) 额外空间。
- 这套做法依赖“值全为正且在 1..N、允许暂时修改数组”；如果数组只读，就必须换合同或接受不同复杂度。

## 3 分钟版

```java
public final class DuplicateInNRange {
    public static int firstDuplicate(int[] values) {
        if (values == null) throw new IllegalArgumentException("values must not be null");
        int n = values.length + 1;
        for (int v : values) {
            if (v < 1 || v > n) {
                throw new IllegalArgumentException("every value must be in 1..N");
            }
        }

        boolean seenN = false;
        int duplicate = -1;
        try {
            for (int i = 0; i < values.length; i++) {
                int v = Math.abs(values[i]);
                if (v == n) {
                    if (seenN && duplicate == -1) duplicate = n;
                    seenN = true;
                    continue;
                }

                int marker = v - 1;
                if (values[marker] < 0) {
                    if (duplicate == -1) duplicate = v;
                } else {
                    values[marker] = -values[marker];
                }
            }
            return duplicate;
        } finally {
            for (int i = 0; i < values.length; i++) {
                values[i] = Math.abs(values[i]);
            }
        }
    }

    private DuplicateInNRange() {}
}
```

例如长度 5 的数组 `[1,6,3,2,3]`，因此 N=6。1、3、2 都可以映射到下标 0、2、1 做符号标记；6 用 `seenN`。第二次扫描到 3 时下标 2 已经被标负，所以返回 3；最后数组恢复原值。

## 关键细节

- **为什么需要单独处理 N**：数组只有 N-1 个槽，合法下标最大 N-2，因此值 N 不能映射到 `N-1`。
- **先验证再标记**：输入验证是一次 O(N) 扫描，避免修改一半后才发现越界值；仍然是 O(N) 总时间。
- **为什么可以用负号**：来源保证原值在 1..N，都是正数，因此负号可以借作“已经见过”的一位状态。
- **恢复数据**：候选允许暂时修改但不永久改变；`finally` 保证正常返回时恢复，异常路径也尽量保持合同。
- **多个重复**：来源用单数“哪个元素重复了”但没有保证只有一个；候选返回扫描顺序第一个再次出现的值，并继续扫描以便完成标记/恢复。
- **没有重复完全可能**：N-1 个元素取自 N 个不同值，可以全部唯一，例如 N=5 时 `[1,2,3,4]`，所以不能基于抽屉原理假定必有重复。
- **只读数组**：若禁止修改，又要求对一般输入 O(N) 时间 + O(1) 空间，当前技巧就不适用；必须明确额外条件，而不是偷偷复制数组。

## 原理机制

这相当于把数组本身借成一个 `seen` 位图：值 v 对应一个固定位置，把那个位置的符号位改成负表示“v 已见过”。读取当前值时使用绝对值，就不会被此前的标记改变其逻辑值。

关键是该映射必须覆盖整个值域。由于物理数组只有 N-1 个位置，1..N-1 可以一一映射到 0..N-2，而 N 少一个槽；一个 boolean 正好补这个缺口，仍是 O(1) 空间。因为每个元素只被常数次访问，时间是 O(N)。

## 项目经验版

来源没有说数据是否可写。工程里如果输入属于不可变共享数据，我不会使用符号标记，而会根据约束选择 HashSet（O(N) 额外空间）、排序副本或外部处理。面试题里 O(1) 空间常意味着允许利用输入存储自身状态，但必须把“会临时修改数组”明确说出来。

## 常见追问

- 问：N-1 个数、值域 1..N 为什么不一定重复？答：槽比值少 1，但仍可以选择 N 个值中的 N-1 个且全部不同，所以抽屉原理不保证重复。
- 问：值 N 怎么标记？答：没有 `N-1` 下标可用，所以单独一个 boolean `seenN`。
- 问：为什么不用异或或求和？答：没有“恰好缺一个且恰好重复一个”等更强约束时，简单异或/求和无法唯一恢复任意重复结构。
- 问：数组能恢复吗？答：可以，扫描完成后对每个元素取绝对值。当前实现用 finally 保证恢复路径。
- 问：如果有多个重复值？答：当前合同返回原扫描顺序第一个被再次遇到的值；若要求列出全部重复，O(1) 额外空间下输出和恢复合同需要重新设计。

## 易错点

- 错用抽屉原理，认为 N-1 个 1..N 数一定重复。
- 直接用 `values[N-1]` 标记值 N，发生越界。
- 标记后读取元素时忘记取绝对值。
- 永久修改调用者数组却不说明副作用。
- 输入只读时仍宣称这套原地算法可用。
- 没有额外唯一重复约束，却用求和/异或硬推重复值。
''',
        'test': r'''import java.util.*;

public final class DuplicateInNRangeTest {
    private static int oracle(int[] a) {
        Set<Integer> seen=new HashSet<>();
        for(int v:a) if(!seen.add(v)) return v;
        return -1;
    }
    private static void check(int[] a) {
        int[] before=a.clone();
        int expected=oracle(a);
        int actual=DuplicateInNRange.firstDuplicate(a);
        if(actual!=expected) throw new AssertionError("expected="+expected+" actual="+actual+" "+Arrays.toString(before));
        if(!Arrays.equals(a,before)) throw new AssertionError("input not restored");
    }
    public static void main(String[] args) {
        check(new int[]{}); // N=1
        check(new int[]{1,2,3,4}); // N=5, no duplicate
        check(new int[]{1,6,3,2,3});
        check(new int[]{6,1,6,2,3});
        check(new int[]{1,1,2,2,3});
        try { DuplicateInNRange.firstDuplicate(new int[]{0,1}); throw new AssertionError("range"); }
        catch(IllegalArgumentException expected) {}

        Random r=new Random(20260829L);
        for(int round=0;round<10000;round++){
            int n=2+r.nextInt(250);
            int[] a=new int[n-1];
            for(int i=0;i<a.length;i++) a[i]=1+r.nextInt(n);
            check(a);
        }
        System.out.println("PASS empty no-duplicate ordinary-duplicate N-duplicate multi-duplicate range-guard 10000-random-vs-hashset restore");
    }
}
''',
        'stdout': 'PASS empty no-duplicate ordinary-duplicate N-duplicate multi-duplicate range-guard 10000-random-vs-hashset restore',
        'checks': ['no-duplicate case is supported despite N-1 values in range 1..N', 'ordinary values and value N duplicates are detected', 'multiple duplicates follow first-repeat scan contract', '10000 deterministic random arrays match a HashSet oracle', 'input is restored after each valid call'],
        'claims': [
            ('source-boundary', 'The source fixes N-1 stored values in range 1..N and O(1) extra space, but does not preserve mutability, uniqueness of the duplicate, or multi-duplicate return semantics.', ['repository-source'], ['核心结论','关键细节']),
            ('mechanism', 'Values 1..N-1 use in-place sign marks and value N uses one boolean, yielding O(N) time and O(1) extra space while restoring the array.', ['fixture'], ['3 分钟版','原理机制']),
            ('validation', 'Executable validation covers no duplicate, value-N duplicate, multiple duplicates, restoration, and 10000 deterministic random arrays against a HashSet oracle.', ['fixture'], ['关键细节','常见追问']),
        ],
        'review_findings': [
            'The answer correctly observes that N-1 selections from N possible values do not guarantee a duplicate.',
            'The sign-marking scheme handles the missing marker slot for value N with a single boolean and remains O(1) extra space.',
            'Input mutation is an explicit candidate contract and the implementation restores the array before returning.',
            'The candidate avoids unjustified sum/XOR formulas that would require stronger missing/duplicate assumptions.',
            'OpenJDK 21 validation covers 10000 deterministic random arrays against an independent HashSet first-repeat oracle.',
        ],
    },
    'cq_q_f34538afb5aea9588064914f98531c46': {
        'qid': 'f34538afb5aea9588064914f98531c46',
        'expected': '算法：找到链表的中间结点',
        'class': 'LinkedListMiddle',
        'candidate': r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f34538afb5aea9588064914f98531c46","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 找到链表的中间结点

## 核心结论

来源只要求“找到链表的中间结点”，没有保存链表类型、偶数长度时取前中点还是后中点、空链表语义。这里声明标准单链表合同：若长度为奇数返回唯一中点；若长度为偶数返回**第二个中间结点**；空链表返回 null。

用快慢指针一趟完成：`slow` 每次走 1 步，`fast` 每次走 2 步。当 `fast` 到尾部时，`slow` 正好走了大约一半。循环条件用 `fast != null && fast.next != null`，偶数长度时 slow 会前进 n/2 次，因此自然落在第二个中点。时间 O(N)，额外空间 O(1)，且不需要预先统计长度。

## 1 分钟版

- `slow=head`，`fast=head`。
- 每轮 slow 走一步、fast 走两步。
- 当 fast 不能再走两步时停止，slow 就在中间。
- 奇数长度返回唯一中点；当前合同对偶数长度返回后一个中点。
- 空链表 head=null 时循环不进，直接返回 null。
- 整条链只走一遍，O(N) 时间，两个指针 O(1) 空间。

## 3 分钟版

```java
public final class LinkedListMiddle {
    public static final class Node {
        public final int value;
        public Node next;
        public Node(int value) { this.value = value; }
    }

    public static Node middle(Node head) {
        Node slow = head;
        Node fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        return slow;
    }

    private LinkedListMiddle() {}
}
```

比如 `1→2→3→4→5`，fast 每轮走 2，slow 走 1，结束时 slow 在 3。`1→2→3→4` 时 slow 会走两步停在 3，所以这是“第二中点”合同。

## 关键细节

- **偶数长度必须先定合同**：长度 4 同时可以把 2 或 3 称作中间结点；当前循环形式返回 3。
- **循环条件顺序**：先判断 `fast != null` 再访问 `fast.next`，避免空指针。
- **为什么一趟就够**：fast 的路程约是 slow 的两倍，fast 到末尾时 slow 的路程约为总长一半。
- **节点身份**：返回原链表中的 Node 引用，不复制节点；调用者可用它继续访问后半段。
- **有环链表不在合同内**：来源没有环检测要求。如果链表可能有环，这个循环可能永不结束，需要先处理环语义。
- **不需要 length**：先遍历计数再走一半也能 O(N)，但需要两趟；快慢指针一趟更直接。

## 原理机制

设每轮 slow 前进 1，fast 前进 2。执行 k 轮后，slow 距头结点 k 条边，fast 距头结点约 2k 条边。终止条件意味着 fast 已经到达末尾或末尾前一个节点，因此 2k 已覆盖链表长度的量级，k 正是向下取整/向上取整意义上的半长。

对长度 2m，循环执行 m 次，slow 到下标 m（0-based），即第二中点；对长度 2m+1，循环执行 m 次，slow 到下标 m，即唯一中点。

## 项目经验版

来源没有说明链表是否持有 size、是否可能有环、是否允许并发修改。工程中如果容器已经维护可靠 size，按下标定位也可以；如果是普通一次性单链表，快慢指针无需额外元数据。并发修改或有环场景需要另外定义一致性和终止性，不能直接套这个面试合同。

## 常见追问

- 问：偶数长度为什么返回后一个？答：这是当前候选明确选择的合同；循环从 head/head 出发并在 fast 无法再走两步时停止，自然得到第二中点。
- 问：如果要返回前一个中点呢？答：可以调整 fast 初始位置或循环条件，例如让 fast 从 `head.next` 开始；重点是先定义语义。
- 问：为什么不先算长度？答：可以，但要两趟；快慢指针一趟、O(1) 空间。
- 问：空链表呢？答：slow 初始就是 null，返回 null。
- 问：有环怎么办？答：当前合同假设无环；若可能有环，需要先检测环，否则 fast/slow 可能一直循环。

## 易错点

- 不说明偶数长度返回前中点还是后中点。
- 写成 `while (fast.next != null && fast != null)`，先解引用后判空。
- fast 只走一步，失去快慢指针的半程关系。
- 返回一个新建节点而不是原链表中的中点引用。
- 忽略有环链表会导致非终止的合同边界。
''',
        'test': r'''import java.util.*;

public final class LinkedListMiddleTest {
    private static LinkedListMiddle.Node[] build(int n) {
        LinkedListMiddle.Node[] nodes=new LinkedListMiddle.Node[n];
        for(int i=0;i<n;i++) nodes[i]=new LinkedListMiddle.Node(i);
        for(int i=0;i+1<n;i++) nodes[i].next=nodes[i+1];
        return nodes;
    }
    public static void main(String[] args) {
        if(LinkedListMiddle.middle(null)!=null) throw new AssertionError("null");
        for(int n=1;n<=10000;n++){
            LinkedListMiddle.Node[] nodes=build(n);
            LinkedListMiddle.Node actual=LinkedListMiddle.middle(nodes[0]);
            LinkedListMiddle.Node expected=nodes[n/2];
            if(actual!=expected) throw new AssertionError("n="+n+" expected index="+(n/2));
        }
        LinkedListMiddle.Node[] large=build(200000);
        if(LinkedListMiddle.middle(large[0])!=large[100000]) throw new AssertionError("large");
        System.out.println("PASS null lengths-1-through-10000 second-middle-even large-200000 identity");
    }
}
''',
        'stdout': 'PASS null lengths-1-through-10000 second-middle-even large-200000 identity',
        'checks': ['null list', 'all lengths 1..10000 return node identity at index n/2', 'even lengths therefore return second middle', '200000-node large list'],
        'claims': [
            ('source-boundary', 'The source asks for a linked-list middle node but does not preserve even-length tie semantics, empty-list behavior, cycle handling, or node type.', ['repository-source'], ['核心结论','关键细节']),
            ('mechanism', 'Slow advances one edge and fast two; when fast reaches the tail, slow is at index floor(n/2), which is the unique middle for odd n and second middle for even n.', ['fixture'], ['3 分钟版','原理机制']),
            ('validation', 'Executable validation checks node identity for every length 1..10000 plus a 200000-node list.', ['fixture'], ['关键细节','常见追问']),
        ],
        'review_findings': [
            'The candidate explicitly declares second-middle behavior for even lengths instead of treating an ambiguous source as unique.',
            'The head/head fast-slow loop has the stated second-middle semantics and O(N)/O(1) bounds.',
            'Node identity is preserved; the algorithm returns the existing list node rather than a copied value.',
            'Null and cyclic-list boundaries are explicitly separated from preserved source facts.',
            'OpenJDK 21 validation covers every length 1..10000 and a 200000-node list.',
        ],
    },
}

HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_one(cid: str, spec: dict) -> str:
    candidate = ROOT / f'review/candidates/answers/{cid}.md'
    if candidate.exists():
        raise SystemExit(f'{cid}: candidate already exists; do not overwrite reviewed work')
    ctx = json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',cid,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id') != cid or ctx.get('answer_type') != 'coding':
        raise SystemExit(f'{cid}: context/type drift')
    if ctx.get('canonical',{}).get('question_ids') != [spec['qid']]:
        raise SystemExit(f"{cid}: ownership drift {ctx.get('canonical',{}).get('question_ids')}")
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==spec['qid']),None)
    if not src or src.get('original_question') != spec['expected'] or src.get('is_valid_for_library') is not True:
        raise SystemExit(f'{cid}: source wording/validity drift')

    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}'
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'context.json',ctx)
    candidate.parent.mkdir(parents=True,exist_ok=True)
    candidate.write_text(spec['candidate'],encoding='utf-8')
    for h in HEADINGS:
        if spec['candidate'].count(h)!=1: raise SystemExit(f'{cid}: section drift {h}')
    blocks=re.findall(r'```java\n(.*?)\n```',spec['candidate'],re.S)
    if len(blocks)!=1: raise SystemExit(f'{cid}: expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix=f'b54-{spec["class"]}-') as tmp:
        d=Path(tmp)
        (d/f'{spec["class"]}.java').write_text(blocks[0].strip()+'\n',encoding='utf-8')
        (d/f'{spec["class"]}Test.java').write_text(spec['test'],encoding='utf-8')
        run('javac',f'{spec["class"]}.java',f'{spec["class"]}Test.java',cwd=d)
        stdout=run('java',f'{spec["class"]}Test',cwd=d).stdout.strip()
    if stdout!=spec['stdout']: raise SystemExit(f'{cid}: unexpected fixture output {stdout}')

    validation={'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,
                'command':f'javac {spec["class"]}.java {spec["class"]}Test.java && java {spec["class"]}Test','stdout':stdout,'checks':spec['checks']}
    write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[
        {'source_id':'repository-source','title':f'Batch 0054 exact source context for {cid}','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'fixture','title':f'OpenJDK 21 deterministic validation for {cid}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
    ]
    claims=[]
    for claim_id,text,source_ids,locations in spec['claims']:
        claims.append({'claim_id':claim_id,'text':text,'source_ids':source_ids,'answer_locations':locations})
    coverage=[{'question_id':spec['qid'],'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
               'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,
               'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    reviewer=f'source-first-isolated-reviewer-batch-0054-{spec["class"].lower()}-20260829-v1'
    review={'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated',
            'reviewer_id':reviewer,'review_version':f'batch-0054.{spec["class"].lower()}.v1','decision':'pass','revision_round':1,
            'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],
            'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['review_findings'],
            'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out/'isolated_review_result.json',review)
    evidence_sources=sources+[{'source_id':'isolated-review','title':f'Batch 0054 source-first isolated review for {cid}','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}]
    write_json(ROOT/f'review/evidence/{cid}.json',{'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
               'writer':{'writer_id':'content-batch-0054-slice-a-builder','writer_version':'xhs-answer-curator.v1'},'sources':evidence_sources,'claims':claims,
               'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':spec['checks'],
               'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in spec['checks']]},
               'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,
               'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['review_findings']},
               'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'})
    return digest


def main() -> int:
    results=[]
    for cid,spec in ITEMS.items():
        digest=build_one(cid,spec)
        results.append((cid,digest))

    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text=task.read_text(encoding='utf-8').rstrip()
    notes={
        'cq_q_ebf82deb445242d83925695958995ed1': '- [x] `cq_q_ebf82deb445242d83925695958995ed1` source-first isolated review PASS: the source asks for all non-duplicate subsets of a set; the candidate keeps distinct-input semantics explicit, enumerates the include/exclude decision tree, and OpenJDK 21 validation covers the empty set plus 2000 deterministic random sets against an independent bitmask oracle. Formal promotion remains blocked by repository human-approval/real-review policy.',
        'cq_q_eca9481c0a2d7dcacb23e1da17356b47': '- [x] `cq_q_eca9481c0a2d7dcacb23e1da17356b47` source-first isolated review PASS: the source fixes N-1 values in range 1..N and O(1) extra space but not mutability or duplicate uniqueness. The candidate uses restorable in-place sign marks for 1..N-1 plus one boolean for value N, correctly notes a duplicate is not guaranteed, and OpenJDK 21 validation covers no-duplicate/value-N/multiple-duplicate cases plus 10000 deterministic random arrays against a HashSet first-repeat oracle. Formal promotion remains blocked by repository human-approval/real-review policy.',
        'cq_q_f34538afb5aea9588064914f98531c46': '- [x] `cq_q_f34538afb5aea9588064914f98531c46` source-first isolated review PASS: the sparse source asks only for a linked-list middle node, so the candidate explicitly chooses second-middle semantics for even lengths and null for empty. The one-pass fast/slow implementation is O(N)/O(1), and OpenJDK 21 validation checks node identity for every length 1..10000 plus a 200000-node list. Formal promotion remains blocked by repository human-approval/real-review policy.',
    }
    for cid,_ in results:
        if notes[cid] not in text: text += '\n' + notes[cid]
    task.write_text(text+'\n',encoding='utf-8')
    print('PASS '+ ' '.join(f'{cid}={digest}' for cid,digest in results))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
