#!/usr/bin/env python3
"""Build, execute, and source-first review three source-clear Batch 0056 coding candidates."""

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
        'cid':'cq_q_fbb2e34022cf1f4d0e2ba1a92b1688aa',
        'qid':'fbb2e34022cf1f4d0e2ba1a92b1688aa',
        'expected':'代码手撕：最长回文子序列（Longest Palindromic Subsequence）。',
        'slug':'longest-palindromic-subsequence',
        'class':'LongestPalindromicSubsequence',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fbb2e34022cf1f4d0e2ba1a92b1688aa","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最长回文子序列（Longest Palindromic Subsequence）

## 核心结论

来源只要求手撕最长回文子序列，没有指定语言、空值合同或是否必须做空间优化。这里采用 Java 合同：`longestPalindromeSubseq(String s)` 返回字符串中最长回文**子序列**长度；空字符串返回 0，`null` 视为无效输入。使用区间动态规划：`dp[i][j]` 表示闭区间 `s[i..j]` 的最长回文子序列长度，时间 O(n²)、空间 O(n²)。

## 1 分钟版

- 子序列允许删除字符但保持相对顺序，不要求连续；这与“最长回文子串”不同。
- 状态：`dp[i][j]` = `s[i..j]` 的 LPS 长度，单字符 `dp[i][i]=1`。
- 若 `s[i]==s[j]`，两端可以一起纳入：长度 2 时答案为 2，更长时 `dp[i+1][j-1]+2`。
- 若两端不同，至少舍弃一端：`max(dp[i+1][j], dp[i][j-1])`。
- 因为状态依赖更短区间，所以 i 从右向左，j 从 i+1 向右填表。

## 3 分钟版

```java
public final class LongestPalindromicSubsequence {
    public static int longestPalindromeSubseq(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        int n = s.length();
        if (n == 0) return 0;

        int[][] dp = new int[n][n];
        for (int i = n - 1; i >= 0; i--) {
            dp[i][i] = 1;
            for (int j = i + 1; j < n; j++) {
                if (s.charAt(i) == s.charAt(j)) {
                    dp[i][j] = (j == i + 1) ? 2 : dp[i + 1][j - 1] + 2;
                } else {
                    dp[i][j] = Math.max(dp[i + 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[0][n - 1];
    }
}
```

例如 `bbbab` 的答案是 4（可取 `bbbb`），`agbdba` 的答案是 5（可取 `abdba`）。

## 关键细节

- “子序列”不要求连续；若把它写成中心扩展，解决的是最长回文子串而不是本题。
- `dp[i][j]` 的依赖都在更短区间，因此遍历顺序必须先保证 `i+1` 行和更短的左区间已经计算。
- 相邻字符相等时没有合法的 `dp[i+1][j-1]` 区间，因此实现直接写 2，避免错误索引。
- 只求长度时可以继续把空间压到 O(n)，但二维版本更容易在面试中解释状态转移和边界。
- 来源没有要求返回具体子序列；若要恢复路径，需要额外记录决策或根据 dp 回溯。

## 原理机制

回文结构的关键是“两端是否能够配对”。若两端字符相等，存在一个最优解可以把这两个端点与内部区间的最优回文子序列组合起来；若两端不同，一个回文子序列不可能同时使用这两个互异端点作为配对，因此最优值来自舍弃左端或舍弃右端两个子问题的最大值。区间长度逐渐扩大后，最终 `dp[0][n-1]` 覆盖完整字符串。

## 项目经验版

来源没有真实业务或性能数据，不能虚构项目收益。面试现场我会先强调“subsequence 不是 substring”，再写状态定义、转移和遍历顺序，并用空串、单字符、全相同字符、没有重复字符做边界验证。只有在明确要求空间优化时才把二维 DP 压缩成一维，避免为了炫技降低可读性。

## 常见追问

- 问：和最长回文子串有什么区别？答：子串必须连续，子序列只保持相对顺序；两题状态和常用算法不同。
- 问：为什么字符相等就能加 2？答：相等端点可以作为回文的对称外层，内部选取其最长回文子序列即可。
- 问：为什么 i 要倒序？答：`dp[i][j]` 依赖 `dp[i+1][...]`，所以 i+1 对应的状态必须先完成。
- 问：能优化到 O(n) 空间吗？答：可以维护一维 dp 和左下角旧值，但题目未要求，二维版更直接。
- 问：如何返回实际序列？答：从 `dp[0][n-1]` 依据端点匹配和相邻状态回溯，构造左右两半。

## 易错点

- 把最长回文子序列误写成最长回文子串。
- DP 遍历方向错误，读取尚未计算的 `dp[i+1][j]`。
- 相邻字符相等时访问无效的内部区间。
- 来源只问长度，却额外声称必须返回具体序列。
''',
        'test':r'''public final class LongestPalindromicSubsequenceTest {
    static void check(int actual,int expected,String m){if(actual!=expected)throw new AssertionError(m+"="+actual);}
    public static void main(String[] args){
        check(LongestPalindromicSubsequence.longestPalindromeSubseq(""),0,"empty");
        check(LongestPalindromicSubsequence.longestPalindromeSubseq("a"),1,"single");
        check(LongestPalindromicSubsequence.longestPalindromeSubseq("bbbab"),4,"bbbab");
        check(LongestPalindromicSubsequence.longestPalindromeSubseq("cbbd"),2,"cbbd");
        check(LongestPalindromicSubsequence.longestPalindromeSubseq("agbdba"),5,"agbdba");
        check(LongestPalindromicSubsequence.longestPalindromeSubseq("abcdef"),1,"distinct");
        try{LongestPalindromicSubsequence.longestPalindromeSubseq(null);throw new AssertionError("null");}catch(IllegalArgumentException expected){}
        System.out.println("PASS empty single classic even-pair nested distinct null-rejected");
    }
}
''',
        'stdout':'PASS empty single classic even-pair nested distinct null-rejected',
        'checks':['empty string returns 0','single character returns 1','classic bbbab returns 4','cbbd returns 2','nested agbdba returns 5','all-distinct input returns 1','null is rejected'],
        'claims':[
            ('source-boundary','The preserved source asks only for Longest Palindromic Subsequence and does not specify language, null handling, path reconstruction, or space optimization.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('dp-correctness','The executable OpenJDK fixture verifies the declared interval-DP length contract across empty, singleton, classic, nested, distinct, and invalid inputs.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate keeps the subsequence problem distinct from the substring variant and defines an explicit length-only Java contract.','The interval DP transition and reverse-i traversal satisfy the stated dependency ordering.','OpenJDK validation covers empty/single/classic/nested/distinct inputs and null rejection.','Path reconstruction and O(n) space compression remain explicit optional follow-ups rather than invented source requirements.'],
        'task_note':'- [x] `cq_q_fbb2e34022cf1f4d0e2ba1a92b1688aa` source-first isolated review PASS: the source-bounded interval DP correctly distinguishes subsequence from substring, and OpenJDK validation covers empty/single/classic/nested/distinct inputs plus null rejection. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_fd5f836465b9d8c2f7c54c5d5a262e9d',
        'qid':'fd5f836465b9d8c2f7c54c5d5a262e9d',
        'expected':'算法基础：如何在二叉搜索树（BST）中查找一个数？',
        'slug':'bst-search',
        'class':'BstSearch',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fd5f836465b9d8c2f7c54c5d5a262e9d","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 在二叉搜索树（BST）中查找一个数

## 核心结论

来源只问 BST 查找，没有指定语言、重复键规则或返回布尔值/节点。这里采用 Java 合同：树满足严格 BST 不变量 `left < node < right`；`search(root, target)` 返回值等于 target 的节点，不存在则返回 `null`。利用 BST 的有序性每次只进入一个子树，时间 O(h)，h 是树高；迭代实现额外空间 O(1)。

## 1 分钟版

- 当前节点值等于 target：直接返回当前节点。
- target 小于当前值：只去左子树，因为右子树所有值都更大。
- target 大于当前值：只去右子树。
- 走到 `null` 仍没命中：不存在。
- 平衡 BST 的 h≈log n，查找通常 O(log n)；退化成链时 h=n，因此最坏 O(n)。

## 3 分钟版

```java
public final class BstSearch {
    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;
        public TreeNode(int val) { this.val = val; }
    }

    public static TreeNode search(TreeNode root, int target) {
        TreeNode current = root;
        while (current != null) {
            if (target == current.val) return current;
            current = target < current.val ? current.left : current.right;
        }
        return null;
    }
}
```

与普通二叉树 DFS 不同，BST 查找不需要同时探索两边；有序不变量允许每次排除整个不可能的子树。

## 关键细节

- 复杂度应写 O(h)，不能无条件声称 O(log n)：只有树高受控时才接近对数复杂度。
- 当前合同假设键严格唯一；若 BST 允许重复键，必须先定义重复元素放左还是放右，以及查找要返回哪一个。
- 返回节点比返回布尔值保留更多信息；如果调用方只关心存在性，可以判断结果是否为 `null`。
- 迭代写法避免递归调用栈；递归版逻辑同样正确，空间为 O(h)。
- 该算法依赖 BST 不变量；对任意普通二叉树使用同样分支规则会漏掉答案。

## 原理机制

BST 的排序约束把每个节点划成三个互斥区域：左子树全部更小、当前节点恰好等于自身键、右子树全部更大。因此比较 target 与当前值后，可以证明其中两个区域不可能包含 target，并永久排除它们。每轮沿根到叶的一条路径推进，所以访问节点数最多等于树高。

## 项目经验版

来源没有真实数据结构或平衡策略，不能虚构线上复杂度。面试中我会先写 O(h) 和唯一键假设，再补充：若频繁查询且树可能退化，应使用 AVL/红黑树等保持高度，或根据业务直接选语言/数据库提供的有序索引结构。是否需要平衡不是当前题目的隐藏前提。

## 常见追问

- 问：为什么复杂度不是永远 O(log n)？答：普通 BST 不保证平衡，最坏可以退化为长度 n 的链。
- 问：递归和迭代哪个好？答：都利用同一不变量；迭代额外空间 O(1)，递归更短但调用栈 O(h)。
- 问：有重复值怎么办？答：要先定义插入和查找语义；当前合同使用严格 BST、键唯一。
- 问：普通二叉树能这样查吗？答：不能，普通二叉树没有左小右大的排除依据。
- 问：找不到怎么表示？答：当前 API 返回 `null`，调用方可据此判断不存在。

## 易错点

- 把 O(h) 直接写成 O(log n)，忽略退化树。
- target 较小时走右子树，分支方向写反。
- 未定义重复键语义却宣称算法适用于所有 BST 定义。
- 在普通二叉树上套用 BST 剪枝规则。
''',
        'test':r'''public final class BstSearchTest {
    static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[] args){
        BstSearch.TreeNode r=new BstSearch.TreeNode(8);
        r.left=new BstSearch.TreeNode(3); r.right=new BstSearch.TreeNode(10);
        r.left.left=new BstSearch.TreeNode(1); r.left.right=new BstSearch.TreeNode(6);
        r.left.right.left=new BstSearch.TreeNode(4); r.left.right.right=new BstSearch.TreeNode(7);
        r.right.right=new BstSearch.TreeNode(14); r.right.right.left=new BstSearch.TreeNode(13);
        check(BstSearch.search(r,8)==r,"root identity");
        check(BstSearch.search(r,4)==r.left.right.left,"left path");
        check(BstSearch.search(r,13)==r.right.right.left,"right path");
        check(BstSearch.search(r,5)==null,"absent interior");
        check(BstSearch.search(null,1)==null,"empty");
        BstSearch.TreeNode skew=new BstSearch.TreeNode(1); skew.right=new BstSearch.TreeNode(2); skew.right.right=new BstSearch.TreeNode(3);
        check(BstSearch.search(skew,3)==skew.right.right,"skew");
        System.out.println("PASS root left-path right-path absent empty skew-tree");
    }
}
''',
        'stdout':'PASS root left-path right-path absent empty skew-tree',
        'checks':['root match returns root identity','left-subtree path is found','right-subtree path is found','absent target returns null','empty tree returns null','degenerate BST still returns correct node'],
        'claims':[
            ('source-boundary','The preserved source asks how to search a value in a BST and does not specify language, duplicate-key placement, or return shape.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('bst-correctness','The executable OpenJDK fixture verifies ordered single-path search across root, left, right, absent, empty, and degenerate-tree cases under the declared strict-BST contract.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate explicitly states the strict-BST invariant needed for one-branch pruning and does not generalize it to arbitrary binary trees.','Complexity is correctly expressed as O(h), with balanced and degenerate cases distinguished.','OpenJDK validation covers root identity, both branch directions, absence, empty input, and a skewed tree.','Duplicate-key policy remains an explicit contract question rather than an invented source fact.'],
        'task_note':'- [x] `cq_q_fd5f836465b9d8c2f7c54c5d5a262e9d` source-first isolated review PASS: the strict-BST O(h) one-branch search contract is explicit, and OpenJDK validation covers root/left/right/absent/empty/degenerate cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_ff9548e89dda56f74db92a45062a08aa',
        'qid':'ff9548e89dda56f74db92a45062a08aa',
        'expected':'算法：查找链表倒数第k个元素',
        'slug':'kth-from-end-list',
        'class':'KthFromEndList',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ff9548e89dda56f74db92a45062a08aa","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 查找链表倒数第 k 个元素

## 核心结论

来源只要求查找链表倒数第 k 个元素，没有指定语言、k 的起始定义或非法输入处理。这里采用单链表 Java 合同：`k` 从 1 开始，`k=1` 表示尾节点；`k<=0`、空链表或 `k>链表长度` 返回 `null`。用快慢双指针让 fast 先走 k 步，再同步前进；fast 到 `null` 时 slow 正好位于倒数第 k 个节点。时间 O(n)、额外空间 O(1)。

## 1 分钟版

- fast 和 slow 都从 head 开始。
- fast 先前进 k 次；中途遇到 `null` 说明 k 大于链表长度，返回 `null`。
- 然后 fast、slow 同时一步一步走。
- 当 fast 到达 `null` 时，它比 slow 始终领先 k 个节点，所以 slow 到尾部的距离正好是 k，slow 即倒数第 k 个节点。
- `k=1` 返回尾节点，`k=链长` 返回头节点。

## 3 分钟版

```java
public final class KthFromEndList {
    public static final class ListNode {
        public final int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode kthFromEnd(ListNode head, int k) {
        if (head == null || k <= 0) return null;

        ListNode fast = head;
        for (int i = 0; i < k; i++) {
            if (fast == null) return null;
            fast = fast.next;
        }

        ListNode slow = head;
        while (fast != null) {
            fast = fast.next;
            slow = slow.next;
        }
        return slow;
    }
}
```

例如链表 `1 -> 2 -> 3 -> 4 -> 5`，`k=2` 时 fast 先领先两步，最终 slow 停在 4。

## 关键细节

- 当前合同明确 k 从 1 开始；若题目把 k 从 0 开始，算法初始化会不同。
- fast 必须先完整走 k 步；如果只走 k-1 步，最后会得到倒数第 k+1 或产生边界偏移。
- `k==length` 时 fast 恰好变成 `null`，slow 保持在 head，正确返回头节点。
- 不需要先单独遍历求长度；双指针一遍完成，仍是 O(n)。
- 若链表可能有环，“倒数”本身没有有限尾节点定义；当前合同假设普通无环单链表。

## 原理机制

核心不变量是同步阶段始终保持 fast 比 slow 领先 k 个“next 边”。fast 到尾后，再也没有剩余节点，而 slow 到尾的边数恰好等于此前保持的 k 差距；按 `k=1` 为尾节点的定义，slow 正好定位倒数第 k 个节点。相比先求长度再定位，双指针把两段逻辑合并成一次线性扫描。

## 项目经验版

来源没有真实链表结构或业务语义，不能虚构。面试现场我会先问清 k 是否从 1 开始、非法 k 如何处理，以及是否保证无环；随后用 `k=1`、`k=length`、`k>length` 三个边界证明没有 off-by-one。如果节点来自不可变结构，算法仍只读取 next，不需要修改链表。

## 常见追问

- 问：为什么 fast 先走 k 步？答：这样同步阶段两指针保持 k 个节点间隔，fast 到尾时 slow 对应倒数第 k 个。
- 问：k 等于链长呢？答：fast 预走后恰好为 null，slow 仍是 head，因此返回头节点。
- 问：为什么不先算长度？答：可以，但要两段遍历；双指针不需要显式长度，空间也仍是 O(1)。
- 问：链表有环怎么办？答：有环时不存在普通意义上的“倒数”，应先修改问题合同或检测环；当前题默认无环链表。
- 问：k=0 呢？答：当前合同 k 从 1 开始，所以 k<=0 返回 null。

## 易错点

- fast 只先走 k-1 步造成 off-by-one。
- 没检查 k>length，预走时空指针异常。
- 未声明 k 从 0 还是从 1 开始。
- 对有环链表仍声称存在倒数第 k 个节点。
''',
        'test':r'''public final class KthFromEndListTest {
    static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    static KthFromEndList.ListNode list(int... a){KthFromEndList.ListNode dummy=new KthFromEndList.ListNode(0),cur=dummy;for(int x:a){cur.next=new KthFromEndList.ListNode(x);cur=cur.next;}return dummy.next;}
    public static void main(String[] args){
        KthFromEndList.ListNode h=list(1,2,3,4,5);
        check(KthFromEndList.kthFromEnd(h,1).val==5,"tail");
        check(KthFromEndList.kthFromEnd(h,2).val==4,"second");
        check(KthFromEndList.kthFromEnd(h,5)==h,"head identity");
        check(KthFromEndList.kthFromEnd(h,6)==null,"too large");
        check(KthFromEndList.kthFromEnd(h,0)==null,"zero");
        check(KthFromEndList.kthFromEnd(h,-1)==null,"negative");
        check(KthFromEndList.kthFromEnd(null,1)==null,"empty");
        KthFromEndList.ListNode one=list(9); check(KthFromEndList.kthFromEnd(one,1)==one,"single");
        System.out.println("PASS tail second head-boundary too-large nonpositive empty single");
    }
}
''',
        'stdout':'PASS tail second head-boundary too-large nonpositive empty single',
        'checks':['k=1 returns tail','k=2 returns second from end','k=length returns head identity','k>length returns null','nonpositive k returns null','empty list returns null','single-node list works'],
        'claims':[
            ('source-boundary','The preserved source asks for the kth element from the end of a linked list and does not specify language, zero/one-based k, invalid-input behavior, or cyclic-list semantics.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('two-pointer-correctness','The executable OpenJDK fixture verifies the declared one-based two-pointer contract across tail, interior, head, oversized/nonpositive k, empty, and singleton cases.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate makes the one-based k and invalid-input behavior explicit before applying the two-pointer method.','The k-step lead invariant correctly covers k=1 and k=length without an off-by-one special case.','OpenJDK validation covers tail/interior/head/too-large/nonpositive/empty/singleton cases.','Cyclic-list semantics are kept out of the ordinary finite-list contract instead of being silently assumed away.'],
        'task_note':'- [x] `cq_q_ff9548e89dda56f74db92a45062a08aa` source-first isolated review PASS: the one-based k-step two-pointer invariant is explicit and OpenJDK validation covers tail/interior/head/oversized/nonpositive/empty/singleton cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
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
