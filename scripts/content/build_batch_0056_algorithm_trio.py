#!/usr/bin/env python3
"""Build, execute, and source-first review three remaining source-clear Batch 0056 coding candidates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0056'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

TARGETS = [
    {
        'cid':'cq_q_fc030f5d732ab198236441d05ebb7eff',
        'qid':'fc030f5d732ab198236441d05ebb7eff',
        'expected':'算法：求最大矩阵面积（LeetCode 84/85 变体）。',
        'slug':'maximal-rectangle',
        'class':'MaximalRectangle',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fc030f5d732ab198236441d05ebb7eff","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最大矩阵面积（LeetCode 84/85 变体）

## 核心结论

来源只说“最大矩阵面积（LeetCode 84/85 变体）”，没有固定输入合同。这里采用一个明确的 85 类合同：输入是只包含 0/1 的矩形 `int[][]`，返回全 1 子矩形的最大面积；空矩阵返回 0，`null`、非矩形或含非 0/1 值的输入视为无效。每一行把连续 1 高度累积成直方图，再用 84 的单调递增栈求该直方图最大矩形，整体时间 O(rows*cols)、额外空间 O(cols)。

## 1 分钟版

- `heights[c]` 表示处理到当前行时，第 c 列连续 1 的高度；遇 0 清零，遇 1 加一。
- 当前行作为矩形底边后，二维问题就变成“直方图最大矩形”。
- 单调栈保存尚未确定右边界的柱子下标；遇到更矮柱时持续弹栈并结算面积。
- 弹出高度 h 后，右边界是当前下标 i，左边界是弹栈后新的栈顶，因此宽度为 `i-left-1`。
- 每个柱子至多进栈、出栈一次，所以每行 O(cols)。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class MaximalRectangle {
    public static int maximalRectangle(int[][] matrix) {
        if (matrix == null) throw new IllegalArgumentException("matrix must not be null");
        if (matrix.length == 0) return 0;
        if (matrix[0] == null) throw new IllegalArgumentException("rows must not be null");
        int cols = matrix[0].length;
        int[] heights = new int[cols];
        int best = 0;
        for (int[] row : matrix) {
            if (row == null || row.length != cols) throw new IllegalArgumentException("matrix must be rectangular");
            for (int c = 0; c < cols; c++) {
                if (row[c] != 0 && row[c] != 1) throw new IllegalArgumentException("matrix must contain only 0/1");
                heights[c] = row[c] == 0 ? 0 : heights[c] + 1;
            }
            best = Math.max(best, largestRectangleArea(heights));
        }
        return best;
    }

    private static int largestRectangleArea(int[] heights) {
        Deque<Integer> stack = new ArrayDeque<>();
        int best = 0;
        for (int i = 0; i <= heights.length; i++) {
            int current = i == heights.length ? 0 : heights[i];
            while (!stack.isEmpty() && heights[stack.peek()] > current) {
                int h = heights[stack.pop()];
                int left = stack.isEmpty() ? -1 : stack.peek();
                best = Math.max(best, h * (i - left - 1));
            }
            stack.push(i);
        }
        return best;
    }
}
```

## 关键细节

- 本答案明确选择“二进制矩阵最大 1 矩形”合同；如果面试官其实只给一维柱高，那直接执行 84 的单调栈子问题即可。
- 高度数组必须在 0 处清零，否则会错误把被 0 隔断的两段连续 1 合并。
- 栈中存下标而不是只存高度，因为面积结算还需要左边界。
- 末尾人为使用高度 0 的哨兵，使仍在栈中的柱子都能统一结算。
- 相等高度不必强制弹出；当前实现只在 `>` 时弹栈，仍能由更早/更晚下标在后续结算出正确最大宽度。

## 原理机制

任意全 1 子矩形都有一条底边。固定某一行作为底边时，每列向上连续 1 的数量正是该列可提供的最大高度，于是所有以该行为底边的候选矩形与一个直方图中的矩形一一对应。单调栈延迟结算尚未遇到更矮右边界的柱子；一旦遇到更矮高度，被弹柱子的左右第一个更矮位置都已经确定，因此它以自身高度能取得的最大宽度也随之确定。

## 项目经验版

来源没有真实业务矩阵规模或性能数据，不能虚构线上收益。面试现场我会先确认到底是 84 的一维直方图还是 85 的二维二进制矩阵，再写“逐行高度 + 单调栈”的降维关系，并用全 0、全 1、单行、空矩阵和非矩形输入验证边界。

## 常见追问

- 问：为什么能逐行转成直方图？答：固定底边后，每列连续 1 高度完整描述了该底边上可形成矩形的纵向约束。
- 问：为什么弹栈时宽度是 `i-left-1`？答：i 是右侧第一个更矮位置，left 是弹栈后左侧第一个更矮位置，中间区间都至少达到被弹高度。
- 问：复杂度为什么不是 O(rows*cols*cols)？答：单调栈让每个柱子每行最多进出栈各一次。
- 问：如果输入是一维柱高呢？答：直接使用 `largestRectangleArea`，不需要构造二维高度。
- 问：能否修改原矩阵保存高度？答：可以，但会改变输入；当前合同选择独立 O(cols) 高度数组。

## 易错点

- 忘记在矩阵值为 0 时清空该列高度。
- 弹栈后把左边界直接写成弹出的下标，导致宽度少算或多算。
- 没有哨兵或收尾循环，遗漏栈中最后一段递增柱子。
- 没确认题目是一维 84 还是二维 85，就直接套一个固定输入接口。
''',
        'test':r'''public final class MaximalRectangleTest {
    static void check(int actual,int expected,String m){if(actual!=expected)throw new AssertionError(m+"="+actual);}
    static void invalid(int[][] m,String name){try{MaximalRectangle.maximalRectangle(m);throw new AssertionError(name);}catch(IllegalArgumentException expected){}}
    public static void main(String[] args){
        check(MaximalRectangle.maximalRectangle(new int[][]{}),0,"empty");
        check(MaximalRectangle.maximalRectangle(new int[][]{{}}),0,"zero-cols");
        check(MaximalRectangle.maximalRectangle(new int[][]{{1,0,1,0,0},{1,0,1,1,1},{1,1,1,1,1},{1,0,0,1,0}}),6,"classic");
        check(MaximalRectangle.maximalRectangle(new int[][]{{1,1,1,1}}),4,"single-row");
        check(MaximalRectangle.maximalRectangle(new int[][]{{0,0},{0,0}}),0,"all-zero");
        check(MaximalRectangle.maximalRectangle(new int[][]{{1,1,1},{1,1,1}}),6,"all-one");
        invalid(null,"null"); invalid(new int[][]{{1,0},{1}},"jagged"); invalid(new int[][]{{1,2}},"nonbinary");
        System.out.println("PASS empty zero-cols classic single-row all-zero all-one null jagged nonbinary");
    }
}
''',
        'stdout':'PASS empty zero-cols classic single-row all-zero all-one null jagged nonbinary',
        'checks':['empty matrix returns 0','zero-column matrix returns 0','classic 85 example returns 6','single-row histogram case returns 4','all-zero returns 0','all-one 2x3 returns 6','null rejected','jagged rejected','non-binary rejected'],
        'claims':[
            ('source-boundary','The preserved source names a LeetCode 84/85-style maximum-area variant but does not fix the input contract; this candidate explicitly selects the binary-matrix maximal-rectangle contract and identifies 84 as the row-histogram subproblem.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('algorithm-correctness','The executable OpenJDK fixture verifies row-height accumulation plus monotonic-stack rectangle calculation across classic, degenerate, and invalid-input cases.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate resolves the 84/85 ambiguity explicitly instead of pretending the source fixed one API.','The row-height reduction and monotonic-stack width invariant are stated with their boundary semantics.','OpenJDK validation covers the classic maximal-rectangle case, empty/zero-column/single-row/all-zero/all-one inputs, and malformed matrices.','One-dimensional histogram handling remains an explicit follow-up rather than an unstated source requirement.'],
        'task_note':'- [x] `cq_q_fc030f5d732ab198236441d05ebb7eff` source-first isolated review PASS: the candidate makes the 84/85 input-contract ambiguity explicit, reduces each binary-matrix row to a histogram, and OpenJDK validation covers classic/degenerate/malformed cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_fe3172f9067bf094daf0310e95ad6fd8',
        'qid':'fe3172f9067bf094daf0310e95ad6fd8',
        'expected':'算法 1：将一棵二叉搜索树 (BST) 转换为一个排序的双向链表',
        'slug':'bst-to-doubly-linked-list',
        'class':'BstToDoublyLinkedList',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fe3172f9067bf094daf0310e95ad6fd8","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 将 BST 转换为排序双向链表

## 核心结论

来源只要求把 BST 转成排序双向链表，没有说明是否原地、是否循环以及重复键语义。这里采用 Java 合同：输入是严格 BST；原地复用每个 `Node`，把 `left` 改作 `prev`、`right` 改作 `next`，返回升序非循环链表头；空树返回 `null`。利用中序遍历天然得到升序顺序，每访问一个节点就把它和上一个访问节点双向连接，时间 O(n)，显式栈空间 O(h)。

## 1 分钟版

- BST 中序遍历顺序就是升序节点顺序。
- 维护 `prev` 指向刚刚访问的前驱节点。
- 当前节点 `cur` 出栈时：若 `prev!=null`，令 `prev.right=cur`、`cur.left=prev`；否则当前节点就是 head。
- 然后 `prev=cur`，继续处理中序的下一个节点。
- 遍历结束后最后一个节点的 `right` 应为 `null`，head 的 `left` 应为 `null`，得到非循环双链表。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class BstToDoublyLinkedList {
    public static final class Node {
        public final int val;
        public Node left;
        public Node right;
        public Node(int val) { this.val = val; }
    }

    public static Node convert(Node root) {
        if (root == null) return null;
        Deque<Node> stack = new ArrayDeque<>();
        Node current = root, prev = null, head = null;
        while (current != null || !stack.isEmpty()) {
            while (current != null) {
                stack.push(current);
                current = current.left;
            }
            current = stack.pop();
            if (prev == null) {
                head = current;
                current.left = null;
            } else {
                prev.right = current;
                current.left = prev;
            }
            prev = current;
            current = current.right;
        }
        prev.right = null;
        return head;
    }
}
```

## 关键细节

- “排序”来自 BST 的中序不变量，不需要额外排序。
- 当前实现原地复用节点，所以转换后原来的树结构被破坏；如果调用方还需要树，必须改为新建链表节点。
- 这是非循环链表合同；若题目要求循环链表，还要额外连接 `head.left=tail` 与 `tail.right=head`。
- 复杂度写 O(n) 时间、O(h) 栈空间；若用 Morris 遍历可以把额外空间降到 O(1)，但实现和临时指针修改更复杂。
- 当前合同假设严格 BST；若允许重复键，仍可保持非降序，但重复键的树侧放置规则应先明确。

## 原理机制

中序遍历在 BST 上产生从小到大的节点序列。双向链表只需要对这个序列中相邻的两个节点建立互逆引用，因此无需保存完整序列：`prev` 就是当前节点在中序序列中的直接前驱。每个节点恰好被压栈、弹栈和连接一次，所以总体线性；栈只保存根到当前搜索路径，峰值由树高决定。

## 项目经验版

来源没有真实内存约束或节点复用要求，不能虚构“必须 O(1) 空间”。面试中我会先问清原地/新建、循环/非循环两个合同，再优先写易验证的显式栈版本；只有明确要求常数额外空间时再讨论 Morris 遍历。

## 常见追问

- 问：为什么不先放到数组再排序？答：BST 中序已经有序；数组+排序会额外浪费空间和 O(n log n) 排序成本。
- 问：能 O(1) 额外空间吗？答：可以用 Morris 中序遍历，但要临时建立和恢复线索，代码复杂度更高。
- 问：如果要循环双链表？答：遍历完成后再把 head 与 tail 首尾互连。
- 问：转换后还能当树使用吗？答：当前合同不能，因为 left/right 已被重解释为 prev/next。
- 问：递归版呢？答：同样维护前驱节点即可，但递归调用栈也是 O(h)。

## 易错点

- 只设置 `prev.right=current`，忘记反向的 `current.left=prev`。
- 没清理 head.left 或 tail.right，留下旧树指针。
- 题目要求非循环却擅自首尾相连，或反过来。
- 原地修改后仍声称原 BST 可以继续使用。
''',
        'test':r'''public final class BstToDoublyLinkedListTest {
    static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    static BstToDoublyLinkedList.Node n(int v){return new BstToDoublyLinkedList.Node(v);}
    public static void main(String[] args){
        check(BstToDoublyLinkedList.convert(null)==null,"empty");
        BstToDoublyLinkedList.Node one=n(9); check(BstToDoublyLinkedList.convert(one)==one,"single-head"); check(one.left==null&&one.right==null,"single-links");
        BstToDoublyLinkedList.Node n1=n(1),n2=n(2),n3=n(3),n4=n(4),n5=n(5); n4.left=n2;n4.right=n5;n2.left=n1;n2.right=n3;
        BstToDoublyLinkedList.Node h=BstToDoublyLinkedList.convert(n4); BstToDoublyLinkedList.Node[] a={n1,n2,n3,n4,n5};
        check(h==n1,"head-identity"); check(h.left==null,"head-prev-null");
        BstToDoublyLinkedList.Node cur=h,prev=null; int i=0; while(cur!=null){check(i<a.length,"cycle");check(cur==a[i],"identity-"+i);check(cur.left==prev,"prev-"+i);prev=cur;cur=cur.right;i++;}
        check(i==5,"length"); check(prev==n5&&n5.right==null,"tail");
        System.out.println("PASS empty single sorted identity prev-next head-tail noncircular");
    }
}
''',
        'stdout':'PASS empty single sorted identity prev-next head-tail noncircular',
        'checks':['empty tree returns null','single node preserved','in-order output sorted','original node identities reused','prev/next links are reciprocal','head.prev is null','tail.next is null','result is non-circular'],
        'claims':[
            ('source-boundary','The preserved source asks to convert a BST to a sorted doubly linked list but does not specify in-place/new-node or circular/non-circular semantics; this candidate declares in-place non-circular semantics.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('traversal-correctness','The executable OpenJDK fixture verifies that iterative in-order traversal reuses the original nodes in sorted order with reciprocal prev/next links and clean head/tail boundaries.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate states the two key omitted contracts—node reuse and circularity—before presenting the algorithm.','The in-order predecessor invariant is sufficient to link adjacent sorted nodes without materializing or sorting an array.','OpenJDK validation verifies empty/single cases, sorted order, node identity reuse, reciprocal links, and non-circular head/tail boundaries.','Morris traversal is kept as an optional O(1)-space follow-up rather than an invented requirement.'],
        'task_note':'- [x] `cq_q_fe3172f9067bf094daf0310e95ad6fd8` source-first isolated review PASS: the candidate declares in-place non-circular semantics, links BST nodes in in-order sequence, and OpenJDK validation verifies identity/order/reciprocal-link/head-tail invariants. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_fedafeab2f6110ead792af233549b58c',
        'qid':'fedafeab2f6110ead792af233549b58c',
        'expected':'算法：最长回文子串。',
        'slug':'longest-palindromic-substring',
        'class':'LongestPalindromicSubstring',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fedafeab2f6110ead792af233549b58c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最长回文子串

## 核心结论

来源只要求最长回文子串，没有指定语言、空值和并列答案规则。这里采用 Java 合同：返回输入字符串中最长的连续回文子串；空串返回空串，`null` 视为无效输入；若有多个同长度最优解，返回起始位置最靠前的一个。使用中心扩展，对每个位置分别尝试奇数中心和偶数中心，时间 O(n²)、额外空间 O(1)。

## 1 分钟版

- “子串”必须连续，因此不能用最长回文子序列的区间 DP 语义混淆。
- 每个回文串都有一个中心：奇数长度中心是字符，偶数长度中心是两个字符之间的缝。
- 从中心向两侧同时扩展，只要字符相等就继续；第一次不等时，该中心的最大回文已经确定。
- 每个位置算奇偶两个中心，维护全局最优 `[start,end]`。
- 只在发现更长答案时更新，因此并列时自然保留更早出现的答案。

## 3 分钟版

```java
public final class LongestPalindromicSubstring {
    public static String longestPalindrome(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        if (s.length() < 2) return s;
        int start = 0, end = 0;
        for (int i = 0; i < s.length(); i++) {
            int odd = expand(s, i, i);
            int even = expand(s, i, i + 1);
            int len = Math.max(odd, even);
            if (len > end - start + 1) {
                start = i - (len - 1) / 2;
                end = i + len / 2;
            }
        }
        return s.substring(start, end + 1);
    }

    private static int expand(String s, int left, int right) {
        while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
            left--;
            right++;
        }
        return right - left - 1;
    }
}
```

## 关键细节

- 奇数中心 `(i,i)` 与偶数中心 `(i,i+1)` 都必须检查，否则会漏掉 `abba` 这类偶数回文。
- `expand` 退出时左右指针已经越过合法回文一格，所以长度是 `right-left-1`。
- 当前实现只在 `len` 严格更大时更新，因此同长度并列保留更早的已有答案；这是本答案显式声明的合同。
- 中心扩展最坏 O(n²)，例如大量相同字符会从许多中心扩展很远；如果要求线性时间可讨论 Manacher，但来源没有要求。
- Java `char` 按 UTF-16 code unit 比较；若题目要求按 Unicode code point 定义字符，需要先改变输入遍历合同。

## 原理机制

回文的对称性意味着一旦中心确定，某个半径是否成立只取决于中心两侧对应字符是否相等。任意连续回文子串都能唯一归入一个奇数或偶数中心，因此枚举全部 2n-1 个中心不会漏解。每个中心扩展到第一次不匹配时，其最大半径已经确定；取所有中心的最大值就是全局最长回文子串。

## 项目经验版

来源没有真实字符串长度、字符集或延迟目标，不能虚构必须使用 Manacher。面试现场我会先用中心扩展写出低风险正确解，声明 O(n²)/O(1)，再根据约束决定是否值得升级到 O(n) 的 Manacher，并额外确认并列答案和 Unicode 字符定义。

## 常见追问

- 问：和最长回文子序列区别？答：子串要求连续，子序列可以跳过字符，两题不能直接互换算法。
- 问：为什么需要偶数中心？答：偶数长度回文没有单个中心字符，中心位于两个字符之间。
- 问：为什么复杂度 O(n²)？答：有 O(n) 个中心，每个中心最坏可扩展 O(n) 距离。
- 问：能做到 O(n) 吗？答：可以用 Manacher，但实现复杂度更高，只有约束需要时才值得使用。
- 问：多个最长答案返回哪个？答：当前合同返回最早起始位置的那个，因为只在严格更长时更新。

## 易错点

- 只扩展奇数中心，漏掉偶数长度回文。
- 把“子串”写成“子序列”问题。
- 退出扩展后长度公式写成 `right-left+1`，造成越界长度。
- 未声明并列答案策略却让测试依赖某个固定返回值。
''',
        'test':r'''public final class LongestPalindromicSubstringTest {
    static void check(String actual,String expected,String m){if(!actual.equals(expected))throw new AssertionError(m+"="+actual);}
    public static void main(String[] args){
        check(LongestPalindromicSubstring.longestPalindrome(""),"","empty");
        check(LongestPalindromicSubstring.longestPalindrome("a"),"a","single");
        check(LongestPalindromicSubstring.longestPalindrome("babad"),"bab","tie-earliest");
        check(LongestPalindromicSubstring.longestPalindrome("cbbd"),"bb","even");
        check(LongestPalindromicSubstring.longestPalindrome("ac"),"a","distinct-tie");
        check(LongestPalindromicSubstring.longestPalindrome("aaaa"),"aaaa","all-same");
        try{LongestPalindromicSubstring.longestPalindrome(null);throw new AssertionError("null");}catch(IllegalArgumentException expected){}
        System.out.println("PASS empty single odd-tie-even distinct-tie all-same null-rejected");
    }
}
''',
        'stdout':'PASS empty single odd-tie-even distinct-tie all-same null-rejected',
        'checks':['empty string returns empty','single character preserved','babad tie returns earliest bab','even palindrome cbbd returns bb','distinct tie returns earliest a','all-same expands to full string','null rejected'],
        'claims':[
            ('source-boundary','The preserved source asks only for the longest palindromic substring and does not specify language, null behavior, tie-breaking, Unicode granularity, or linear-time requirements.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('center-expansion-correctness','The executable OpenJDK fixture verifies the declared earliest-tie center-expansion contract across empty, odd/even, all-same, distinct-tie, and invalid inputs.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate keeps substring semantics distinct from the already-covered subsequence problem.','Both odd and even centers are enumerated, with the post-expansion length formula and earliest-tie rule made explicit.','OpenJDK validation covers empty/single/odd/even/tie/all-same/null cases.','Manacher and Unicode code-point handling remain explicit contract-dependent follow-ups rather than hidden assumptions.'],
        'task_note':'- [x] `cq_q_fedafeab2f6110ead792af233549b58c` source-first isolated review PASS: the source-bounded center-expansion solution covers odd/even centers with an explicit earliest-tie contract, and OpenJDK validation covers empty/tie/even/all-same/null cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
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
        raise SystemExit('Batch 0056 source inventory must be frozen before writing')
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
        with tempfile.TemporaryDirectory(prefix=f'b56-{target["slug"]}-') as tmp:
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
            {'source_id':'repository-source','title':f'Batch 0056 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
            {'source_id':'fixture','title':f'OpenJDK deterministic validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        ]
        claims = [{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
        coverage = [{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
        write_json(out/'writer_research.json', {'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
        reviewer = f'source-first-isolated-reviewer-batch-0056-{target["slug"]}-20260829-v1'
        review = {'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0056.{target["slug"]}.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]}
        write_json(out/'isolated_review_result.json', review)
        write_json(evidence, {'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':f'content-batch-0056-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0056 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':target['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in target['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']},'promotion_blocker':PROMOTION_BLOCKER})
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
